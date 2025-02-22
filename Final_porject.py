from boltiotai import openai
import os
import yfinance as yf
import requests_cache
import requests
from bs4 import BeautifulSoup
import time

#Some Symbols for testing
# Indian Stocks (NSE):
# TCS.NS, RELIANCE.NS, HDFCBANK.NS, INFY.NS, WIPRO.NS, TATAMOTORS.NS, HINDUNILVR.NS, ICICIBANK.NS, BHARTIARTL.NS, ADANIENT.NS
# US Stocks:
# AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX, KO, MCD


# Set API Key
openai.api_key ="x55QExGmhWwvSx7Sh72HovSG92d7E_3uTmCGS7y2VkU"

# Get Stock Symbol
STOCK_SYMBOL = input("Enter Stock Symbol:\n")

# Function to fetch stock data
def get_stock_data(symbol):
    # Create a cached session to reduce API requests
    session = requests_cache.CachedSession('yfinance_cache', expire_after=1800)  # Cache for 30 minutes
    stock = yf.Ticker(symbol, session=session)
    
    # Fetch stock history
    df = stock.history(period="1mo", interval="1d")
    return df

# Fetch financial news using requests (instead of Selenium)
def fetch_news(STOCK_SYMBOL):
    url = f"https://www.google.com/search?q={STOCK_SYMBOL}+stock+news&tbm=nws"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return ["Failed to fetch news"]
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("a.WlydOe")  # Updated Google News XPath

    news_list = []
    for article in articles[:5]:  # Limit to 5 articles
        title = article.get_text()
        link = article["href"]
        news_list.append({"title": title, "link": link})

    return news_list

# Market Trend Function (Fixed SMA Calculation)
def market_trend(STOCK_SYMBOL):
    try:
        data = yf.download(STOCK_SYMBOL, period="2y", interval="1wk")
        if data.empty:
            return "No data available"

        data["SMA50"] = data["Close"].rolling(window=20).mean()
        data["SMA200"] = data["Close"].rolling(window=50).mean()

        latest_data = data.iloc[-1]
        trend = "Uptrend 📈" if latest_data["SMA50"] > latest_data["SMA200"] else "Downtrend 📉"
        return f"Current Trend: {trend}"
    
    except Exception as e:
        return f"Error: {e}"

# Fetch Quarterly Report
def get_quarterly_report(STOCK_SYMBOL):
    stock = yf.Ticker(STOCK_SYMBOL)
    report = stock.quarterly_financials

    key_metrics = ["Total Revenue", "Net Income", "Diluted EPS", "Operating Income", "Gross Profit"]
    return {metric: report.loc[metric].iloc[0] if metric in report.index else "N/A" for metric in key_metrics}

# Fetch Peer Comparison
def compare_peers_with_main(STOCK_SYMBOL):
    stock = yf.Ticker(STOCK_SYMBOL)
    sector = stock.info.get("sector", "Unknown")

    # Get first 2 peer stocks from Yahoo Finance
    peers = stock.info.get("industryKey", [])[:2]
    
    peer_data = {}
    for peer in peers:
        peer_data[peer] = get_quarterly_report(peer)
    
    return peer_data

# Generate Stock Review using OpenAI
def generate_stock_review(STOCK_SYMBOL, stock_data, trend, report, peer_comparison, news):
    prompt = f"""
    Analyze the following stock data for {STOCK_SYMBOL} and provide an investment recommendation:

    **Stock Data (Last 6 Months)**:
    {stock_data.tail(6)}

    **Market Trend**:
    {trend}

    **Quarterly Report**:
    {report}

    **Peer Comparison**:
    {peer_comparison}

    **News Headlines**:
    {news}

    Provide a conclusion: **BUY, SELL, or HOLD**, with justification.
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a financial analyst."
            },
            {"role": "user", "content": prompt
            }
        ]
    )

    return response['choices'][0]['message']['content']

# Main Execution
if __name__ == "__main__":
    stock_data = get_stock_data(STOCK_SYMBOL)
    news = fetch_news(STOCK_SYMBOL)
    trend = market_trend(STOCK_SYMBOL)
    report = get_quarterly_report(STOCK_SYMBOL)
    peer_comparison = compare_peers_with_main(STOCK_SYMBOL)
    
    review = generate_stock_review(STOCK_SYMBOL, stock_data, trend, report, peer_comparison, news)
    
    print("\nStock Review & Recommendation:\n")
    print(review)
