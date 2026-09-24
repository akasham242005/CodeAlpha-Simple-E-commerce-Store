# Streamlit deployment checklist

## GitHub repository

The repository root should look like this:

```text
streamlit_app.py
db.py
styles.css
requirements.txt
README.md
.streamlit/config.toml
data/.gitkeep
```

Do not upload `.venv/` or `data/store.db`.

## Streamlit Community Cloud

Use:

- Repository: your GitHub repository
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python: 3.12 is a good default if available in the deployment dialog

No secrets are required.

## If deployment shows "ModuleNotFoundError"

Make sure `requirements.txt` is in the repository root and contains:

```text
streamlit>=1.40,<2
```

Then redeploy/reboot the app.

## If the database seems empty

That is expected on a fresh runtime: the app automatically creates `data/store.db` and inserts the sample products.

## Production database

For a real store, move users/orders/products to a managed PostgreSQL database. Do not commit database credentials to GitHub; use Streamlit Secrets or the database provider's secure environment variables.
