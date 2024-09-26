import streamlit as st
from app.yahoo_finance_api import get_stock_history, get_stock_data
import plotly.graph_objs as go
import pandas as pd
import talib

# Function to calculate indicators using TA-Lib
def calculate_indicators(data_unprocessed):
    data_unprocessed = pd.DataFrame(data_unprocessed)

    indicators = {
        'adosc': talib.ADOSC(data_unprocessed['High'], data_unprocessed['Low'], data_unprocessed['Close'], data_unprocessed['Volume']),
        'adx': talib.ADX(data_unprocessed['High'], data_unprocessed['Low'], data_unprocessed['Close']),
        'ad': talib.AD(data_unprocessed['High'], data_unprocessed['Low'], data_unprocessed['Close'], data_unprocessed['Volume']),
        'adxr': talib.ADXR(data_unprocessed['High'], data_unprocessed['Low'], data_unprocessed['Close']),
        'apo': talib.APO(data_unprocessed['Close']),
        'aroon_down': talib.AROON(data_unprocessed['High'], data_unprocessed['Low'])[0],
        'aroon_up': talib.AROON(data_unprocessed['High'], data_unprocessed['Low'])[1],
        'aroonosc': talib.AROONOSC(data_unprocessed['High'], data_unprocessed['Low']),
        'atr': talib.ATR(data_unprocessed['High'], data_unprocessed['Low'], data_unprocessed['Close']),
        'avgprice': talib.AVGPRICE(data_unprocessed['Open'], data_unprocessed['High'], data_unprocessed['Low'], data_unprocessed['Close']),
        'bbands_upper': talib.BBANDS(data_unprocessed['Close'])[0],
        'bbands_middle': talib.BBANDS(data_unprocessed['Close'])[1],
        'bbands_lower': talib.BBANDS(data_unprocessed['Close'])[2],
        'bop': talib.BOP(data_unprocessed['Open'], data_unprocessed['High'], data_unprocessed['Low'], data_unprocessed['Close']),
        'cci': talib.CCI(data_unprocessed['High'], data_unprocessed['Low'], data_unprocessed['Close']),
        'cmo': talib.CMO(data_unprocessed['Close']),
        'correl': talib.CORREL(data_unprocessed['High'], data_unprocessed['Low']),
        'dx': talib.DX(data_unprocessed['High'], data_unprocessed['Low'], data_unprocessed['Close']),
        'ema': talib.EMA(data_unprocessed['Close']),
        'sma': talib.SMA(data_unprocessed['Close']),
        'rsi': talib.RSI(data_unprocessed['Close']),
        # Add other indicators as necessary
    }

    indicators_df = pd.DataFrame(indicators)
    indicators_df.fillna(0, inplace=True)

    data_processed = pd.concat([data_unprocessed, indicators_df], axis=1)

    return data_processed


# Function to display stock data in a card format
def display_stock_info(ticker):
    stock = get_stock_data(ticker)
    stock_info = stock.info  # Fetch stock information

    # Get year over year
    hist = stock.history(period="1y")

    # Use .get() to avoid KeyError if key is not found
    close_price = stock_info.get('currentPrice', None)

    # Calculate daily return and get the most recent value
    hist['Daily_Return'] = hist['Close'].pct_change()
    price_diff_percent = hist['Daily_Return'].iloc[-1]  # Get the most recent daily return

    week_high = stock_info.get('fiftyTwoWeekHigh', None)
    week_low = stock_info.get('fiftyTwoWeekLow', None)

    # Convert to float, if not None
    if close_price is not None:
        close_price = float(close_price)
    if price_diff_percent is not None:
        price_diff_percent = float(price_diff_percent) * 100  # Convert to percentage
    else:
        price_diff_percent = 0  # Set a default value if None
    if week_high is not None:
        week_high = float(week_high)
    if week_low is not None:
        week_low = float(week_low)

    st.markdown(f"### Stock Data for {ticker}")

    # Display stock data cards
    col1, col2, col3 = st.columns(3)

    with col1:
        if close_price is not None:
            st.metric(label="Close Price", 
                       value=f"${close_price:.2f}", 
                       delta=f"{price_diff_percent:.2f}%", 
                       delta_color="normal" if price_diff_percent >= 0 else "inverse")
        else:
            st.metric(label="Close Price", value="N/A")

    with col2:
        st.metric(label="52-Week High", value=f"${week_high:.2f}" if week_high is not None else "N/A")

    with col3:
        st.metric(label="52-Week Low", value=f"${week_low:.2f}" if week_low is not None else "N/A")

def plot_stock_chart(data, ticker):
    """Plot stock price chart using Plotly."""
    fig = go.Figure()

    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Market Data'
    ))

    # Automatically add all indicators as traces
    indicator_columns = [col for col in data.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume']]
    for col in indicator_columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data[col],
            mode='lines',
            name=col,
            line=dict(width=1.5),
            visible='legendonly'
        ))

    # Set chart title and labels
    fig.update_layout(
        title=f'{ticker} Stock Price',
        yaxis_title=f'{ticker} Price (USD)',
        xaxis_rangeslider_visible=True,
        legend_itemclick='toggleothers',
        legend_itemdoubleclick=False
    )

    return fig


# Streamlit app layout
st.title("Stock Dashboard")

# Sidebar
ticker = st.sidebar.text_input("Enter stock ticker", value="MSFT", max_chars=5)

# Available time periods for buttons
time_periods = {
    "1d": "1d", 
    "5d": "5d", 
    "1m": "1mo", 
    "3m": "3mo", 
    "6m": "6mo", 
    "1y": "1y",
    "5y": "5y"
}

# Set default time period to "1y"
if "selected_period" not in st.session_state:
    st.session_state.selected_period = "1y"

# Fetch and display stock data if a ticker is entered
if ticker:
    stock_history = get_stock_history(ticker, st.session_state.selected_period)
    
    # Calculate indicators
    stock_history_with_indicators = calculate_indicators(stock_history)

    # Display stock information
    display_stock_info(ticker)

    # Plot stock chart
    st.plotly_chart(plot_stock_chart(stock_history_with_indicators, ticker))

    # Display time period buttons **below the chart**
    button_container = st.container()
    cols = st.columns(len(time_periods))
    for i, (label, period) in enumerate(time_periods.items()):
        with cols[i]:
            is_selected = st.session_state.selected_period == period
            button_color = "primary" if is_selected else "secondary"
            # When a button is pressed, update the selected period in session state
            if st.button(label):
                st.session_state.selected_period = period
                is_selected = st.session_state.selected_period == period
                button_color = "primary" if is_selected else "secondary"
                st.rerun()

    # Card to place an order
    st.subheader("Place an Order (this doesnt actually place an order yet)")
    order_type = st.selectbox("Order Type", ["Buy", "Sell"])
    quantity = st.number_input("Quantity", min_value=1, step=1)

    if st.button("Place Order"):
        # Simulate placing an order (You can implement actual order placement logic here)
        st.success(f"{order_type} order for {quantity} shares of {ticker} placed!")

    # Display stock data
    st.write(f"## {ticker} Stock Historical Data with Indicators")
    st.write(stock_history_with_indicators)
