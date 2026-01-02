from flask import Flask, render_template_string
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

app = Flask(__name__)

# ==========================
# CONFIG
# ==========================
SYMBOL = "ABEV3.SA"   # change asset here
INTERVAL = "15m"
PERIOD = "5d"

# ==========================
# DATA
# ==========================
def get_data():
    df = yf.download(
        tickers=SYMBOL,
        interval=INTERVAL,
        period=PERIOD
    )
    df.dropna(inplace=True)
    return df

# ==========================
# INDICATORS
# ==========================
def add_indicators(df):
    df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["EMA21"] = df["Close"].ewm(span=21, adjust=False).mean()
    return df

# ==========================
# SIGNAL LOGIC
# ==========================
def trading_signal(df):
    last = df.iloc[-1]

    price = last["Close"]
    ema9 = last["EMA9"]
    ema21 = last["EMA21"]

    entry = price
    stop = ema21
    risk = abs(entry - stop)
    take_profit = entry + (risk * 2)

    if price > ema9 and price > ema21 and ema9 > ema21:
        signal = "BUY"
    elif price < ema21 or ema9 < ema21:
        signal = "SELL"
        take_profit = entry - (risk * 2)
    else:
        signal = "HOLD"
        take_profit = None

    return {
        "signal": signal,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "take_profit": round(take_profit, 2) if take_profit else "-"
    }

# ==========================
# CHART
# ==========================
def build_chart(df):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["EMA9"],
        mode="lines",
        name="EMA 9"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["EMA21"],
        mode="lines",
        name="EMA 21"
    ))

    fig.update_layout(
        template="plotly_dark",
        height=600,
        xaxis_rangeslider_visible=False
    )

    return fig.to_html(full_html=False)

# ==========================
# ROUTE
# ==========================
@app.route("/")
def index():
    df = get_data()
    df = add_indicators(df)

    signal_data = trading_signal(df)
    chart = build_chart(df)

    return render_template_string("""
    <html>
    <head>
        <title>Trading Chart</title>
    </head>
    <body style="background:#0f172a;color:white;font-family:Arial;padding:20px">
        <h2>Asset: {{symbol}}</h2>

        <h3>Signal: {{signal.signal}}</h3>
        <p>Entry: {{signal.entry}}</p>
        <p>Stop: {{signal.stop}}</p>
        <p>Exit (Take Profit): {{signal.take_profit}}</p>

        {{chart | safe}}

        <p style="margin-top:20px;font-size:12px;opacity:0.6">
        Educational use only. No financial advice.
        </p>
    </body>
    </html>
    """,
    chart=chart,
    signal=signal_data,
    symbol=SYMBOL)

# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
