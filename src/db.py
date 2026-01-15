import sqlite3
import os

DB_PATH = "data/fulfillment.db"

def get_conn():
    # Ensure the data folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        created_ts TEXT,
        due_ts TEXT,
        channel TEXT,
        items_count INTEGER,
        distance_miles REAL,
        is_expedited INTEGER
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fulfillment_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        worker_id TEXT,
        picked_ts TEXT,
        packed_ts TEXT,
        ready_ts TEXT,
        delivered_ts TEXT,
        status TEXT,
        out_of_stock_items INTEGER,
        FOREIGN KEY(order_id) REFERENCES orders(order_id)
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("DB initialized:", DB_PATH)
