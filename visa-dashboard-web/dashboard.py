import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import re
from datetime import datetime
import os

import streamlit.components.v1 as components

# --- Read message.txt ---
message_path = "message.txt"
BASE_DIR = os.path.dirname(__file__)
MSG_PATH = os.path.join(BASE_DIR, "message.txt")


DB_PATH = "decisions.db"

st.set_page_config(page_title="Visa Decisions Dashboard", layout="wide")

st.markdown("""
    <style>
    input {
        background-color: #dcdee0!important;  /* soft but visible orange */
        color: black !important;
        border: 2px solid black !important;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
# cache-bust: 2025-08-12T18:40:08.933244
    import os
    BASE_DIR = os.path.dirname(__file__)
    db_path = os.path.join(BASE_DIR, "decisions.db")
    conn = sqlite3.connect(db_path)

    df = pd.read_sql_query("SELECT app_number, decision, week, end_date FROM decisions", conn)
    conn.close()
    df = df.rename(columns={"app_number": "application_number"})
    # Convert end_date to datetime
    df["end_date"] = pd.to_datetime(df["end_date"])
    df = df.sort_values(by="end_date")  # 👈 sort by end_date in ascending order
    return df

def parse_week_start(week_label):
    match = re.match(r"(\d{1,2} [A-Za-z]+) to (\d{1,2} [A-Za-z]+ \d{4})", week_label)
    if not match:
        return None
    start_str, end_str = match.groups()
    try:
        # Extract the year from the end date and apply it to the start
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

def show_chart(summary):
    weeks = summary["week"]
    approved = summary.get("Approved", pd.Series([0]*len(weeks)))
    refused = summary.get("Refused", pd.Series([0]*len(weeks)))
    total = summary["Total"]
    refused_pct = summary["Refused %"]
    approved_pct = 100 - refused_pct

    fig, ax = plt.subplots(figsize=(12, 6))

    bar1 = ax.bar(weeks, approved, label="Approved", color="green")
    bar2 = ax.bar(weeks, refused, label="Refused", color="red", bottom=approved)

    for rect, pct in zip(bar1, approved_pct):
        height = rect.get_height()
        if height > 0:
            ax.annotate(f'{int(height)} ({pct:.1f}%)',
                        xy=(rect.get_x() + rect.get_width() / 2, height / 2),
                        ha='center', va='center', color='white', fontsize=8, fontweight='bold')

    for rect, base_height, pct in zip(bar2, approved, refused_pct):
        height = rect.get_height()
        if height > 0:
            ax.annotate(f'{int(height)} ({pct:.1f}%)',
                        xy=(rect.get_x() + rect.get_width() / 2, base_height + height / 2),
                        ha='center', va='center', color='white', fontsize=8, fontweight='bold')

    for i, tot in enumerate(total):
        ax.annotate(f'Total: {int(tot)}',
                    xy=(i, tot),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9, fontweight='bold')

    ax.set_title("Visa Decisions per Week")
    ax.set_ylabel("Number of Applications")
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, axis='y')
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)

# === MAIN APP ===

st.title("📊 Visa Decisions Dashboard")

# # add the logo and text
logo_path = os.path.join(os.path.dirname(__file__), "BISA-Logo-250.png")

# image from github so it ca be centred


st.markdown("""
    <style>
        .centered {
            display: block;
            margin-left: auto;
            margin-right: auto;
            text-align: center;
        }
    </style>
    <div class="centered">
        <img src='https://raw.githubusercontent.com/trevorh7000/visa-dashboard/master/visa-dashboard-web/BISA-Logo-250.png'
    </div>
""", unsafe_allow_html=True)

# Centered text with hyperlink
left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.markdown(
    """
    <div style="text-align: center; margin-top: 10px;">
        Compiled by <a href="https://businessirelandsouthafrica.co.za/" target="_blank">Business Ireland South Africa</a>
    </div>
    """,
    unsafe_allow_html=True
    )




# ----------------------------------- new try  ----------------------------------
df = load_data()
if df.empty:
    st.warning("No data found in database.")
else:

    # --- Lookup moved to top ---
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
        # --- Show summary and charts only if no lookup query ---
        summary = compute_stats(df)
        summary_for_table = summary.sort_values("week_start_date", ascending=False).reset_index(drop=True)

        # --- Charts and Table ---
        with st.expander("📋 Show Weekly Summary Table", expanded=True):
            st.dataframe(summary_for_table.drop(columns=["week_start_date"]))

        show_chart(summary)

        # --- Downloads ---
        st.subheader("📥 Download Data")
        csv_summary = summary.drop(columns=["week_start_date"]).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Weekly Summary (CSV)", csv_summary, "visa_summary.csv", "text/csv")

        csv_full = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Full Application Data (CSV)", csv_full, "visa_decisions_full.csv", "text/csv")

st.write("Data sourced from: https://www.irishimmigration.ie/south-africa-visa-desk/#tourist")
st.write("Dash board created by T Cubed - tghughes@gmail.com")

if os.path.exists(MSG_PATH):
    with open(MSG_PATH, "r") as f:
        message = f.read().strip()  # strip removes leading/trailing blank lines

    # --- Display with smaller boxed style ---
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