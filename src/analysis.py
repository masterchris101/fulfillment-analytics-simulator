import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import sqlite3

from src.db import DB_PATH

def load_df(query: str, params=None):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn, params=params or [])
    finally:
        conn.close()
    return df

def kpis():
    return load_df("""
    SELECT
        COUNT(*) AS total_orders,
        SUM(CASE WHEN fe.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
        SUM(CASE WHEN fe.status = 'Late' THEN 1 ELSE 0 END) AS late,
        SUM(CASE WHEN fe.status = 'Canceled' THEN 1 ELSE 0 END) AS canceled,
        ROUND(AVG((julianday(fe.ready_ts) - julianday(o.created_ts)) * 24 * 60), 1) AS avg_minutes_to_ready,
        ROUND(AVG(COALESCE(fe.out_of_stock_items, 0)), 2) AS avg_oos_items
    FROM orders o
    JOIN fulfillment_events fe ON fe.order_id = o.order_id;
    """)

def worker_perf():
    return load_df("""
    SELECT
        fe.worker_id,
        COUNT(*) AS orders_handled,
        ROUND(AVG((julianday(fe.picked_ts) - julianday(o.created_ts)) * 24 * 60), 1) AS avg_pick_minutes,
        ROUND(AVG((julianday(fe.ready_ts) - julianday(o.created_ts)) * 24 * 60), 1) AS avg_ready_minutes,
        SUM(CASE WHEN fe.status = 'Late' THEN 1 ELSE 0 END) AS late_orders,
        SUM(CASE WHEN fe.status = 'Canceled' THEN 1 ELSE 0 END) AS canceled_orders
    FROM orders o
    JOIN fulfillment_events fe ON fe.order_id = o.order_id
    GROUP BY fe.worker_id
    ORDER BY orders_handled DESC;
    """)

def orders_detail(limit=300):
    return load_df(f"""
    SELECT
        o.order_id,
        o.channel,
        o.items_count,
        o.distance_miles,
        o.is_expedited,
        o.created_ts,
        o.due_ts,
        fe.worker_id,
        fe.status,
        fe.out_of_stock_items,
        ROUND((julianday(fe.ready_ts) - julianday(o.created_ts)) * 24 * 60, 1) AS minutes_to_ready,
        ROUND((julianday(fe.delivered_ts) - julianday(o.created_ts)) * 24 * 60, 1) AS minutes_to_delivered
    FROM orders o
    JOIN fulfillment_events fe ON fe.order_id = o.order_id
    ORDER BY o.created_ts DESC
    LIMIT {limit};
    """)

def status_breakdown():
    return load_df("""
    SELECT fe.status, COUNT(*) AS orders
    FROM fulfillment_events fe
    GROUP BY fe.status
    ORDER BY orders DESC;
    """)

def ready_time_distribution():
    return load_df("""
    SELECT
        ROUND((julianday(fe.ready_ts) - julianday(o.created_ts)) * 24 * 60, 1) AS minutes_to_ready
    FROM orders o
    JOIN fulfillment_events fe ON fe.order_id = o.order_id
    WHERE fe.ready_ts IS NOT NULL;
    """)
