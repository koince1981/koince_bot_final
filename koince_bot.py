import os
import requests
import matplotlib.pyplot as plt
import pandas as pd
import io
from telegram import Bot

# --- AYARLAR ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CRYPTO_PANIC_API_KEY = os.getenv("CRYPTO_PANIC_API_KEY")

bot = Bot(token=BOT_TOKEN)

# --- HABERLERİ ÇEK ---
def get_crypto_news():
    try:
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTO_PANIC_API_KEY}&public=true&kind=news"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except Exception as e:
        print(f"Haber alınamadı: {e}")
        return []

# --- HABERİ ANALİZ ET ---
def analyze_news_reason(title, content):
    positive_keywords = ["partnership", "listing", "launch", "integration", "upgrade"]
    negative_keywords = ["exploit", "hack", "delist", "down", "rug"]
    reason = []
    for word in positive_keywords:
        if word in title.lower() or (content and word in content.lower()):
            reason.append(word)
    for word in negative_keywords:
        if word in title.lower() or (content and word in content.lower()):
            reason.append(word)
    return ", ".join(reason) if reason else "Genel gelişme"

# --- FİYAT VERİSİ AL ---
def get_binance_data(symbol="BTCUSDT", interval="1d", limit=30):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "c1", "c2", "c3", "c4", "c5", "c6"
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close'] = df['close'].astype(float)
        df['low'] = df['low'].astype(float)
        df['high'] = df['high'].astype(float)
        return df[['timestamp', 'close', 'low', 'high']]
    except Exception as e:
        print(f"{symbol} için fiyat verisi alınamadı: {e}")
        return None

        

# --- GİRİŞ ve HEDEF HESAPLA ---
def calculate_levels(df):
    lows = df['low'].sort_values().head(5)
    entry = round(lows.mean(), 4)
    high = df['high'].max()
    low = df['low'].min()
    diff = high - low
    target = round(high + diff * 0.618, 4)
    return entry, target

# --- GRAFİK OLUŞTUR ---
def create_chart(df, symbol):
    plt.figure(figsize=(10, 4))
    plt.plot(df['timestamp'], df['close'], label='Fiyat')
    plt.title(f"{symbol} Fiyat Grafiği")
    plt.xlabel("Tarih")
    plt.ylabel("Fiyat")
    plt.grid(True)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

# --- TELEGRAM'A GÖNDER ---
def send_message_and_chart(symbol, sentiment, strength, reason, entry, target, chart_buf):
    emoji = "🚀" if sentiment == "Pozitif" else "📉"
    message = f"{emoji} {sentiment} Haber\n\nCoin: {symbol} ({strength})\nDurum: {emoji} {'Pump' if sentiment == 'Pozitif' else 'Dump'} sinyali\nSebep: {reason}\n\n🎯 Giriş Seviyesi: {entry} USDT\n🎯 Hedef Seviye: {target} USDT\n\nKaynak: CryptoPanic"
    try:
        bot.send_photo(chat_id=CHAT_ID, photo=chart_buf, caption=message)
    except Exception as e:
        print(f"Telegram'a gönderilemedi: {e}")

# --- ANA FONKSİYON ---
def main():
    news = get_crypto_news()
    for post in news:
        currencies = post.get('currencies')
        if not currencies:
            continue
        for coin in currencies:
            symbol_code = coin['code'].upper()
            symbol = symbol_code + "USDT"
            sentiment = "Pozitif" if post.get('positive_votes', 0) > post.get('negative_votes', 0) else "Negatif"
            strength = "sağlam" if symbol_code in ["BTC", "ETH", "SOL", "BNB"] else "zayıf"
            reason = analyze_news_reason(post['title'], post.get('body'))

            df = get_binance_data(symbol)
            if df is not None:
                entry, target = calculate_levels(df)
                chart = create_chart(df, symbol)
                send_message_and_chart(symbol, sentiment, strength, reason, entry, target, chart)

if __name__ == "__main__":
    main()
