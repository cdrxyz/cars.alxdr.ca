# Alexander Private Cars

Premium private transportation in Waterloo, Ontario. Website deployed at [cars.alxdr.ca](https://cars.alxdr.ca).

## Deployment

The site auto-deploys to GitHub Pages on push to `master` via GitHub Actions.

### First-time setup

1. **Enable GitHub Pages**: Go to repo Settings → Pages → Source → select "GitHub Actions"
2. **Configure DNS**: Add a CNAME record for `cars` on `alxdr.ca` pointing to `cdrxyz.github.io`
3. **Push to master** — the workflow will deploy automatically

## TODO

- [ ] Consider integrating [Formsubmit](https://formsubmit.co/) for the contact form so submissions go directly to email without opening the user's mail client. Free, no signup, works with GitHub Pages — just change the form action to `https://formsubmit.co/cars@alxdr.ca`.
