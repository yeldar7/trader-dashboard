import yfinance as yf

def get_stock_data(ticker):
    """Fetch stock data for the given ticker."""
    stock = yf.Ticker(ticker)
    return stock

def get_stock_history(ticker, period='1y'):
    """Fetch historical stock data for the given ticker."""
    stock = get_stock_data(ticker)
    return stock.history(period=period)
