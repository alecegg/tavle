# Third-party licences

Tavle has no runtime Python dependencies.

## Vendored browser code

`src/tavle/static/vendor/mithril.js` is Mithril 2.3.8 (MIT, licence in `mithril.LICENSE`), the unmodified `mithril.min.js` from <https://registry.npmjs.org/mithril/-/mithril-2.3.8.tgz> (npm integrity `sha512-za/Yo7qXEckjm5syrSfaaI9Utf4tCUT3T1IOIYqH6Lrj7G0OZuYYLAY9SV4ygoaAf0+CNqU92MBt+7pmo53JVQ==`) behind a one-line header. `tests/test_vendor_mithril.py` checks the file against this row.

| File | Version | Licence | SHA-256 |
|---|---|---|---|
| `src/tavle/static/vendor/mithril.js` | 2.3.8 | MIT | `87b87d475d600eec08a1e0553a376614853f06d9f0fb0efecd211c38bfa84f3f` |
