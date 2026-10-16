# Vacío — editor

Workbench for the endless-drift toy in the Lab of [mxnchv.xyz](https://mxnchv.xyz/lab).

- `vacio-editor.html` — the game with every control: form toggles, feedback amount, names, and
  the **mesa de sonido** (one strip per voice, solo/mute, "probar", per-note randomness).
  Open it in a browser, tune by ear, then press **copiar ajustes**.
- `tools/make_site_js.py` — builds the site's `vacio.js` from the editor (same engine, no UI):

  ```
  python3 tools/make_site_js.py vacio-editor.html ../mxnchv.xyz/vacio.js
  ```

  Paste the copied settings into `TUNED` in the generated `vacio.js`, bump `vacio.js?v=` in the
  site's `index.html`, and run the site's `tools/build_pages.py`.
