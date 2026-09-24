import streamlit as st
from db import (
    init_db, get_products, get_product, create_user, authenticate_user,
    create_order, get_user_orders
)
from pathlib import Path
import hashlib
import hmac
import os

st.set_page_config(
    page_title="ShopEase | Simple E-commerce",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "store.db"

# ---------- Styling ----------
CSS_PATH = BASE_DIR / "styles.css"
if CSS_PATH.exists():
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ---------- Initialization ----------
init_db(DB_PATH)

if "user" not in st.session_state:
    st.session_state.user = None
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

def money(value):
    return f"₹{value:,.2f}"

def password_hash(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def add_to_cart(product_id: int):
    products = get_products(DB_PATH)
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return
    current = st.session_state.cart.get(product_id, 0)
    if current < product["stock"]:
        st.session_state.cart[product_id] = current + 1
        st.toast(f"{product['name']} added to cart 🛒")
    else:
        st.warning("No more stock available for this product.")

def cart_count():
    return sum(st.session_state.cart.values())

def cart_items():
    products = get_products(DB_PATH)
    by_id = {p["id"]: p for p in products}
    items = []
    for pid, qty in st.session_state.cart.items():
        product = by_id.get(pid)
        if product:
            items.append((product, qty))
    return items

def navigate(page):
    st.session_state.page = page
    st.session_state.selected_product = None
    st.rerun()

# ---------- Header ----------
st.markdown(
    """
    <div class="hero">
        <div>
            <div class="brand">🛍️ ShopEase</div>
            <div class="tagline">A simple, complete e-commerce demo built for Streamlit</div>
        </div>
        <div class="hero-badge">Django/Express-style task • Streamlit-ready</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    if st.button("🏠 Home", use_container_width=True):
        navigate("Home")
    if st.button("🛒 Shopping Cart", use_container_width=True):
        navigate("Cart")
    if st.button("📦 My Orders", use_container_width=True):
        navigate("Orders")

    st.divider()
    st.markdown("### 👤 Account")
    if st.session_state.user:
        st.success(f"Signed in as **{st.session_state.user['name']}**")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "Home"
            st.rerun()
    else:
        if st.button("🔐 Login / Register", use_container_width=True):
            navigate("Auth")

    st.divider()
    st.metric("Cart items", cart_count())

# ---------- Home / Product listing ----------
def render_home():
    st.title("Featured Products")
    st.caption("Browse products, open details, add items to your cart, and place an order.")

    products = get_products(DB_PATH)
    search = st.text_input("🔎 Search products", placeholder="Try: laptop, shoes, headphones...")
    category = st.selectbox(
        "Category",
        ["All"] + sorted({p["category"] for p in products}),
        horizontal=True,
    )

    filtered = products
    if search:
        q = search.lower().strip()
        filtered = [
            p for p in filtered
            if q in p["name"].lower()
            or q in p["description"].lower()
            or q in p["category"].lower()
        ]
    if category != "All":
        filtered = [p for p in filtered if p["category"] == category]

    st.markdown(f"**{len(filtered)} product(s) found**")

    cols = st.columns(3)
    for i, product in enumerate(filtered):
        with cols[i % 3]:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="product-icon">{product["emoji"]}</div>', unsafe_allow_html=True)
            st.markdown(f"### {product['name']}")
            st.caption(f"{product['category']} • {product['stock']} in stock")
            st.markdown(f"**{money(product['price'])}**")
            st.write(product["description"])
            c1, c2 = st.columns(2)
            with c1:
                if st.button("View details", key=f"detail_{product['id']}", use_container_width=True):
                    st.session_state.selected_product = product["id"]
                    st.session_state.page = "Product"
                    st.rerun()
            with c2:
                if st.button("Add to cart", key=f"add_{product['id']}", use_container_width=True):
                    add_to_cart(product["id"])
            st.markdown("</div>", unsafe_allow_html=True)

def render_product():
    product = get_product(DB_PATH, st.session_state.selected_product)
    if not product:
        st.error("Product not found.")
        return

    if st.button("← Back to products"):
        navigate("Home")

    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    left, right = st.columns([1, 2])
    with left:
        st.markdown(f'<div class="detail-icon">{product["emoji"]}</div>', unsafe_allow_html=True)
    with right:
        st.caption(product["category"])
        st.title(product["name"])
        st.markdown(f"# {money(product['price'])}")
        st.write(product["description"])
        st.markdown(f"**Available stock:** {product['stock']}")
        qty = st.number_input(
            "Quantity",
            min_value=1,
            max_value=max(1, product["stock"]),
            value=1,
            step=1,
            key=f"qty_{product['id']}",
        )
        if st.button("🛒 Add selected quantity", type="primary"):
            current = st.session_state.cart.get(product["id"], 0)
            st.session_state.cart[product["id"]] = min(current + qty, product["stock"])
            st.toast("Added to cart!")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Authentication ----------
def render_auth():
    st.title("🔐 Account")
    login_tab, register_tab = st.tabs(["Login", "Create account"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary")
            if submitted:
                user = authenticate_user(DB_PATH, email, password, verify_password)
                if user:
                    st.session_state.user = user
                    st.success("Login successful.")
                    st.session_state.page = "Home"
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with register_tab:
        with st.form("register_form"):
            name = st.text_input("Full name")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account", type="primary")
            if submitted:
                if not name.strip() or not email.strip() or not password:
                    st.error("Please complete all fields.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must contain at least 6 characters.")
                else:
                    ok, message = create_user(
                        DB_PATH, name.strip(), email.strip().lower(),
                        password_hash(password)
                    )
                    if ok:
                        st.success("Account created. You can now log in.")
                    else:
                        st.error(message)

# ---------- Cart ----------
def render_cart():
    st.title("🛒 Shopping Cart")
    items = cart_items()

    if not items:
        st.info("Your cart is empty. Add some products from the home page.")
        if st.button("Browse products", type="primary"):
            navigate("Home")
        return

    total = 0.0
    for product, qty in items:
        subtotal = product["price"] * qty
        total += subtotal
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        with c1:
            st.markdown(f"**{product['emoji']} {product['name']}**")
            st.caption(money(product["price"]) + " each")
        with c2:
            new_qty = st.number_input(
                "Qty",
                min_value=1,
                max_value=max(1, product["stock"]),
                value=min(qty, product["stock"]),
                key=f"cart_qty_{product['id']}",
            )
            st.session_state.cart[product["id"]] = new_qty
        with c3:
            st.markdown(f"**{money(subtotal)}**")
        with c4:
            if st.button("Remove", key=f"remove_{product['id']}"):
                st.session_state.cart.pop(product["id"], None)
                st.rerun()
        st.divider()

    st.markdown(f"## Total: {money(total)}")

    if not st.session_state.user:
        st.warning("Please log in or create an account before checkout.")
        if st.button("Login / Register", type="primary"):
            navigate("Auth")
        return

    with st.expander("📍 Checkout details", expanded=True):
        address = st.text_area("Delivery address", placeholder="House / street / city / PIN")
        phone = st.text_input("Phone number")
        payment = st.selectbox("Payment method", ["Cash on Delivery", "Demo Card Payment"])
        if st.button("✅ Place order", type="primary", use_container_width=True):
            if not address.strip() or not phone.strip():
                st.error("Please enter your delivery address and phone number.")
            else:
                order_id = create_order(
                    DB_PATH,
                    st.session_state.user["id"],
                    items,
                    address.strip(),
                    phone.strip(),
                    payment,
                )
                st.session_state.cart = {}
                st.success(f"Order #{order_id} placed successfully!")
                st.session_state.page = "Orders"
                st.rerun()

# ---------- Orders ----------
def render_orders():
    st.title("📦 My Orders")
    if not st.session_state.user:
        st.info("Log in to view your orders.")
        if st.button("Login / Register", type="primary"):
            navigate("Auth")
        return

    orders = get_user_orders(DB_PATH, st.session_state.user["id"])
    if not orders:
        st.info("You haven't placed any orders yet.")
        return

    for order in orders:
        with st.expander(
            f"Order #{order['id']} • {order['created_at']} • {money(order['total'])}"
        ):
            st.write(f"**Status:** {order['status']}")
            st.write(f"**Payment:** {order['payment_method']}")
            st.write(f"**Phone:** {order['phone']}")
            st.write(f"**Delivery:** {order['address']}")
            st.markdown("**Items**")
            for item in order["items"]:
                st.write(
                    f"- {item['product_name']} × {item['quantity']} — "
                    f"{money(item['unit_price'] * item['quantity'])}"
                )

# ---------- Router ----------
page = st.session_state.page
if page == "Home":
    render_home()
elif page == "Product":
    render_product()
elif page == "Auth":
    render_auth()
elif page == "Cart":
    render_cart()
elif page == "Orders":
    render_orders()
else:
    render_home()

st.markdown(
    '<div class="footer">ShopEase • Streamlit e-commerce project • SQLite database</div>',
    unsafe_allow_html=True,
)
