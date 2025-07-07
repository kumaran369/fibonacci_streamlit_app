import yfinance as yf
import pandas as pd
from datetime import datetime
import yagmail
import os

# Email credentials (from GitHub Secrets)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Parameters
TIMEFRAME = "15m"
LOOKBACK_DAYS = 3
MIN_VOLUME = 50000

# Load stock symbols
def load_symbols():
    df = pd.read_csv("ind_nifty500list.csv")
    return df['Symbol'].tolist()

# Calculate targets/stop loss
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

# Fibonacci levels
def calculate_fib_levels(high, low):
    diff = high - low
    return {
        '0.0%': high,
        '23.6%': high - 0.236 * diff,
        '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.500 * diff,
        '61.8%': high - 0.618 * diff,
        '100.0%': low
    }

# Send email
def send_email(subject, body, attachment_path):
    if EMAIL_USER and EMAIL_PASS:
        try:
            yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
            yag.send(to=EMAIL_USER, subject=subject, contents=body, attachments=attachment_path)
            print("✅ Email sent.")
        except Exception as e:
            print("❌ Email error:", e)
    else:
        print("⚠️ Email not configured.")

# Main function
def main():
    symbols = load_symbols()
    buy_signals, sell_signals = [], []

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol + ".NS")
            hist = ticker.history(period=f"{LOOKBACK_DAYS}d", interval=TIMEFRAME)

            if len(hist) < 10 or hist['Volume'].mean() < MIN_VOLUME:
                continue

            close = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[0]

            if close >= 1000:
                continue

            high = hist['High'].max()
            low = hist['Low'].min()
            fib = calculate_fib_levels(high, low)

            near_fib = any(abs(close - fib[level]) < 0.5 for level in ['61.8%', '50.0%'])
            if not near_fib:
                continue

            signal = {}
            signal['Stock'] = symbol
            signal['Entry Price'] = round(close, 2)
            signal['Fib Level'] = min(fib, key=lambda k: abs(close - fib[k]))
            signal['Distance to Fib'] = round(abs(close - fib['61.8%']), 2)

            if close > open_price:
                signal['Signal'] = 'Buy'
                t1, t2, sl = calculate_levels(close, 'Buy')
            elif close < open_price:
                signal['Signal'] = 'Short'
                t1, t2, sl = calculate_levels(close, 'Sell')
            else:
                continue

            signal['Target 1'] = t1
            signal['Target 2'] = t2
            signal['Stop Loss'] = sl

            if signal['Signal'] == 'Buy':
                buy_signals.append(signal)
            else:
                sell_signals.append(signal)

        except Exception as e:
            print(f"Error with {symbol}: {e}")
            continue

    # Keep only one best buy and one best short
    top_buys = sorted(buy_signals, key=lambda x: x['Distance to Fib'])[:1]
    top_sells = sorted(sell_signals, key=lambda x: x['Distance to Fib'])[:1]
    final_signals = top_buys + top_sells

    if final_signals:
        df = pd.DataFrame(final_signals).drop(columns=["Distance to Fib"])
        filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(filename, index=False)
        print("✅ Signals saved to:", filename)

        subject = f"📈 Fibonacci Signals TWO – {datetime.now().strftime('%d %b %Y')}"
        body = f"{len(final_signals)} signals found.\n\n" + df.to_string(index=False)
        send_email(subject, body, filename)
    else:
        print("❌ No signals found.")

if __name__ == "__main__":
    main()
