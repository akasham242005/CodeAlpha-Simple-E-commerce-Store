import sqlite3
from pathlib import Path
from datetime import datetime, timezone

SEED_PRODUCTS = [
    ("AeroBook 14", "Laptop", 64999.00, 12, "💻", "Slim 14-inch laptop for work, study, and everyday productivity."),
    ("Pulse X1", "Headphones", 3999.00, 25, "🎧", "Wireless over-ear headphones with immersive sound and comfortable cushions."),
    ("Urban Runner", "Shoes", 2999.00, 30, "👟", "Lightweight everyday running shoes with breathable mesh."),
    ("PixelCam Mini", "Camera", 18999.00, 8, "📷", "Compact digital camera for travel, family moments, and casual photography."),
    ("Nova Watch", "Wearables", 5499.00, 18, "⌚", "Smart everyday watch with activity tracking and notification support."),
    ("CarryPro 25", "Bags", 2499.00, 20, "🎒", "Durable 25L backpack with laptop sleeve and multiple storage compartments."),
    ("KeyLite", "Accessories", 1299.00, 40, "⌨️", "Compact wireless keyboard designed for a clean desk setup."),
    ("GlowDesk", "Home", 1799.00, 15, "💡", "Adjustable LED desk lamp for reading, studying, and focused work."),
]

def connect(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path):
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0),
                stock INTEGER NOT NULL CHECK(stock >= 0),
                emoji TEXT NOT NULL,
                description TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total REAL NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Placed',
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );
            """
        )

        count = conn.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"]
        if count == 0:
            conn.executemany(
                """
                INSERT INTO products
                    (name, category, price, stock, emoji, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                SEED_PRODUCTS,
            )

def get_products(db_path):
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM products ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]

def get_product(db_path, product_id):
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return dict(row) if row else None

def create_user(db_path, name, email, password_hash):
    try:
        with connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, password_hash, datetime.now(timezone.utc).isoformat()),
            )
        return True, "Account created."
    except sqlite3.IntegrityError:
        return False, "An account with that email already exists."

def authenticate_user(db_path, email, password, verify_password):
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

    if row and verify_password(password, row["password_hash"]):
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
        }
    return None

def create_order(db_path, user_id, items, address, phone, payment_method):
    # Re-read stock inside one transaction so checkout uses current DB values.
    with connect(db_path) as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            prepared = []
            total = 0.0

            for product, requested_qty in items:
                row = conn.execute(
                    "SELECT * FROM products WHERE id = ?",
                    (product["id"],),
                ).fetchone()

                if row is None:
                    raise ValueError(f"Product #{product['id']} no longer exists.")
                if requested_qty < 1 or requested_qty > row["stock"]:
                    raise ValueError(
                        f"Not enough stock for {row['name']}. Available: {row['stock']}."
                    )

                line_total = row["price"] * requested_qty
                total += line_total
                prepared.append((dict(row), requested_qty))

            cur = conn.execute(
                """
                INSERT INTO orders
                    (user_id, total, address, phone, payment_method, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'Placed', ?)
                """,
                (
                    user_id,
                    total,
                    address,
                    phone,
                    payment_method,
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                ),
            )
            order_id = cur.lastrowid

            for product, qty in prepared:
                conn.execute(
                    """
                    INSERT INTO order_items
                        (order_id, product_id, product_name, quantity, unit_price)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (order_id, product["id"], product["name"], qty, product["price"]),
                )
                conn.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    (qty, product["id"]),
                )

            conn.commit()
            return order_id
        except Exception:
            conn.rollback()
            raise

def get_user_orders(db_path, user_id):
    with connect(db_path) as conn:
        orders = conn.execute(
            """
            SELECT *
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()

        result = []
        for order in orders:
            items = conn.execute(
                """
                SELECT *
                FROM order_items
                WHERE order_id = ?
                ORDER BY id
                """,
                (order["id"],),
            ).fetchall()
            data = dict(order)
            data["items"] = [dict(item) for item in items]
            result.append(data)
        return result
