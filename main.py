import os
import smtplib
import sys # Added to force crashes
import yfinance as yf
from dotenv import load_dotenv 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Attempt to load .env (harmless if it doesn't exist on GitHub)
load_dotenv()

def get_market_data():
    """Fetches the latest available price for S&P 500 and Nasdaq 100."""
    tickers = { "Nasdaq 100": "^NDX", "S&P 500": "^GSPC" }
    data = {}
    print("--- DEBUG: Fetching market data... ---")
    
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                latest_price = hist['Close'].iloc[-1]
                data[name] = latest_price
            else:
                data[name] = "N/A (Market Closed?)"
        except Exception as e:
            print(f"--- ERROR fetching {name}: {e} ---")
            data[name] = "Error"
            
    return data

def send_email(market_data):
    # 1. READ SECRETS
    sender_email = os.environ.get('MY_EMAIL')
    sender_password = os.environ.get('MY_PASSWORD')
    recipient_email = os.environ.get('MY_RECIPIENT')

    # 2. DEBUG SECRETS (Check if they exist without revealing them)
    print(f"--- DEBUG: MY_EMAIL is set? {'YES' if sender_email else 'NO'} ---")
    print(f"--- DEBUG: MY_PASSWORD is set? {'YES' if sender_password else 'NO'} ---")
    print(f"--- DEBUG: MY_RECIPIENT is set? {'YES' if recipient_email else 'NO'} ---")

    # 3. CRASH IF MISSING
    if not all([sender_email, sender_password, recipient_email]):
        print("--- FATAL ERROR: One or more Secrets are missing! Check your YAML file. ---")
        sys.exit(1) # This turns the GitHub Action RED

    # 4. PREPARE EMAIL
    subject = f"Market Update: {datetime.now().strftime('%Y-%m-%d')}"
    body_lines = ["Here are the latest market indices:\n"]
    for index, price in market_data.items():
        val = f"{price:,.2f}" if isinstance(price, float) else str(price)
        body_lines.append(f"{index}: {val}")
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText("\n".join(body_lines), 'plain'))

    # 5. SEND EMAIL
    try:
        print("--- DEBUG: Connecting to SMTP server (smtp.gmail.com:587)... ---")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        print(f"--- DEBUG: Logging in as {sender_email}... ---")
        server.login(sender_email, sender_password)
        
        print(f"--- DEBUG: Sending message to {recipient_email}... ---")
        server.send_message(msg)
        server.quit()
        print("--- SUCCESS: Email sent successfully! ---")
        
    except Exception as e:
        print(f"--- FATAL ERROR: SMTP Failed. {e} ---")
        sys.exit(1) # This turns the GitHub Action RED

if __name__ == "__main__":
    prices = get_market_data()
    send_email(prices)
