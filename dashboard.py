import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

# Your Google Tag Manager or Analytics snippet as a raw HTML string:

GA_JS = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-8ZMY8YCKVH"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-8ZMY8YCKVH');
</script>
"""
components.html(GA_JS)

DB_PATH = "decisions.db"

st.set_page_config(page_title="Visa Decisions Dashboard", layout="wide")

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT app_number, decision, week FROM decisions", conn)
    conn.close()
    df = df.rename(columns={"app_number": "application_number"})
    return df

def parse_week_start(week_label):
    match = re.match(r"(\d{1,2}-[A-Za-z]+)-to-", week_label)
    if not match:
        return None
    start_str = match.group(1) + "-" + week_label[-4:]
    try:
        return datetime.strptime(start_str, "%d-%B-%Y")
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

df = load_data()
if df.empty:
    st.warning("No data found in database.")
else:
    summary = compute_stats(df)

    # --- Charts and Table ---
    with st.expander("📋 Show Weekly Summary Table", expanded=True):
        st.dataframe(summary.drop(columns=["week_start_date"]))

    show_chart(summary)

    # --- Downloads ---
    st.subheader("📥 Download Data")
    csv_summary = summary.drop(columns=["week_start_date"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Weekly Summary (CSV)", csv_summary, "visa_summary.csv", "text/csv")

    csv_full = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Full Application Data (CSV)", csv_full, "visa_decisions_full.csv", "text/csv")

    # --- Lookup ---
    st.subheader("🔎 Look Up Application Number")
    app_num = st.text_input("Enter Application Number (case insensitive):")
    if app_num:
        results = df[df["application_number"].str.lower() == app_num.strip().lower()]
        if not results.empty:
            st.success(f"Found {len(results)} result(s):")
            st.table(results)
        else:
            st.error("No matching application number found.")
