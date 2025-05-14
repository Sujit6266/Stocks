import streamlit as st
import pandas as pd 
import numpy as np
import yfinance as yf 
import plotly.express as px
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews
import matplotlib.pyplot as plt

# Streamlit app title
st.title('Welcome to the world of Finance🪙')
st.divider()

# Display metrics
col1, col2, col3 = st.columns(3)
col1.metric("Dow Jones", "38293", "0.055%")
col2.metric("S&P 500", "4973", "-0.09%")
col3.metric("Nasdaq Composite", "15761", "0.6%")
st.divider()

# Sidebar input for stock and date range
with st.sidebar:
    ticker = st.text_input('💹 Stock name', 'AAPL')  # Default to 'AAPL' for testing
    start_date = st.date_input('🗓️ Start date', pd.to_datetime('2020-01-01'))
    end_date = st.date_input('🗓️ End date', pd.to_datetime('2021-01-01'))

# Download stock data
data = yf.download(ticker, start=start_date, end=end_date)
# Fix multi-index column names if needed
if isinstance(data.columns, pd.MultiIndex):
    data.columns = [' '.join(col).strip() for col in data.columns]

# Display the line chart for the adjusted close price
close_col = [col for col in data.columns if 'Close' in col and 'Adj' not in col]
if close_col:
    close_col = close_col[0]
    fig = px.line(data, x=data.index, y=close_col, title=f"{ticker} Closing Price")
    st.plotly_chart(fig)
else:
    st.error("No 'Close' column found in the data.")

# Safely identify the 'Volume' column
volume_col = [col for col in data.columns if 'Volume' in col and 'Adj' not in col]

if volume_col:
    volume_col = volume_col[0]
    fig1 = px.bar(data, x=data.index, y=volume_col, title=f"{ticker} Trading Volume",color_discrete_sequence=["red"])
    st.plotly_chart(fig1)
else:
    st.error("No 'Volume' column found in the data.")

# Tabs for pricing data, fundamental data, news, and technical indicators
pricing_data, fundamental_data, news = st.tabs(['Pricing data', 'Fundamental data', 'Top 5 news'])

# Pricing Data Tab
with pricing_data:
    st.subheader('Price Movements')
    data2 = data.copy()

    close_col = [col for col in data.columns if 'Close' in col and 'Adj' not in col]
    if close_col:
        close_series = data[close_col[0]]
        data2['% change'] = close_series / close_series.shift(1) - 1
        data2.dropna(inplace=True)
        st.write(data2)

        annual_return = data2['% change'].mean() * 252 * 100
        st.write(f'Annual Return: {annual_return:.2f}%')

        st_dev = np.std(data2['% change']) * np.sqrt(252)
        st.write(f'Standard Deviation: {st_dev*100:.2f}%')
    else:
        st.error("'Close' column not found in the data.")


# Fundamental Data Tab
with fundamental_data:
    st.subheader('Fundamentals')
    key = 'NJ0SNR7OVF82O3PQ'
    fd = FundamentalData(key, output_format='pandas')

    st.subheader('Balance Sheet')
    try:
        balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
        bs = balance_sheet.T[2:]
        bs.columns = list(balance_sheet.T.iloc[0])
        st.write(bs)
    except Exception as e:
        st.error(f"Balance Sheet data unavailable: {e}")

    st.subheader('Cash Flow')
    try:
        cash_flow = fd.get_cash_flow_annual(ticker)[0]
        cf = cash_flow.T[2:]
        cf.columns = list(cash_flow.T.iloc[0])
        st.write(cf)
        st.bar_chart(cf)
    except Exception as e:
        st.error(f"Cash Flow data unavailable: {e}")

    st.subheader('Cash Flow Chart')
    try:
        cash_flow_data = yf.Ticker(ticker).cashflow
        if not cash_flow_data.empty:
            selected_vars = st.multiselect('Select Cash Flow Variables', cash_flow_data.columns)
            if selected_vars:
                plt.figure(figsize=(10, 6))
                cash_flow_data[selected_vars].plot(kind='bar', ax=plt.gca())
                plt.title(f'Cash Flow Statement for {ticker}')
                plt.xlabel('Year')
                plt.ylabel('Amount')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot()
            else:
                st.info("Please select at least one variable.")
        else:
            st.warning("Cash flow data not available for this ticker.")
    except Exception as e:
        st.error(f"Error generating cash flow chart: {e}")

# News Tab
with news:
    st.header(f'News of {ticker}')
    try:
        sn = StockNews(ticker, save_news=False)
        df_news = sn.read_rss()
        if df_news.empty:
            st.warning("No news found.")
        else:
            for i in range(min(5, len(df_news))):
                st.subheader(f'News {i+1}')
                st.write(df_news['published'][i])
                st.write(df_news['title'][i])
                st.write(df_news['summary'][i])
                st.write(f"Title Sentiment: {df_news['sentiment_title'][i]}")
                st.write(f"News Sentiment: {df_news['sentiment_summary'][i]}")
    except Exception as e:
        st.error(f"Error fetching news: {e}")

