# 🛍️ ShopEase — Streamlit E-commerce Store

A complete beginner-friendly e-commerce project built specifically so it can be deployed as a **Streamlit app** without needing Django/Node.js server configuration.

## Features

- Product listing / catalog
- Product search and category filtering
- Product details page
- Shopping cart
- User registration
- User login with salted PBKDF2 password hashing
- Checkout and order processing
- SQLite database for products, users, orders, and order items
- Stock validation during checkout
- Order history
- Responsive styling
- Seed products created automatically on first run
- No external API keys required
- No `packages.txt` or system packages required

## Project structure

```text
ecommerce_streamlit_store/
├── streamlit_app.py
├── db.py
├── styles.css
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
└── data/
    └── .gitkeep
```

## Run locally

Python 3.11 or 3.12 is recommended.

### Windows

```powershell
cd ecommerce_streamlit_store
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

### macOS/Linux

```bash
cd ecommerce_streamlit_store
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Then open the local URL printed by Streamlit, normally:

```text
http://localhost:8501
```

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload the contents of this project to the repository.
3. Keep `streamlit_app.py` in the repository root.
4. Go to Streamlit Community Cloud and choose **Create app**.
5. Select the GitHub repository, branch, and `streamlit_app.py`.
6. Deploy.

The included `requirements.txt` is intentionally small and the project uses only Python standard-library modules plus Streamlit.

## Database note

This project uses SQLite because it makes the assignment self-contained and easy to deploy. The database file is created automatically at:

```text
data/store.db
```

On cloud hosting, local application storage can be ephemeral. That means this SQLite database is suitable for a classroom/demo deployment, but it should be replaced with a managed database such as PostgreSQL for production data that must survive application replacement or redeployment.

## Demo flow

1. Open **Login / Register**.
2. Create a new account.
3. Return to products.
4. Open a product and add it to the cart.
5. Open **Shopping Cart**.
6. Enter a delivery address and phone number.
7. Place the order.
8. Open **My Orders** to see the saved order.

## Important deployment choice

The original assignment allows Django or Express.js as the backend. A normal Django/Express server cannot be started directly by selecting a `.py`/`.js` backend as the Streamlit Community Cloud entrypoint. This implementation therefore uses **Streamlit itself as the web application layer**, with SQLite as the database, so the whole assignment is contained in one Streamlit-deployable project.

This keeps deployment simple: the Community Cloud entrypoint is just `streamlit_app.py`.
