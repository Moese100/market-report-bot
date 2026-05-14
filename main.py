import requests
import os
from datetime import datetime, timezone, timedelta

# ---- 1. 东八区今天的日期 -----
def get_today_str():
    beijing_now = datetime.now(timezone.utc) + timedelta(hours=8)
    return beijing_now.strftime("%Y年%m月%d日")

# ---- 2. 从仓库 Secrets 读取 token 与 key ----
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

# ---- 3. 调用 DeepSeek 生成报告 ----
def fetch_deepseek_report():
    today = get_today_str()
    prompt = f"""今天是东八区{today}，请严格按照之前确定的最终版模板（共 11 个板块），生成今日的加密市场晨报。"""
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位专业的加密货币与大宗商品策略师。"},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "temperature": 0.8,
        "max_tokens": 4000,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ---- 4. 发送到你的 Telegram ----
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    CHUNK_SIZE = 3800
    for i in range(0, len(text), CHUNK_SIZE):
        chunk = text[i:i + CHUNK_SIZE]
        payload = {"chat_id": CHAT_ID, "text": chunk}
        requests.post(url, json=payload, timeout=30)

# ---- 5. 主流程 ----
if __name__ == "__main__":
    report = fetch_deepseek_report()
    send_telegram(report)
