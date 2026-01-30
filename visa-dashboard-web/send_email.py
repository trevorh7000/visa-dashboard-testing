import smtplib
from email.message import EmailMessage
import io
import os
from dotenv import load_dotenv
from datetime import datetime



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
    Server, port, sender, and recipient are hard-coded.
    """

    # --- Save figure to a BytesIO buffer ---
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200)
    buf.seek(0)
    img_bytes = buf.read()

    recipients = ["tghughes@gmail.com", "clairetimeout@gmail.com"]

    # --- Build email ---
    msg = EmailMessage()
    msg["From"] = "BISA Visa Report <visa@businessirelandsa.co.za>"
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"[TEST] -----BISA Weekly Visa Dashboard Chart – {datetime.now().strftime('%d %b %Y')}"

    # Plain-text fallback
    msg.set_content("Please view this email in an HTML-capable email client.")

    # HTML body with inline image
    msg.add_alternative(
    """
    <html>
      <body>
        <p>Here is this week's Visa Dashboard chart:</p>
        <img src="cid:visa_chart"
             style="max-width:100%; width:640px; height:auto;
                    border:1px solid #ddd;">
      </body>
    </html>
    """,
    subtype="html"
)

    # Attach image inline (NOT as a download attachment)
    msg.get_payload()[1].add_related(
        img_bytes,
        maintype="image",
        subtype="png",
        cid="visa_chart"
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
