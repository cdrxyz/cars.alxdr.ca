# Alexander Private Cars

Premium private transportation in Waterloo, Ontario. Website deployed at [cars.alxdr.ca](https://cars.alxdr.ca).

## Deployment

The site auto-deploys to GitHub Pages on push to `master` via GitHub Actions.

### First-time setup

1. **Enable GitHub Pages**: Go to repo Settings → Pages → Source → select "GitHub Actions"
2. **Configure DNS**: Add a CNAME record for `cars` on `alxdr.ca` pointing to `cdrxyz.github.io`
3. **Push to master** — the workflow will deploy automatically

## Design Assets

### Logo — [`design/logo/`](design/logo/)

- `logo-primary` — Gold shield + text on transparent background (default)
- `logo-dark` — Dark version for light backgrounds
- `logo-light` — Light version for dark backgrounds
- `icon` — Shield icon only

Each available in SVG and PNG formats.

### Business Cards — [`design/business-cards/`](design/business-cards/)

- `business-card-dark.pdf` — Black card with gold accents
- `business-card-light.pdf` — White card with gold accents
- `business-card-template.pdf` — Original dark template

Formatted for Avery 8371 perforated paper (3.5" × 2", 10 per sheet) available at Staples.

## TODO

- [ ] Consider integrating [Formsubmit](https://formsubmit.co/) for the contact form so submissions go directly to email without opening the user's mail client. Free, no signup, works with GitHub Pages — just change the form action to `https://formsubmit.co/cars@alxdr.ca`.
