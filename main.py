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

# Mapping Benchmark Tickers to Names
BENCHMARK_TICKERS = {
    "LYMS.DE": "Amundi Core Nasdaq-100 Swap UCITS ETF",
    "QDVE.DE": "iShares S&P 500 Info Tech Sector UCITS ETF"
    "AUM5.DE": "Amundi S&P 500 Swap UCITS ETF"
}

# Mapping Tickers to Names
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
    Downloads history for all tickers in ticker_map.
    """
    print("Fetching stock data...")
    symbols = list(ticker_map.keys())
    data = yf.download(symbols, period="6mo", auto_adjust=True, progress=False)['Close']
    return data

def calculate_benchmark_performance(benchmark_data, periods, benchmark_map):
    """
    Generates a comparison table for benchmark ETFs with columns for each lookback period.
    """
    rows = []
    for ticker, name in benchmark_map.items():
        if ticker not in benchmark_data.columns:
            continue
            
        series = benchmark_data[ticker].dropna()
        row = {"Benchmark": name, "Ticker": ticker}
        
        for days, col_name in periods:
            if len(series) >= days:
                current_price = series.iloc[-1]
                past_price = series.iloc[-days]
                pct_change = ((current_price - past_price) / past_price) * 100
                row[col_name] = f"{pct_change:,.2f}%"
            else:
                row[col_name] = "N/A"
        rows.append(row)

    return pd.DataFrame(rows)

def calculate_performance(data, days_lookback, is_top=True):
    """
    Calculates % change over the lookback period. 
    If is_top is True, returns top 10 increases.
    If is_top is False, returns top 10 decliners.
    """
    if len(data) < days_lookback:
        return pd.DataFrame() 

    current_price = data.iloc[-1]
    past_price = data.iloc[-days_lookback]
    
    pct_change = ((current_price - past_price) / past_price) * 100
    
    df = pct_change.to_frame(name='% Change')
    df.index.name = 'Name of Stock'
    df = df.dropna()
    df = df.sort_values(by='% Change', ascending=not is_top)
    
    top_10 = df.head(10).reset_index()
    top_10['Name of Stock'] = top_10['Name of Stock'].map(TICKERS).fillna(top_10['Name of Stock'])
    top_10.insert(0, 'Rank', range(1, 11))
    top_10['% Change'] = top_10['% Change'].map('{:,.2f}%'.format)
    
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
    msg['Subject'] = f"Weekly Nasdaq & Benchmark Performance Report - {datetime.now().strftime('%Y-%m-%d')}"

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
        # Define trading day horizons: 5 days, ~30 days (21 trading), ~90 days (63 trading)
        benchmark_horizons = [
            (5, "5 Trading Days"),
            (21, "~30 Calendar Days"),
            (63, "~90 Calendar Days")
        ]

        # 1. Fetch & Build Benchmark Table
        benchmark_data = get_stock_data(BENCHMARK_TICKERS)
        benchmark_df = calculate_benchmark_performance(benchmark_data, benchmark_horizons, BENCHMARK_TICKERS)

        # 2. Fetch Stock Data
        data = get_stock_data(TICKERS)
        
        performers_periods = [
            (5, "Table 1: Top 10 Performing Stocks (Past 5 Trading Days)"),
            (21, "Table 2: Top 10 Performing Stocks (Past ~30 Calendar Days)"),
            (63, "Table 3: Top 10 Performing Stocks (Past ~90 Calendar Days)")
        ]
        
        decliners_periods = [
            (5, "Table 4: Top 10 Declining Stocks (Past 5 Trading Days)"),
            (21, "Table 5: Top 10 Declining Stocks (Past ~30 Calendar Days)"),
            (63, "Table 6: Top 10 Declining Stocks (Past ~90 Calendar Days)")
        ]
        
        email_body = "<h2>Weekly Nasdaq & Benchmark Performance Report</h2>"
        
        # Benchmark Table at Top
        email_body += dataframe_to_html(benchmark_df, "Benchmark ETF Overview")
        email_body += "<br><hr><br>"

        # Top Performers Tables
        for days, title in performers_periods:
            top_stocks = calculate_performance(data, days, is_top=True)
            email_body += dataframe_to_html(top_stocks, title)
            email_body += "<br><hr><br>"

        # Top Decliners Tables
        for days, title in decliners_periods:
            declining_stocks = calculate_performance(data, days, is_top=False)
            email_body += dataframe_to_html(declining_stocks, title)
            email_body += "<br><hr><br>"

        send_email(email_body)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
