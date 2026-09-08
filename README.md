# gorillac.net

Personal portfolio and resume website for [gorillac.net](https://gorillac.net).

## Hosting
This site is hosted locally on a **Proxmox** `qaserver` and exposed to the internet via a **Cloudflare Tunnel**.
TLS terminates at Cloudflare; nginx on the origin serves the static files from `/opt/gorillac`.

## Project Structure
```
.
├── website/                 # Everything here is deployed (rsync'd to /opt/gorillac)
│   ├── index.html
│   ├── resume.html
│   ├── portfolio.html
│   ├── contact.html
│   ├── job-application-tracker-demo.html
│   ├── job-copilot-demo.html
│   ├── projects.json        # Portfolio content — edit this, not portfolio.html
│   ├── robots.txt
│   ├── sitemap.xml
│   ├── favicon.ico / favicon-16.png / favicon-32.png / apple-touch-icon.png
│   ├── certs/               # CompTIA certification badge images
│   └── imgs/                # avatar.webp + avatar.png (site logo), og-image.jpg (social card)
├── deploy/
│   └── nginx-gorillac.conf  # Origin server block incl. security headers — NOT auto-deployed
├── assets-src/              # Master art, deliberately outside website/ so it isn't served
│   └── logo-master.png      # 1408x768 original; all icons/avatars are derived from this
└── notes/                   # Scratch work for other repos; not part of the site
```

## Editing content
Portfolio projects and the tools taxonomy live in `website/projects.json` — `portfolio.html` renders
them at load time. Adding a project means adding an object to `projects[]`; no HTML changes needed.

## Local Development
```bash
cd website
python3 -m http.server 8000
```
Then navigate to `http://localhost:8000`.

## Deployment
A push to `main` triggers `.github/workflows/deploy.yml`. Per REM-003 the job runs on the isolated
`ci-runner` CT — **not** on the production box — and reaches `qaserver` only through a forced-command
SSH key (`ci_deploy_ed25519` → `ci-deploy.sh`), which streams a tarball of `website/` over the
restricted `deploy-gorillac` channel. The runner has no other access to production.

Only `website/` is shipped. `deploy/`, `assets-src/`, and `notes/` stay in the repo and are never
served — keep it that way when adding files, since anything placed under `website/` becomes public.

### Caching gotcha
The origin currently serves `projects.json` with `max-age=2592000` (30 days). Since the portfolio
page renders from that file, an edit to it can stay invisible to anyone who has loaded the page
before — the browser never re-requests it. Two mitigations are in place:

- `portfolio.html` fetches with `{ cache: 'no-cache' }`, forcing a revalidation (a cheap 304 when
  nothing changed). This works regardless of server config.
- `deploy/nginx-gorillac.conf` sets `no-cache` on `.json`/`.xml`/`.txt` as well as `.html`, which
  fixes it at the source — but only once that config is installed on the origin.

If you replace an **image** without renaming it, the edge and browser copies can still be stale.
Either rename the file (`avatar-v2.webp`) or purge manually:

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/9a92398265ad7b4015449ac0bd0748cf/purge_cache" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

An automated purge step was tried and removed — it needed a `Zone / Cache Purge` API token stored as
a repo secret, which is more credential surface than a site this size warrants. Renaming changed
images achieves the same thing with no secret to manage.

### Origin nginx config
`deploy/nginx-gorillac.conf` is **not** applied by the deploy workflow — it is a manual step on the
origin host:

```bash
sudo cp deploy/nginx-gorillac.conf /etc/nginx/conf.d/gorillac.conf
sudo nginx -t && sudo systemctl reload nginx
```

It sets HSTS, CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and
`Permissions-Policy`, plus extensionless URL routing (`/resume` → `resume.html`) and cache headers.
Verify after reload:

```bash
curl -sI https://gorillac.net/ | grep -iE 'strict-transport|content-security|x-frame|x-content-type|referrer|permissions'
```

## Regenerating images
All derived images come from `assets-src/logo-master.png`:

```bash
# Avatar (150px display, 2x)
magick assets-src/logo-master.png -crop 768x768+320+0 +repage -resize 300x300 -strip \
  -quality 86 -define webp:method=6 website/imgs/avatar.webp
magick assets-src/logo-master.png -crop 768x768+320+0 +repage -resize 300x300 -strip \
  -colors 128 -dither FloydSteinberg PNG8:website/imgs/avatar.png

# Social preview card
magick assets-src/logo-master.png -resize 1200x -gravity center -crop 1200x630+0+0 +repage \
  -strip -quality 84 website/imgs/og-image.jpg

# Icons (tight crop on the gorilla — the wordmark is illegible at favicon sizes)
magick assets-src/logo-master.png -crop 340x340+570+140 +repage -strip /tmp/icon-src.png
magick /tmp/icon-src.png -resize 180x180 -colors 128 -strip PNG8:website/apple-touch-icon.png
magick /tmp/icon-src.png -resize 32x32 -strip website/favicon-32.png
magick /tmp/icon-src.png -resize 16x16 -strip website/favicon-16.png
magick /tmp/icon-src.png \( -clone 0 -resize 16x16 \) \( -clone 0 -resize 32x32 \) \
  \( -clone 0 -resize 48x48 \) -delete 0 -strip website/favicon.ico
```
