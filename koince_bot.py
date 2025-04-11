
import requests
import time
import telebot

# Bot token ve chat ID
BOT_TOKEN = "BOT_TOKENIN_BURAYA"
CHAT_ID = "CHAT_IDIN_BURAYA"

# CryptoPanic API Key
API_KEY = "API_KEYIN_BURAYA"

# Bot oluştur
bot = telebot.TeleBot(BOT_TOKEN)

def escape_markdown(text):
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

def get_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={API_KEY}&kind=news&filter=hot"
    response = requests.get(url)
    data = response.json()

    messages = []
    for post in data.get("results", []):
        title = escape_markdown(post.get("title", ""))
        url_escaped = escape_markdown(post.get("url", ""))
        domain = escape_markdown(post.get("domain", ""))
        published_at = escape_markdown(post.get("published_at", ""))

        message = f"📣 *{title}*\n🔗 {url_escaped}\n🌍 {domain}\n🕒 {published_at}"
        messages.append(message)

    return messages

def main_loop():
    sent_links = set()

    while True:
        try:
            news = get_news()
            for item in news:
                if item not in sent_links:
                    bot.send_message(CHAT_ID, item, parse_mode="MarkdownV2")
                    sent_links.add(item)
                    time.sleep(1)
        except Exception as e:
            print(f"Hata: {e}")

        time.sleep(60 * 5)

if __name__ == "__main__":
    main_loop()
