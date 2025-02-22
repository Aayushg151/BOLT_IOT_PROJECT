#Some Symbols for testing
# Indian Stocks (NSE):
# TCS.NS, RELIANCE.NS, HDFCBANK.NS, INFY.NS, WIPRO.NS, TATAMOTORS.NS, HINDUNILVR.NS, ICICIBANK.NS, BHARTIARTL.NS, ADANIENT.NS
# US Stocks:
# AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX, KO, MCD

from boltiotai import openai
import os
import yfinance as yf
import requests_cache
import requests
from bs4 import BeautifulSoup
import time

# Set API Key
openai.api_key = "x55QExGmhWwvSx7Sh72HovSG92d7E_3uTmCGS7y2VkU"

# Get Stock Symbol
STOCK_SYMBOL = input("Enter Stock Symbol:\n")

# Function to fetch stock data
def get_stock_data(symbol):
    session = requests_cache.CachedSession('yfinance_cache', expire_after=1800)
    stock = yf.Ticker(symbol)
    df = stock.history(period="1mo", interval="1d")
    return df

# Fetch financial news
def fetch_news(symbol):
    url = f"https://www.google.com/search?q={symbol}+stock+news&tbm=nws"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return ["Failed to fetch news"]
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("a.WlydOe")
    
    news_list = []
    for article in articles[:5]:
        title = article.get_text()
        link = article["href"]
        news_list.append(f"- {title} ({link})")
    
    return "\n".join(news_list)

# Market Trend Analysis
def get_market_trend(symbol):
    try:
        data = yf.download(symbol, period="2y", interval="1wk")
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
def get_quarterly_report(symbol):
    stock = yf.Ticker(symbol)
    report = stock.quarterly_financials
    
    key_metrics = ["Total Revenue", "Net Income", "Diluted EPS", "Operating Income", "Gross Profit"]
    return {metric: report.loc[metric].iloc[0] if metric in report.index else "N/A" for metric in key_metrics}

# Peer Comparison
def get_peer_comparison(symbol):
    stock = yf.Ticker(symbol)
    peers = stock.info.get("sector")  # Fetch sector to get similar stocks

    if not peers:
        return "No peer data available"

    similar_stocks = [peer for peer in peers if isinstance(peer, str)]  # Ensure valid symbols

    peer_data = {}
    for peer in similar_stocks[:2]:  # Limit to 2 peers
        peer_data[peer] = get_quarterly_report(peer)

    return peer_data


# Generate Stock Review
def generate_stock_review(symbol, stock_data, trend, report, peer_comparison, news):
    prompt = f"""
    Analyze the following stock data for {symbol} and provide an investment recommendation:
    
    Stock Data (Last 6 Months):
    {stock_data.tail(6)}
    
    Market Trend:
    {trend}
    
    Quarterly Report:
    {report}
    
    Peer Comparison:
    {peer_comparison}
    
    News Headlines:
    {news}
    
    Provide a conclusion for your analysis. Should I buy, sell or hold the stock{symbol} 
    """
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response['choices'][0]['message']['content']

# Main Execution
if __name__ == "__main__":
    stock_data = get_stock_data(STOCK_SYMBOL)
    news = fetch_news(STOCK_SYMBOL)
    trend = get_market_trend(STOCK_SYMBOL)
    report = get_quarterly_report(STOCK_SYMBOL)
    peer_comparison = get_peer_comparison(STOCK_SYMBOL)
    
    review = generate_stock_review(STOCK_SYMBOL, stock_data, trend, report, peer_comparison, news)
    
    print("\nStock Review & Recommendation:\n")
    print(review)
