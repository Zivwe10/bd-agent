"""
setup_database.py
Creates a SQLite database (data/bd_agent.db) and seeds it from existing JSON files.
Safe to re-run: drops and recreates all tables each time.
"""

import sqlite3
import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH   = os.path.join('data', 'bd_agent.db')
DATA_DIR  = 'data'

# -- Schema --------------------------------------------------------------------

SCHEMA = """
CREATE TABLE clients (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT    NOT NULL UNIQUE,
    last_meeting_date TEXT,
    open_issues       TEXT    -- JSON array stored as text
);

CREATE TABLE client_products (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id  INTEGER NOT NULL REFERENCES clients(id),
    product    TEXT    NOT NULL
);

CREATE TABLE orders (
    order_id      TEXT PRIMARY KEY,
    customer_name TEXT    NOT NULL,
    territory     TEXT    NOT NULL,
    order_date    TEXT    NOT NULL,
    status        TEXT    NOT NULL,
    total_amount  REAL    NOT NULL
);

CREATE TABLE order_lines (
    line_id      TEXT PRIMARY KEY,
    order_id     TEXT NOT NULL REFERENCES orders(order_id),
    sku          TEXT NOT NULL,
    product_name TEXT NOT NULL,
    quantity     INTEGER NOT NULL,
    unit_price   REAL    NOT NULL,
    line_total   REAL    NOT NULL
);
"""

# -- Helpers -------------------------------------------------------------------

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# -- Main ----------------------------------------------------------------------

def setup():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Remove existing DB so we get a clean slate
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    # Create tables
    cur.executescript(SCHEMA)
    print("Created tables: clients, client_products, orders, order_lines")

    # -- Seed clients ----------------------------------------------------------
    clients = load_json('clients.json')
    client_id_map = {}

    for c in clients:
        cur.execute(
            "INSERT INTO clients (name, last_meeting_date, open_issues) VALUES (?, ?, ?)",
            (c['name'], c.get('last_meeting_date'), json.dumps(c.get('open_issues', [])))
        )
        client_id = cur.lastrowid
        client_id_map[c['name']] = client_id

        for product in c.get('products', []):
            cur.execute(
                "INSERT INTO client_products (client_id, product) VALUES (?, ?)",
                (client_id, product)
            )

    print(f"Seeded {len(clients)} clients")

    # -- Seed orders -----------------------------------------------------------
    orders = load_json('orders.json')
    cur.executemany(
        """INSERT INTO orders (order_id, customer_name, territory, order_date, status, total_amount)
           VALUES (:order_id, :customer_name, :territory, :order_date, :status, :total_amount)""",
        orders
    )
    print(f"Seeded {len(orders)} orders")

    # -- Seed order lines ------------------------------------------------------
    order_lines = load_json('order_lines.json')
    cur.executemany(
        """INSERT INTO order_lines (line_id, order_id, sku, product_name, quantity, unit_price, line_total)
           VALUES (:line_id, :order_id, :sku, :product_name, :quantity, :unit_price, :line_total)""",
        order_lines
    )
    print(f"Seeded {len(order_lines)} order lines")

    con.commit()
    con.close()

    # -- Quick verification ----------------------------------------------------
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    print("\n-- Verification --------------------------------")

    cur.execute("SELECT COUNT(*) AS n FROM clients")
    print(f"  clients:      {cur.fetchone()['n']}")

    cur.execute("SELECT COUNT(*) AS n FROM client_products")
    print(f"  client_products: {cur.fetchone()['n']}")

    cur.execute("SELECT COUNT(*) AS n FROM orders")
    print(f"  orders:       {cur.fetchone()['n']}")

    cur.execute("SELECT COUNT(*) AS n FROM order_lines")
    print(f"  order_lines:  {cur.fetchone()['n']}")

    cur.execute("""
        SELECT territory, COUNT(*) as cnt, ROUND(SUM(total_amount),2) as revenue
        FROM orders GROUP BY territory ORDER BY revenue DESC
    """)
    print("\n-- Revenue by territory -------------------------")
    for row in cur.fetchall():
        print(f"  {row['territory']:10s}  {row['cnt']} orders   ${row['revenue']:,.2f}")

    con.close()
    print(f"\nDatabase ready: {DB_PATH}")


if __name__ == '__main__':
    setup()
