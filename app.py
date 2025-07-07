import yfinance as yf
import pandas as pd
from datetime import datetime
import yagmail

# ------------- CONFIGURATION -------------
MIN_VOLUME = 50000
TIMEFRAME = "15m"
LOOKBACK_DAYS = 3
EMAIL_USER = your_email@gmail.com
EMAIL_PASS = your_app_password
TO_EMAIL = your_email@gmail.com
CSV_FILE = ind_nifty500list.csv
# ----------------------------------------

# Load symbols
symbols = pd.read_csv(CSV_FILE)[Symbol].tolist()
buy_signals, sell_signals = [], []

# Level calculation
def calculate_levels(price, signal_type)
    if price  100
        t1, t2, sl = 1.0, 2.0, 0.8
    elif price  250
        t1, t2, sl = 1.5, 3.0, 1.2
    elif price  500
        t1, t2, sl = 2.5, 4.5, 2.0
    elif price  750
        t1, t2, sl = 3.5, 6.0, 3.0
    else
        t1, t2, sl = 5.0, 8.0, 4.0

    if signal_type == 'Buy'
        return round(price + t1, 2), round(price + t2, 2), round(price - sl, 2)
    else
        return round(price - t1, 2), round(price - t2, 2), round(price + sl, 2)

# Fibonacci levels
def calculate_fib_levels(high, low)
    diff = high - low
    return {
        '0.0%' high,
        '23.6%' high - 0.236  diff,
        '38.2%' high - 0.382  diff,
        '50.0%' high - 0.500  diff,
        '61.8%' high - 0.618  diff,
        '100.0%' low
    }

# Signal generation
for symbol in symbols
    try
        ticker = yf.Ticker(symbol + .NS)
        hist = ticker.history(period=f'{LOOKBACK_DAYS}d', interval=TIMEFRAME)

        if len(hist)  10
            continue

        avg_vol = hist['Volume'].mean()
        if avg_vol  MIN_VOLUME
            continue

        close = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[0]
        if close = 1000
            continue

        high = hist['High'].max()
        low = hist['Low'].min()
        fib = calculate_fib_levels(high, low)
        near_fib = any(abs(close - fib[level])  0.5 for level in ['61.8%', '50.0%'])

        if close  open_price and near_fib
            t1, t2, sl = calculate_levels(close, 'Buy')
            buy_signals.append({
                'Type' 'Buy',
                'Stock' symbol,
                'Entry' round(close, 2),
                'Target 1' t1,
                'Target 2' t2,
                'Stop Loss' sl,
                'Fib Level' min(fib, key=lambda k abs(close - fib[k]))
            })

        elif close  open_price and near_fib
            t1, t2, sl = calculate_levels(close, 'Sell')
            sell_signals.append({
                'Type' 'Short',
                'Stock' symbol,
                'Entry' round(close, 2),
                'Target 1' t1,
                'Target 2' t2,
                'Stop Loss' sl,
                'Fib Level' min(fib, key=lambda k abs(close - fib[k]))
            })

    except Exception as e
        continue

# Sort & select top 3
buy_signals = sorted(buy_signals, key=lambda x abs(x['Entry'] - x['Target 1']))[3]
sell_signals = sorted(sell_signals, key=lambda x abs(x['Entry'] - x['Target 1']))[3]
all_signals = buy_signals + sell_signals

# Format email
def format_email_table(signals)
    if not signals
        return pNo signals today.p

    df = pd.DataFrame(signals)
    return df.to_html(index=False, justify=center, border=1)

# Send email
def send_email()
    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
    subject = f"📈 Fibonacci Signals – {datetime.now().strftime('%d %b %Y')}"
    body = h2🔵 Buy Signalsh2 + format_email_table(buy_signals)
    body += h2🔴 Short Signalsh2 + format_email_table(sell_signals)
    yag.send(TO_EMAIL, subject, body)
    print(✅ Email sent successfully!)

# Execute
if all_signals
    send_email()
else
    print(❌ No signals to send today.)
