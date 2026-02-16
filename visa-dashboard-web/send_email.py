import smtplib
from email.message import EmailMessage
import io
import os
from dotenv import load_dotenv
from datetime import datetime


BASE_DIR = os.path.dirname(__file__)  # folder where this script lives
os.chdir(BASE_DIR)  # optionally change current working directory

# --- Load local .env if it exists ---
load_dotenv()  # will do nothing if no .env is present

# --- Get credentials from environment ---
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")

if not USERNAME or not PASSWORD:
    raise RuntimeError("USERNAME or PASSWORD environment variable not set!")


def send_figure_email(fig):
    """
    Send a matplotlib figure as an inline image email.
    Both the chart and the BISA logo are embedded inline.
    """

    # --- Save chart figure to a BytesIO buffer ---
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200)
    buf.seek(0)
    chart_bytes = buf.read()

    # --- Load BISA logo from local file ---
    logo_path = "BISA-Logo-250.png"
    if not os.path.exists(logo_path):
        raise RuntimeError(f"Logo file not found: {logo_path}")
    with open(logo_path, "rb") as f:
        logo_bytes = f.read()

    recipients = [
      "tghughes@gmail.com",
      "clairetimeout@gmail.com",
      "Cathal.Digan@dfa.ie",
      "treasurer@businessirelandsa.co.za",
    ]

    # recipients = ["tghughes@gmail.com"]  # for testing, send only to myself

    # --- Build email ---
    msg = EmailMessage()
    msg["From"] = "BISA Visa Report <visa@businessirelandsa.co.za>"
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"BISA Weekly Visa Dashboard Chart – {datetime.now().strftime('%d %b %Y')}"

    # Plain-text fallback
    msg.set_content("Please view this email in an HTML-capable email client.")

    # HTML body with inline images
    msg.add_alternative(
        """
        <html>
          <body style="font-family: Arial, sans-serif; color: #000;">

            <!-- Header / Branding -->
            <div style="margin-bottom: 15px;">
              <img src="cid:bisa_logo"
                   alt="BISA Logo"
                   style="width:200px; height:auto; display:block; margin-bottom:8px;">
              <div style="font-size: 13px;">
                Compiled by
                <a href="https://businessirelandsouthafrica.co.za/"
                   target="_blank"
                   style="color:#0066cc; text-decoration:none;">
                  Business Ireland South Africa
                </a>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                See all the data at the
                <a href="https://visa-dashboard.streamlit.app/"
                   target="_blank"
                   style="color:#0066cc; text-decoration:none;">
                  BISA Visa Dashboard
              </div>
            </div>

            <!-- Chart -->
            <div style="margin: 20px 0;">
              <img src="cid:visa_chart"
                   alt="Weekly Visa Dashboard Chart"
                   style="max-width:100%; width:800px; height:auto;
                          border:1px solid #ddd;">
            </div>

            <!-- Footer / Data source -->
            <div style="margin-top: 20px; font-size: 12px; color: #555;">
              Data sourced from:
              <a href="https://www.irishimmigration.ie/south-africa-visa-desk/#tourist"
                 target="_blank"
                 style="color:#0066cc; text-decoration:none;">
                https://www.irishimmigration.ie/south-africa-visa-desk/#tourist
              </a>
             <p>Dashboard created by T Cubed - <a href="mailto:tghughes@gmail.com">tghughes@gmail.com</a></p>

            </div>

          </body>
        </html>
        """,
        subtype="html"
    )

    # --- Attach images inline ---
    msg.get_payload()[1].add_related(
        chart_bytes,
        maintype="image",
        subtype="png",
        cid="visa_chart"
    )
    msg.get_payload()[1].add_related(
        logo_bytes,
        maintype="image",
        subtype="png",
        cid="bisa_logo"
    )

    # --- Send email via SMTP SSL ---
    smtp_server = "smtp.businessirelandsa.co.za"
    smtp_port = 465

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as s:
        s.login(USERNAME, PASSWORD)
        s.send_message(msg, to_addrs=recipients)

    print("Email sent successfully!")
    buf.close()
    return True


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Example usage
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    send_figure_email(fig)
