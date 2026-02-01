import smtplib
import os
import yfinance as yf
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SENDER_EMAIL = os.environ.get('MY_EMAIL')
SENDER_PASSWORD = os.environ.get('MY_PASSWORD')
RECIPIENT_EMAIL = os.environ.get('MY_RECIPIENT')

# REMOVED: ANSS, ATVI (Delisted)
TICKERS = [
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "GOOG", "META", "TSLA", "AVGO", "PEP",
    "COST", "CSCO", "TMUS", "CMCSA", "TXN", "ADBE", "QCOM", "AMD", "NFLX", "INTC",
    "HON", "AMGN", "INTU", "SBUX", "GILD", "MDLZ", "BKNG", "ADI", "ISRG", "ADP",
    "REGN", "PYPL", "VRTX", "FISV", "LRCX", "MELI", "MNST", "PANW", "ORLY",
    "KLAC", "SNPS", "CDNS", "CHTR", "MAR", "CSX", "ABNB", "NXPI", "ASML", "LULU",
    "AEP", "KDP", "ADSK", "CTAS", "KHC", "DXCM", "BIIB", "EXC", "PAYX", "IDXX",
    "MCHP", "MRVL", "EA", "XEL", "WDAY", "PCAR", "ROST", "CTSH", "ILMN", "ODFL",
    "FAST", "CPRT", "DLTR", "BKR", "GFS", "WBD", "CSGP", "SIRI", "VRSK", "ALGN",
    "EBAY", "FANG", "ENPH", "TEAM", "ZM", "ZS", "CRWD", "DDOG", "SWKS"
]

def get_stock_data(tickers):
    """
    Downloads history for all tickers.
    FIX: Added 'auto_adjust=True' and changed 'Adj Close' to 'Close'.
    """
    print("Fetching stock data...")
    # 'auto_adjust=True' ensures we get the split/dividend adjusted price.
    # The column name for this is now 'Close', not 'Adj Close'.
    data = yf.download(tickers, period="3mo", auto_adjust=True, progress=False)['Close']
    return data

def calculate_top_performers(data, days_lookback):
    """
    Calculates % increase over the lookback period and returns the top 10.
    """
    if len(data) < days_lookback:
        return pd.DataFrame() 

    # .iloc[-1] is the most recent day, .iloc[-X] is X days ago
    current_price = data.iloc[-1]
    past_price = data.iloc[-days_lookback]
    
    # Calculate percentage change
    pct_change = ((current_price - past_price) / past_price) * 100
    
    # Create DataFrame
    df = pct_change.to_frame(name='% Increase')
    df.index.name = 'Name of Stock'
    
    # Drop NaNs (tickers that didn't exist back then)
    df = df.dropna()
    
    # Sort descending
    df = df.sort_values(by='% Increase', ascending=False)
    
    # Take top 10
    top_10 = df.head(10).reset_index()
    
    # Add Rank column
    top_10.insert(0, 'Rank', range(1, 11))
    
    # Format to 2 decimal places
    top_10['% Increase'] = top_10['% Increase'].map('{:,.2f}%'.format)
    
    return top_10

def dataframe_to_html(df, title):
    if df.empty:
        return f"<p>Not enough data for {title}</p>"
        
    html = f"<h3>{title}</h3>"
    html += df.to_html(index=False, border=0, justify='left', classes='table')
    return html

def send_email(html_content):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Error: Email credentials not found. Make sure environment variables are set.")
        return

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = f"Weekly Nasdaq Top Performers - {datetime.now().strftime('%Y-%m-%d')}"

    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    try:
        data = get_stock_data(TICKERS)
        
        periods = [
            (5, "Table 1: Top 10 Performing Stocks (Past 5 Trading Days)"),
            (10, "Table 2: Top 10 Performing Stocks (Past 10 Trading Days)"),
            (21, "Table 3: Top 10 Performing Stocks (Past ~30 Calendar Days)"),
            (42, "Table 4: Top 10 Performing Stocks (Past ~60 Calendar Days)")
        ]
        
        email_body = "<h2>Weekly Nasdaq Performance Report</h2>"
        
        for days, title in periods:
            top_stocks = calculate_top_performers(data, days)
            email_body += dataframe_to_html(top_stocks, title)
            email_body += "<br><hr><br>"

        send_email(email_body)
    except Exception as e:
        print(f"An error occurred in main execution: {e}")

if __name__ == "__main__":
    main()
