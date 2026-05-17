# Private Vault

A Cloudflare Worker that serves a private HTML file (or small set of files)
from a private R2 bucket, behind Cloudflare Access. Designed for hosting
content at `https://learning.martyschneider.com/` that only the owner can
reach via email one-time PIN.

The public site at `martyschneider.com` (this repo's GitHub Pages
deployment) is unaffected.

## Architecture

```
Browser  ->  Cloudflare Edge  ->  Cloudflare Access (email OTP)
                                    |
                                    v
                                  Worker (this code)
                                    |
                                    v
                                  R2 bucket: private-vault
```

- The HTML file is **never** committed to this (public) repo. It only
  lives in the private R2 bucket.
- Every request to `learning.martyschneider.com` hits Cloudflare Access
  before the Worker runs. No valid session, no Worker invocation.
- The Worker also rejects requests with path-traversal segments and
  non-`GET`/`HEAD` methods.

## One-time setup

These steps need to be done once, in this order. Most are clicks in the
Cloudflare dashboard; the rest are local commands.

### 1. Add martyschneider.com to Cloudflare

1. Cloudflare dashboard -> **Add a Site** -> `martyschneider.com` -> Free
   plan.
2. Cloudflare auto-imports DNS. Verify the existing GitHub Pages records:
   - `A` apex `@` -> `185.199.108.153`, `185.199.109.153`,
     `185.199.110.153`, `185.199.111.153`
   - `CNAME www` -> `marty-schneider.github.io`
   - Proxy status: orange cloud (proxied) on both
3. At your registrar, change the nameservers to the two Cloudflare
   nameservers shown on the Cloudflare overview page.
4. Wait for propagation (usually minutes). Confirm
   `https://martyschneider.com/` still loads as before.

### 2. Enable Cloudflare Zero Trust

1. Cloudflare dashboard -> **Zero Trust**.
2. On first entry, pick a team domain (e.g. `marty.cloudflareaccess.com`).
   Free plan, supports up to 50 users.
3. Identity providers: the built-in **One-time PIN** is enabled by
   default. No extra setup.

### 3. Create the R2 bucket

In the Cloudflare dashboard:

1. **R2** -> Create bucket named exactly `private-vault`.
2. Do **not** enable a public r2.dev URL. Do **not** attach a custom
   domain. The bucket must stay private.

(You can also create it from the CLI after step 4 with
`wrangler r2 bucket create private-vault`.)

### 4. Install Wrangler and authenticate

From this directory (`private-vault/`):

```bash
npm install
npx wrangler login
```

`wrangler login` opens a browser tab and links the CLI to your Cloudflare
account.

### 5. Upload the private HTML to R2

Stage the file locally in `private-vault/content/` (this folder is
gitignored). For example:

```bash
mkdir content
cp /path/to/your-private-file.html content/index.html
npx wrangler r2 object put private-vault/index.html --file=./content/index.html
```

If the page references additional assets (CSS, images, JS), upload each
one with the same path it expects:

```bash
npx wrangler r2 object put private-vault/styles.css --file=./content/styles.css
npx wrangler r2 object put private-vault/logo.png   --file=./content/logo.png
```

### 6. Deploy the Worker

```bash
npx wrangler deploy
```

This publishes the Worker, binds the `VAULT` -> `private-vault` R2
binding from `wrangler.toml`, and creates the `private` DNS record
pointing at the Worker.

### 7. Put Cloudflare Access in front of the hostname

In the Cloudflare dashboard:

1. **Zero Trust** -> **Access** -> **Applications** -> **Add an
   application** -> **Self-hosted**.
2. Application configuration:
   - Name: `Private Vault`
   - Session duration: `24 hours` (tweak to taste)
   - Application domain: `learning.martyschneider.com`
   - Path: leave blank (protect everything on this hostname)
3. Identity providers: check **One-time PIN**.
4. Add a policy:
   - Name: `Owner only`
   - Action: **Allow**
   - Include: **Emails** -> `marty.schneider@gmail.com`
5. Save.

### 8. Verify

- Open `https://learning.martyschneider.com/` in a fresh / incognito
  browser. You should see the Cloudflare Access login screen.
- Enter `marty.schneider@gmail.com`, receive the PIN, enter it.
- The HTML you uploaded should render.
- In a different browser without a session, confirm the same URL still
  challenges you.
- Confirm `https://martyschneider.com/` works exactly as before.

## Day-to-day operations

### Update the private HTML

```bash
cp /path/to/new-version.html content/index.html
npx wrangler r2 object put private-vault/index.html --file=./content/index.html
```

No redeploy of the Worker is needed. R2 is read live on each request
(`Cache-Control: private, no-store` is set).

### Rotate the allowed email or add a second user

Cloudflare dashboard -> Zero Trust -> Access -> Applications ->
`Private Vault` -> Policies. Edit the include list.

### Logs

```bash
npx wrangler tail
```

Streams live Worker logs (status codes, errors).

### Local development

```bash
npx wrangler dev
```

Runs the Worker locally against your real R2 bucket. Useful for testing
new features in `worker.ts` without deploying. Note this bypasses
Cloudflare Access; only run it on a trusted machine.

## Files

- [wrangler.toml](wrangler.toml) - Worker name, R2 binding, route binding.
- [src/worker.ts](src/worker.ts) - Request handler. Maps URL pathnames to
  R2 object keys, returns the object body with safe headers.
- [package.json](package.json) - Dev dependencies (`wrangler`,
  `@cloudflare/workers-types`, `typescript`) and convenience scripts.
- [tsconfig.json](tsconfig.json) - Strict TS config scoped to `src/`.
- `.gitignore` - Excludes `node_modules/`, `.wrangler/`, and the local
  `content/` staging folder so private files never get committed.
