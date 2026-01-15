import streamlit as st
import pandas as pd

from src.db import init_db
from src.generate_data import generate_orders
from src.analysis import (
    kpis,
    worker_perf,
    orders_detail,
    status_breakdown,
    ready_time_distribution,
)

st.set_page_config(page_title="Fulfillment Analytics Simulator", layout="wide")
st.title("📦 Order Fulfillment Analytics Simulator")

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Controls")

    if st.button("Initialize DB"):
        init_db()
        st.success("Database initialized.")

    n = st.slider("Generate synthetic orders", 100, 2000, 400, 100)
    seed = st.number_input("Random seed", min_value=1, max_value=99999, value=42, step=1)

    if st.button("Generate synthetic data"):
        init_db()
        generate_orders(int(n), seed=int(seed))
        st.success(f"Generated {n} orders.")

# ---------------- KPIs ----------------
k = kpis()
if k.empty:
    st.warning("No data found. Use the sidebar to generate synthetic data.")
    st.stop()

total_orders = int(k.loc[0, "total_orders"])
completed = int(k.loc[0, "completed"])
late = int(k.loc[0, "late"])
canceled = int(k.loc[0, "canceled"])
avg_ready = float(k.loc[0, "avg_minutes_to_ready"])
avg_oos = float(k.loc[0, "avg_oos_items"])

late_rate = (late / total_orders) * 100 if total_orders else 0
cancel_rate = (canceled / total_orders) * 100 if total_orders else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Orders", total_orders)
c2.metric("Completed", completed)
c3.metric("Late", late)
c4.metric("Canceled", canceled)
c5.metric("Avg Minutes to Ready", f"{avg_ready:.1f}")
c6.metric("Late Rate", f"{late_rate:.1f}%")

st.caption(f"Avg out-of-stock items per order: **{avg_oos:.2f}**")

st.info(
    f"**Key Insights**\n\n"
    f"- Late rate: **{late_rate:.1f}%** | Cancel rate: **{cancel_rate:.1f}%**\n"
    f"- Avg minutes to ready: **{avg_ready:.1f}**\n"
    f"- Avg out-of-stock items per order: **{avg_oos:.2f}**\n"
    f"- Use filters below to isolate bottlenecks by channel, worker, and status."
)

# ---------------- Charts ----------------
st.subheader("Charts")
left, right = st.columns(2)

with left:
    sb = status_breakdown()
    st.bar_chart(sb.set_index("status")["orders"])

with right:
    dist = ready_time_distribution()
    st.write("Minutes to Ready (distribution)")

    bins = pd.cut(dist["minutes_to_ready"], bins=20)
    hist = bins.value_counts().sort_index()

    hist_df = hist.reset_index()
    hist_df.columns = ["bucket", "count"]
    hist_df["bucket"] = hist_df["bucket"].astype(str)

    st.bar_chart(hist_df.set_index("bucket")["count"])

st.divider()

# ---------------- Worker Performance ----------------
st.subheader("Worker Performance")
wp = worker_perf()
st.dataframe(wp, width="stretch")

st.divider()

# ---------------- Order Detail ----------------
st.subheader("Order Detail (Most recent)")
detail = orders_detail(500)

channels = sorted(detail["channel"].dropna().unique().tolist())
statuses = sorted(detail["status"].dropna().unique().tolist())
workers = sorted(detail["worker_id"].dropna().unique().tolist())

f1, f2, f3 = st.columns(3)
selected_channels = f1.multiselect("Channel", channels, default=channels)
selected_statuses = f2.multiselect("Status", statuses, default=statuses)
selected_workers = f3.multiselect("Worker", workers, default=workers)

filtered = detail[
    detail["channel"].isin(selected_channels)
    & detail["status"].isin(selected_statuses)
    & detail["worker_id"].isin(selected_workers)
].copy()

st.dataframe(filtered, width="stretch")
