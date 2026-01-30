

import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import re
from datetime import datetime  # CHANGED / NEW: ensure datetime imported
import os
import streamlit.components.v1 as components
import io
import sys

# --- Paths ---
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "decisions.db")
MSG_PATH = os.path.join(BASE_DIR, "message.txt")
DASHBOARD_PATH = os.path.join(BASE_DIR, "dashboard.py")



# --- Load data ---
def load_data(db_path, msg_path, db_mtime, msg_mtime, dash_mtime):
    conn = sqlite3.connect(db_path) # cache buster added Tuesday Jan 27 as i pull out my hair
    df = pd.read_sql_query("SELECT app_number, decision, week, start_date, end_date FROM decisions", conn)  # CHANGED / NEW: include start_date
    conn.close()
    df = df.rename(columns={"app_number": "application_number"})
    df["end_date"] = pd.to_datetime(df["end_date"])
    df["start_date"] = pd.to_datetime(df["start_date"])  # CHANGED / NEW: convert start_date to datetime
    df = df.sort_values(by="end_date")  # end_date is used for ordering

    with open(msg_path, "r") as f:
        msg = f.read().strip()

    return df, msg


# --- Helper functions ---
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
    summary["end_date"] = df.groupby("week")["end_date"].first().values  # CHANGED / NEW: get end_date for each week
    summary["start_date"] = df.groupby("week")["start_date"].first().values  # CHANGED / NEW: include start_date if needed
    summary = summary.sort_values("end_date").reset_index(drop=True)  # CHANGED / NEW: sort by end_date
    return summary


# --- Advanced stats ---
def advanced_stats(summary):
    adv = summary.copy()
    adv["Total_3wk_MA"] = adv["Total"].rolling(3, min_periods=1).mean()  # CHANGED / NEW: 3-week moving average
    adv["Total_pct_change"] = adv["Total"].pct_change().fillna(0) * 100  # CHANGED / NEW: week-to-week % change
    return adv


# --- Chart function ---
def show_chart(summary, window=8):
    weeks = summary["week"]
    approved = summary.get("Approved", pd.Series([0] * len(weeks)))
    refused = summary.get("Refused", pd.Series([0] * len(weeks)))
    total = summary["Total"]

    # --- NEW: week-to-week % change
    total_pct_change = total.pct_change().fillna(0) * 100

    refused_pct = summary["Refused %"]
    approved_pct = 100 - refused_pct

    # --- FIXED Y-AXIS SCALE (global max across all weeks) ---
    global_max_total = summary["Total"].max()
    y_max = int(global_max_total * 1.1)  # 10% headroom


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

    # --- Plot bars
    fig, ax = plt.subplots(figsize=(12, 6))
    bar1 = ax.bar(weeks[start:end], approved[start:end], label="Approved", color="green")
    bar2 = ax.bar(
        weeks[start:end], refused[start:end],
        label="Refused", color="red", bottom=approved[start:end]
    )

    # --- Add annotations with combined total and percentage change ---
    for i, (tot, pc_change) in enumerate(zip(total[start:end], total_pct_change[start:end])):
        ax.annotate(
            f"{int(tot)} ({pc_change:+.1f}%)",
            xy=(i, tot),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="black"
        )

    # --- Add approved/refused inside bars ---
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


    # --- APPLY FIXED Y SCALE ---
    ax.set_ylim(0, y_max)

    ax.set_title("Visa Decisions per Week")
    ax.set_ylabel("Number of Applications")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, axis="y")
    ax.legend()
    fig.tight_layout()



    return fig




# === MAIN APP ===
def main():
    """Set up Streamlit page configuration and styles and all the output."""
    
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

    db_mtime = os.path.getmtime(DB_PATH)
    msg_mtime = os.path.getmtime(MSG_PATH)
    dash_mtime = os.path.getmtime(DASHBOARD_PATH)

    df, message = load_data(DB_PATH, MSG_PATH, db_mtime, msg_mtime, dash_mtime)
    summary = compute_stats(df)
    adv_summary = advanced_stats(summary)  # CHANGED / NEW

    # Last updated display
    last_updated_ts = max(db_mtime, msg_mtime, dash_mtime)
    last_updated = datetime.fromtimestamp(last_updated_ts).strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"<p style='text-align:right; font-size:80%; color:gray;'>Last updated: {last_updated}</p>", unsafe_allow_html=True)

    st.title("📊 Visa Decisions Dashboard")

    logo_url = 'https://raw.githubusercontent.com/trevorh7000/visa-dashboard/master/visa-dashboard-web/BISA-Logo-250.png'
    st.markdown(f'<div style="text-align:center;"><img src="{logo_url}" class="centered"></div>', unsafe_allow_html=True)

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
            # --- Weekly summary table reversed & header fixed
            summary_for_table = summary.iloc[::-1].reset_index(drop=True)
            st.subheader("📋 Weekly Summary Table")
            st.dataframe(summary_for_table, height=200)

            # --- Advanced stats table reversed & header fixed
            adv_summary_for_table = adv_summary.iloc[::-1].reset_index(drop=True)
            st.subheader("📈 Advanced Stats")
            st.dataframe(
                adv_summary_for_table[["week", "Total", "Total_3wk_MA", "Total_pct_change"]],
                height=150
            )

            # --- Show chart with moving average & % change
            fig = show_chart(summary)
                # now i removed the streamlit logic from show_chart I should rename it to generate_chart or similar
            st.pyplot(fig)

            # Button styling
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

            # above can be moved to a fucntion i think
            ########################################
            # put new debuggin st.writes here if needed
            ########################################
            # st.write(df)  # Example debug line
            # st.write(summary)
            # st.write(adv_summary)
            # st.write("this is fig printed  ido not know what fig is:")
            # st.write("fig object type:", type(fig))
            # st.write(fig)
            ########################################

            # --- Downloads ---
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=200)
            buf.seek(0)
            st.download_button("⬇️ Download Chart as PNG", buf, "weekly_chart.png", "image/png")

            # CSV with moving average and % change
            summary_for_csv = summary.copy()
            summary_for_csv["Total_3wk_MA"] = adv_summary["Total_3wk_MA"]
            summary_for_csv["Total_pct_change"] = adv_summary["Total_pct_change"]
            csv_summary = summary_for_csv.to_csv(index=False).encode("utf-8")
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

def run_cli():
    db_mtime = os.path.getmtime(DB_PATH)
    msg_mtime = os.path.getmtime(MSG_PATH)
    dash_mtime = os.path.getmtime(DASHBOARD_PATH)

    df, message = load_data(DB_PATH, MSG_PATH, db_mtime, msg_mtime, dash_mtime)
    summary = compute_stats(df)
    fig = show_chart(summary)

    print(summary)
    fig.savefig(f"weekly_summary_{datetime.now().strftime('%Y-%m-%d')}.png")


if __name__ == "__main__":
    if "-c" in sys.argv:
        run_cli()
    else:
        main()
