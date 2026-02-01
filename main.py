import smtplib
import os
import yfinance as yf
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# --- CONFIGURATION ---
SENDER_EMAIL = os.environ.get('MY_EMAIL')
SENDER_PASSWORD = os.environ.get('MY_PASSWORD')
RECIPIENT_EMAIL = os.environ.get('MY_RECIPIENT')

# Mapping Tickers to Names
# I have pre-filled the names for the tickers you provided.
TICKERS = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp", "AMZN": "Amazon.com", "NVDA": "NVIDIA Corp",
    "GOOGL": "Alphabet Inc. (A)", "GOOG": "Alphabet Inc. (C)", "META": "Meta Platforms", "TSLA": "Tesla Inc.",
    "AVGO": "Broadcom Inc.", "PEP": "PepsiCo", "COST": "Costco Wholesale", "CSCO": "Cisco Systems",
    "TMUS": "T-Mobile US", "CMCSA": "Comcast Corp", "TXN": "Texas Instruments", "ADBE": "Adobe Inc.",
    "QCOM": "Qualcomm Inc.", "AMD": "Advanced Micro Devices", "NFLX": "Netflix Inc.", "INTC": "Intel Corp",
    "HON": "Honeywell Intl", "AMGN": "Amgen Inc.", "INTU": "Intuit Inc.", "SBUX": "Starbucks Corp",
    "GILD": "Gilead Sciences", "MDLZ": "Mondelez Intl", "BKNG": "Booking Holdings", "ADI": "Analog Devices",
    "ISRG": "Intuitive Surgical", "ADP": "ADP", "REGN": "Regeneron Pharm", "PYPL": "PayPal Holdings",
    "VRTX": "Vertex Pharm", "FISV": "Fiserv Inc.", "LRCX": "Lam Research", "MELI": "MercadoLibre",
    "MNST": "Monster Beverage", "PANW": "Palo Alto Networks", "ORLY": "O'Reilly Automotive", "KLAC": "KLA Corp",
    "SNPS": "Synopsys Inc.", "CDNS": "Cadence Design", "CHTR": "Charter Comm", "MAR": "Marriott Intl",
    "CSX": "CSX Corp", "ABNB": "Airbnb Inc.", "NXPI": "NXP Semiconductors", "ASML": "ASML Holding",
    "LULU": "Lululemon Athletica", "AEP": "American Electric Power", "KDP": "Keurig Dr Pepper",
    "ADSK": "Autodesk Inc.", "CTAS": "Cintas Corp", "KHC": "Kraft Heinz", "DXCM": "DexCom Inc.",
    "BIIB": "Biogen Inc.", "EXC": "Exelon Corp", "PAYX": "Paychex Inc.", "IDXX": "IDEXX Labs",
    "MCHP": "Microchip Tech", "MRVL": "Marvell Tech", "EA": "Electronic Arts", "XEL": "Xcel Energy",
    "WDAY": "Workday Inc.", "PCAR": "PACCAR Inc", "ROST": "Ross Stores", "CTSH": "Cognizant Tech",
    "ILMN": "Illumina Inc.", "ODFL": "Old Dominion Freight", "FAST": "Fastenal Co", "CPRT": "Copart Inc.",
    "DLTR": "Dollar Tree", "BKR": "Baker Hughes", "GFS": "GlobalFoundries", "WBD": "Warner Bros. Discovery",
    "CSGP": "CoStar Group", "SIRI": "Sirius XM", "VRSK": "Verisk Analytics", "ALGN": "Align Tech",
    "EBAY": "eBay Inc.", "FANG": "Diamondback Energy", "ENPH": "Enphase Energy", "TEAM": "Atlassian Corp",
    "ZM": "Zoom Video", "ZS": "Zscaler Inc.", "CRWD": "CrowdStrike", "DDOG": "Datadog Inc.", "SWKS": "Skyworks Solutions"
}

def get_stock_data(ticker_map):
    """
    Downloads history for all tickers.
    We pass the list of keys (symbols) to yfinance.
    """
    print("Fetching stock data...")
    symbols = list(ticker_map.keys())
    # 'auto_adjust=True' ensures we get the split/dividend adjusted price.
    data = yf.download(symbols, period="3mo", auto_adjust=True, progress=False)['Close']
    return data

def calculate_top_performers(data, days_lookback):
    """
    Calculates % increase over the lookback period and returns the top 10.
    """
    if len(data) < days_lookback:
        return pd.DataFrame() 

    current_price = data.iloc[-1]
    past_price = data.iloc[-days_lookback]
    
    # Calculate percentage change
    pct_change = ((current_price - past_price) / past_price) * 100
    
    # Create DataFrame
    df = pct_change.to_frame(name='% Increase')
    df.index.name = 'Name of Stock'
    
    # Drop NaNs
    df = df.dropna()
    
    # Sort descending
    df = df.sort_values(by='% Increase', ascending=False)
    
    # Take top 10
    top_10 = df.head(10).reset_index()

    # --- THIS IS THE FIX ---
    # Replace the Ticker Symbol with the Full Name from our Dictionary
    # If a name isn't found (e.g. you added a new stock), it falls back to the ticker
    top_10['Name of Stock'] = top_10['Name of Stock'].map(TICKERS).fillna(top_10['Name of Stock'])
    
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
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
