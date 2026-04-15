import streamlit as st
from openai import OpenAI
import yfinance as yf
import requests
import xml.etree.ElementTree as ET
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def get_stock_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        hist = yf.download(ticker_symbol, period="5d", progress=False)

        price = None
        if not hist.empty:
            price = hist["Close"].iloc[-1].item()

        return {
            "company": info.get("longName"),
            "price": price,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE")
        }

    except Exception:
        return {
            "company": None,
            "price": None,
            "market_cap": None,
            "pe_ratio": None
        }

def get_stock_news(ticker_symbol):
    url = f"https://news.google.com/rss/search?q={ticker_symbol}+stock"
    response = requests.get(url)
    root = ET.fromstring(response.content)

    headlines = []

    for item in root.findall(".//item")[:5]:
        title = item.find("title").text
        headlines.append(title)

    return headlines

def get_price_chart_data(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="1y")
    return hist[["Close"]]

def research_stock(ticker):
    return {
        "ticker": ticker,
        "data": get_stock_data(ticker),
        "news": get_stock_news(ticker)
    }

def analyse_stock(ticker):
    data = research_stock(ticker)

    if "data" not in data or data["data"] is None:
        return "Error: Could not retrieve stock data."

    stock_info = data["data"]

    company = stock_info.get("company", "data not available")
    price = stock_info.get("price", "data not available")
    market_cap = stock_info.get("market_cap", "data not available")
    pe_ratio = stock_info.get("pe_ratio", "data not available")
    news = data.get("news", [])

    prompt = f"""
You are a disciplined stock research assistant.

Rules:
- Only use the data provided
- Do NOT make up financials
- If something is missing, say "data not available"
- Be cautious and realistic (not overly bullish)

Analyse this stock:

Ticker: {ticker}
Company: {company}
Price: {price}
Market Cap: {market_cap}
PE Ratio: {pe_ratio}

Recent News:
{news}

Return your answer in this exact format:

### Score
75

### Positives
- ...

### Risks
- ...

### Summary
...
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text

st.title("Stock Research Agent")

ticker_input = st.text_input("Enter a stock ticker").upper()

if st.button("Analyse") and ticker_input:
    with st.spinner("Analysing stock..."):
        result = analyse_stock(ticker_input)

    st.subheader("Analysis")
    st.markdown(result)

    chart_data = get_price_chart_data(ticker_input)
    st.subheader("1-Year Price Chart")
    st.line_chart(chart_data)