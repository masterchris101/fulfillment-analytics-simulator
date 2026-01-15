import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import random
from datetime import datetime, timedelta
import sqlite3
from faker import Faker

from src.db import init_db, DB_PATH

fake = Faker()

CHANNELS = ["BOPIS", "Delivery", "ShipToHome"]
WORKERS = ["W1", "W2", "W3", "W4", "W5"]

def random_ts(start: datetime, minutes_min: int, minutes_max: int):
    return start + timedelta(minutes=random.randint(minutes_min, minutes_max))

def generate_orders(n=400, seed=42):
    random.seed(seed)
    base = datetime.now() - timedelta(days=30)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for _ in range(n):
        created = base + timedelta(minutes=random.randint(0, 30 * 24 * 60))
        due = created + timedelta(hours=random.randint(2, 48))

        order_id = fake.uuid4()
        channel = random.choice(CHANNELS)
        items = random.randint(1, 25)
        distance = round(random.uniform(0.5, 25.0), 2)
        expedited = 1 if random.random() < 0.18 else 0

        worker = random.choice(WORKERS)
        pick = random_ts(created, 8, 120)
        pack = random_ts(pick, 3, 40)
        ready = random_ts(pack, 2, 35)

        out_of_stock = 0
        status = "Completed"
        delivered = None

        if random.random() < min(0.05 + items * 0.01, 0.35):
            out_of_stock = random.randint(1, min(3, items))
            if random.random() < 0.25:
                status = "Canceled"

        if status != "Canceled":
            if channel == "BOPIS":
                delivered = random_ts(ready, 10, 600)
            elif channel == "Delivery":
                delivered = random_ts(ready, 60, 1440)
            else:
                delivered = random_ts(ready, 240, 2880)

            if delivered > due and random.random() < 0.35:
                status = "Late"

        cur.execute("""
            INSERT OR REPLACE INTO orders
            (order_id, created_ts, due_ts, channel, items_count, distance_miles, is_expedited)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            created.isoformat(),
            due.isoformat(),
            channel,
            items,
            distance,
            expedited
        ))

        cur.execute("""
            INSERT INTO fulfillment_events
            (order_id, worker_id, picked_ts, packed_ts, ready_ts, delivered_ts, status, out_of_stock_items)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            worker,
            pick.isoformat(),
            pack.isoformat(),
            ready.isoformat(),
            delivered.isoformat() if delivered else None,
            status,
            out_of_stock
        ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    generate_orders(400)
    print("Generated 400 orders into:", DB_PATH)
