# Flood Hydro Group Website

Personal academic website for ZHAO Gang, built with Jekyll and the Academic Pages theme.

## Local Preview

Install dependencies once:

```bash
bundle install
```

Start a local preview:

```bash
bundle exec jekyll serve --livereload --host localhost
```

Then open:

```text
http://localhost:4000/website/
```

## Common Maintenance

- Homepage: edit `_pages/about.md`
- CV: edit `_pages/cv.md`
- Publications: edit files in `_publications/`, or update `_data/pubs_orcid.json`
- Navigation menu: edit `_data/navigation.yml`
- Profile/sidebar details: edit `_config.yml`
- Images and PDFs: place files in `images/` or `files/`

## Deploy

Commit changes and push to `master`. GitHub Pages will rebuild the site automatically.

Current project-page URL:

```text
https://gangzhao-hydro.github.io/website/
```
