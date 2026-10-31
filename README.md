# Altawakol Cables — website

Static bilingual site (EN + AR) for Altawakol Cables, tawakolcables.com, served by GitHub Pages from the repository root.

- Site files: everything except `source/`. Regenerated, never edited by hand.
- `source/`: the generator. Edit `source/conductors.csv` (one row per conductor code) or `source/i18n.py` (all text), then:
  `cd source && pip install jinja2 reportlab pillow && TARGET=pages SITE_URL=https://tawakolcables.com python3 build.py`
  and copy `source/dist/*` to the repository root (`cp -r dist/. ..`), commit, push.
- RFQ form: opens the visitor's email app prefilled (no server). To receive submissions in an inbox instead, create a free
  Formspree form and rebuild with `FORM_ENDPOINT=https://formspree.io/f/XXXX`.
- Catalogue and type-test PDFs live in `assets/docs/` at the root; they are not duplicated in `source/`.
