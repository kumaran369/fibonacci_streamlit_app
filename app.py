import yfinance as yf
import pandas as pd
import yagmail
import os
from datetime import datetime

# Load symbols (customize this file path if needed)
def load_symbols():
    df = pd.read_csv("ind_nifty500list.csv")
    return df['Symbol'].tolist()

# Calculate Fibonacci levels
def calculate_fib_levels(high, low):
    diff = high - low
    return {
        '0.0%': high,
        '23.6%': high - 0.236 * diff,
        '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.5 * diff,
        '61.8%': high - 0.618 * diff,
        '100.0%': low
    }

# Define Target & Stop Loss logic
def calculate_levels(price, signal_type):
    if price < 100:
        t1, t2, sl = 1.0, 2.0, 0.8
    elif price < 250:
        t1, t2, sl = 1.5, 3.0, 1.2
    elif price < 500:
        t1, t2, sl = 2.5, 4.5, 2.0
    elif price < 750:
        t1, t2, sl = 3.5, 6.0, 3.0
    else:
        t1, t2, sl = 5.0, 8.0, 4.0

    if signal_type == 'Buy':
        return round(price + t1, 2), round(price + t2, 2), round(price - sl, 2)
    else:
        return round(price - t1, 2), round(price - t2, 2), round(price + sl, 2)

# Send email using yagmail and environment secrets
def send_email(subject, body):
    EMAIL_USER = os.environ.get("EMAIL_USER")
    EMAIL_PASS = os.environ.get("EMAIL_PASS")
    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
    yag.send(to=EMAIL_USER, subject=subject, contents=body)

# Main logic
def main():
    symbols = load_symbols()
    buy_signals, sell_signals = [], []
    timeframe = "15m"
    lookback_days = 3
    min_volume = 50000

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol + ".NS")
            hist = ticker.history(period=f"{lookback_days}d", interval=timeframe)

            if len(hist) < 10 or hist['Volume'].mean() < min_volume:
                continue

            close = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[0]
            if close >= 1000:
                continue

            high, low = hist['High'].max(), hist['Low'].min()
            fib = calculate_fib_levels(high, low)
            near_fib = any(abs(close - fib[level]) < 0.5 for level in ['61.8%', '50.0%'])

            if close > open_price and near_fib:
                t1, t2, sl = calculate_levels(close, 'Buy')
                buy_signals.append(f"Buy: {symbol} | Entry: ₹{close:.2f} | T1: ₹{t1}, T2: ₹{t2}, SL: ₹{sl}")
            elif close < open_price and near_fib:
                t1, t2, sl = calculate_levels(close, 'Sell')
                sell_signals.append(f"Short: {symbol} | Entry: ₹{close:.2f} | T1: ₹{t1}, T2: ₹{t2}, SL: ₹{sl}")

        except Exception:
            continue

    if not buy_signals and not sell_signals:
        body = "❌ No signals found today."
    else:
        body = "\n".join(["📘 Buy Signals:"] + buy_signals + ["", "📕 Short Signals:"] + sell_signals)

    subject = f"📈 Fibonacci Signals – {datetime.now().strftime('%d %b %Y')}"
    send_email(subject, body)

# Entry point
if __name__ == "__main__":
    main()
