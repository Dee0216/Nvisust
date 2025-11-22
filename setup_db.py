import sqlite3
from pathlib import Path

DB_PATH = Path("data/sql_expert.db")
DB_PATH.parent.mkdir(exist_ok=True)

schema_sql = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    loyalty_tier TEXT CHECK (loyalty_tier IN ('Bronze','Silver','Gold','Platinum'))
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    list_price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TEXT NOT NULL,
    status TEXT CHECK (status IN ('pending','shipped','delivered','cancelled')),
    total_amount DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL
);
"""
 
seed_sql = """
INSERT OR REPLACE INTO customers VALUES
(1,'Alice Johnson','alice@example.com','Gold'),
(2,'Brian Patel','brian@example.com','Silver'),
(3,'Carla Mendes','carla@example.com','Bronze');

INSERT OR REPLACE INTO products VALUES
(101,'Smart Speaker','Electronics',129.99),
(102,'Noise-Cancelling Headphones','Electronics',249.00),
(201,'Espresso Machine','Home',399.50),
(301,'Trail Running Shoes','Sports',149.00);

INSERT OR REPLACE INTO orders VALUES
(5001,1,'2024-09-12','delivered',528.99),
(5002,2,'2024-09-15','shipped',249.00),
(5003,1,'2024-10-01','pending',149.00);

INSERT OR REPLACE INTO order_items VALUES
(9001,5001,101,2,119.99),
(9002,5001,201,1,289.01),
(9003,5002,102,1,249.00),
(9004,5003,301,1,149.00);
"""
with sqlite3.connect(DB_PATH) as conn:
    conn.executescript(schema_sql)
    conn.executescript(seed_sql)
    conn.commit()

print(f"Database ready at {DB_PATH}")