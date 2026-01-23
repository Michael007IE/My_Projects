import os
import smtplib
import yfinance as yf
from dotenv import load_dotenv 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

load_dotenv()


def get_market_data():
    """Fetches the latest available price for S&P 500 and Nasdaq 100."""
    tickers = {
        "Nasdaq 100": "^NDX",
        "S&P 500": "^GSPC"
    }
    
    data = {}
    print("Fetching market data...")
    
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            # Get the most recent 1 day of data
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                # Get the last available 'Close' price (latest current price)
                latest_price = hist['Close'].iloc[-1]
                data[name] = latest_price
            else:
                data[name] = "N/A"
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            data[name] = "Error"
            
    return data

def send_email(market_data):
    """Sends the email using credentials from environment variables."""
    
    # Retrieve credentials from Environment Variables
    sender_email = os.environ.get('MY_EMAIL')
    sender_password = os.environ.get('MY_PASSWORD')
    recipient_email = os.environ.get('MY_RECIPIENT')

    if not all([sender_email, sender_password, recipient_email]):
        print("Error: Missing environment variables. Please set EMAIL_USER, EMAIL_PASSWORD, and MY_RECIPIENT.")
        return

    # Create Email Content
    subject = f"Market Update: {datetime.now().strftime('%Y-%m-%d')}"
    
    # Formatting the body
    body_lines = ["Here are the latest market indices:\n"]
    for index, price in market_data.items():
        if isinstance(price, float):
            body_lines.append(f"{index}: {price:,.2f}")
        else:
            body_lines.append(f"{index}: {price}")
    
    body = "\n".join(body_lines)

    # Setup MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Send via SMTP (Gmail example)
    try:
        print("Connecting to SMTP server...")
        # Note: Port 587 is for TLS. If using SSL, use port 465.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Upgrade connection to secure
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Email successfully sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    # 1. Get Data
    prices = get_market_data()
    
    # 2. Send Email
    send_email(prices)
