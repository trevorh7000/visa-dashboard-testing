import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import re
from datetime import datetime
import os
import streamlit.components.v1 as components
import io

# --- Paths ---
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "decisions.db")
MSG_PATH = os.path.join(BASE_DIR, "message.txt")
DASHBOARD_PATH = os.path.join(BASE_DIR, "dashboard.py")

st.set_page_config(page_title="Visa Decisions Dashboard", layout="wide")

st.markdown("""
    <style>
    input {
        background-color: #dcdee0!important;
        color: black !important;
        border: 2px solid black !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Load data with cache busted by file mtimes ---
@st.cache_data
def load_data(db_path, msg_path, db_mtime, msg_mtime, dash_mtime):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT app_number, decision, week, end_date FROM decisions", conn)
    conn.close()
    df = df.rename(columns={"app_number": "application_number"})
    df["end_date"] = pd.to_datetime(df["end_date"])
    df = df.sort_values(by="end_date")

    with open(msg_path, "r") as f:
        msg = f.read().strip()

    return df, msg


# --- Helper functions ---
def parse_week_start(week_label):
    match = re.match(r"(\d{1,2} [A-Za-z]+) to (\d{1,2} [A-Za-z]+ \d{4})", week_label)
    if not match:
        return None
    start_str, end_str = match.groups()
    try:
        end_date = datetime.strptime(end_str, "%d %b %Y")
        start_date = datetime.strptime(start_str + f" {end_date.year}", "%d %b %Y")
        return start_date
    except Exception:
        return None

def compute_stats(df):
    df["decision"] = df["decision"].str.strip().str.capitalize()
    summary = (
        df.groupby("week")["decision"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    summary["Total"] = summary.get("Approved", 0) + summary.get("Refused", 0)
    summary["Refused %"] = (summary.get("Refused", 0) / summary["Total"] * 100).round(2)
    summary["week_start_date"] = summary["week"].apply(parse_week_start)
    summary = summary.sort_values("week_start_date").reset_index(drop=True)
    return summary

def show_chart(summary, window=8):
    weeks = summary["week"]
    approved = summary.get("Approved", pd.Series([0] * len(weeks)))
    refused = summary.get("Refused", pd.Series([0] * len(weeks)))
    total = summary["Total"]
    refused_pct = summary["Refused %"]
    approved_pct = 100 - refused_pct

    if "start_idx" not in st.session_state:
        st.session_state.start_idx = max(0, len(weeks) - window)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        left_col, right_col = st.columns([1, 1])
        with left_col:
            back_clicked = st.button("<< Back")
        with right_col:
            forward_clicked = st.button("Forward >>")

    if back_clicked:
        st.session_state.start_idx = max(0, st.session_state.start_idx - window)
    if forward_clicked:
        st.session_state.start_idx = min(len(weeks) - window, st.session_state.start_idx + window)

    start = st.session_state.start_idx
    end = start + window

    # Create the figure
    fig, ax = plt.subplots(figsize=(12, 6))
    bar1 = ax.bar(weeks[start:end], approved[start:end], label="Approved", color="green")
    bar2 = ax.bar(
        weeks[start:end], refused[start:end],
        label="Refused", color="red", bottom=approved[start:end]
    )

    # Add annotations
    for rect, pct in zip(bar1, approved_pct[start:end]):
        height = rect.get_height()
        if height > 0:
            ax.annotate(f"{int(height)} ({pct:.1f}%)",
                        xy=(rect.get_x() + rect.get_width() / 2, height / 2),
                        ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    for rect, base_height, pct in zip(bar2, approved[start:end], refused_pct[start:end]):
        height = rect.get_height()
        if height > 0:
            ax.annotate(f"{int(height)} ({pct:.1f}%)",
                        xy=(rect.get_x() + rect.get_width() / 2, base_height + height / 2),
                        ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    for i, tot in enumerate(total[start:end]):
        ax.annotate(f"Total: {int(tot)}",
                    xy=(i, tot),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center", va="bottom",
                    fontsize=9, fontweight="bold")

    ax.set_title("Visa Decisions per Week")
    ax.set_ylabel("Number of Applications")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, axis="y")
    ax.legend()
    fig.tight_layout()

    # Show in Streamlit
    st.pyplot(fig)

   
    # Optional: keep your button styling
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #4CAF50 !important;
            color: white !important;
            font-weight: bold;
            height: 40px;
            width: 140px;
            border-radius: 5px;
            border: none;
            margin: 0px;
        }
        div.stButton > button:hover {
            background-color: #45a049 !important;
        }
        div.stButton > button:focus {
            outline: none !important;
            box-shadow: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    return fig

# === MAIN APP ===

# --- Compute modification times for cache busting ---
db_mtime = os.path.getmtime(DB_PATH)
msg_mtime = os.path.getmtime(MSG_PATH)
dash_mtime = os.path.getmtime(DASHBOARD_PATH)

# --- Load data and compute summary---
df, message = load_data(DB_PATH, MSG_PATH, db_mtime, msg_mtime, dash_mtime)
summary = compute_stats(df)


# --- Last updated display ---
last_updated_ts = max(db_mtime, msg_mtime, dash_mtime)
last_updated = datetime.fromtimestamp(last_updated_ts).strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"<p style='text-align:right; font-size:80%; color:gray;'>Last updated: {last_updated}</p>", unsafe_allow_html=True)

st.title("📊 Visa Decisions Dashboard")

logo_url = 'https://raw.githubusercontent.com/trevorh7000/visa-dashboard/master/visa-dashboard-web/BISA-Logo-250.png'
st.markdown(f'<div style="text-align:center;"><img src="{logo_url}" class="centered"></div>', unsafe_allow_html=True)

# Centered text with hyperlink
_, cent_co, _ = st.columns(3)
with cent_co:
    st.markdown("""
    <div style="text-align: center; margin-top: 10px;">
        Compiled by <a href="https://businessirelandsouthafrica.co.za/" target="_blank">Business Ireland South Africa</a>
    </div>
    """, unsafe_allow_html=True)

if df.empty:
    st.warning("No data found in database.")
else:
    st.subheader("🔎 Look Up Application Number")
    app_num = st.text_input("Enter Application Number (case insensitive):")
    if app_num:
        results = df[df["application_number"].str.lower() == app_num.strip().lower()]
        if not results.empty:
            st.success(f"Found {len(results)} result(s):")
            st.table(results)
        else:
            st.error("No matching application number found.")
    else:
        summary_for_table = summary.sort_values("week_start_date", ascending=False).reset_index(drop=True)

        with st.expander("📋 Show Weekly Summary Table", expanded=True):
            st.dataframe(summary_for_table.drop(columns=["week_start_date"]), height=200)

        fig = show_chart(summary)

        # Downloads

        # Chart download (in the same container as above)

        # Chart download
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=200)
        buf.seek(0)
        st.download_button("⬇️ Download Chart as PNG", buf, "weekly_chart.png", "image/png")

        # CSV downloads
        csv_summary = summary.drop(columns=["week_start_date"]).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Weekly Summary (CSV)", csv_summary, "visa_summary.csv", "text/csv")

        csv_full = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Full Application Data (CSV)", csv_full, "visa_decisions_full.csv", "text/csv")

st.write("Data sourced from: https://www.irishimmigration.ie/south-africa-visa-desk/#tourist")
st.write("Dash board created by T Cubed - tghughes@gmail.com")

# Message box
if message:
    st.markdown("Status Message")
    st.markdown(f"""
    <div style="
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 10px;
        background-color: #f9f9f9;
        font-family: monospace;
        font-size: 50%;
        white-space: pre-wrap;
        line-height: 1.4;
    ">
{message}
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No update message found yet.")
