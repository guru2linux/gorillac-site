# gorillac.net

Personal portfolio and resume website for [gorillac.net](https://gorillac.net).

## Hosting
This site is hosted locally on a **Proxmox** `qaserver` and exposed to the internet via a **Cloudflare Tunnel**.

## Project Structure
```
.
└── website/         # Static HTML/CSS/JS files
    ├── index.html
    ├── resume.html
    ├── portfolio.html
    ├── contact.html
    ├── job-application-tracker-demo.html
    ├── job-copilot-demo.html
    ├── projects.json
    └── certs/       # CompTIA certification badge images
```

## Local Development
Since this is a static site, you can serve it using any simple HTTP server. For example:
```bash
cd website
python3 -m http.server 8000
```
Then navigate to `http://localhost:8000`.
