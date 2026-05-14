import requests
import os
from datetime import datetime, timezone, timedelta

# ---- 1. 东八区日期 & 时间戳 ----
def get_today_str():
    beijing_now = datetime.now(timezone.utc) + timedelta(hours=8)
    return beijing_now.strftime("%Y年%m月%d日 %H:%M")

def get_full_prompt():
    today = get_today_str()
    
    # 【关键】把你的完整提示词粘贴在这个三引号中间
    prompt = f"""今天是东八区{today}，请严格按照我们之前确定的最终版模板，联网搜索并生成今日的加密市场晨报。

报告必须包含以下所有板块，每个部分都需给出明确判断，而不是简单罗列数据：

---
**加密市场、美股及大宗商品晨报速览 | {today} (东八区)**

### 1. 核心指标速览
- 美股市场表格（纳斯达克/标普500/道指 实时价格、涨跌幅）
- 加密与大宗商品表格（BTC/ETH/SOL价格、恐慌指数、美元指数、ETF资金流、黄金/白银/WTI/布伦特）
- 情绪速评一小段

### 2. 宏观与地缘交火点
- 宏观交易主线（通胀、利率、美元、非农、CPI/PPI等最新数据）
- 地缘政治核心事件（美伊局势、霍尔木兹海峡、OPEC等）

### 3. 特别关注：MSTR“卖币付息”言论与BTC的多空博弈（如有最新财报或言论则分析）

### 4. 技术面关键地图
- BTC：核心博弈区间、阻力支撑位、RSI、EMA
- ETH：趋势判断、关键支撑阻力
- SOL：机构资金流入、支撑阻力

### 5. 期权市场预警信号
- IV、负Gamma仓位、偏度变化、波动率风险溢价

### 6. 预测市场与多市场定价分歧（三市场对比表格）
| 资产 | 预测市场（Polymarket） | 期权市场 | 合约市场 | 综合方向 |

### 7. BTC ETF资金面
- 当日/当周净流入流出数据、IBIT/FBTC等主要产品明细

### 8. 美股市场与头部科技股
- 美股技术面综述
- 头部科技股表现表格（特斯拉/英伟达/苹果/微软/MSTR/COIN/CRCL等）

### 9. 大宗商品
- 原油（WTI/布伦特涨跌、霍尔木兹影响）
- 黄金（COMEX/现货、央行购金动态）
- 白银（工业需求共振）

### 10. 今日最可能主导行情的两个核心逻辑
1. **[逻辑标题]**：简述，并直接说明其对BTC/ETH/SOL/大宗商品的倾向性影响。
2. **[逻辑标题]**：同上。

### 11. 短线风险提示（表格形式）
| 资产 | 核心风险 | 触发信号与后果 |

---

输出铁律：
- 所有关键数据必须通过联网搜索获取，标注时间戳。
- 禁止堆砌数据，每个数字必须有结论。
- 禁止模棱两可，必须给出非黑即白的判断。
- 语言简洁有力，直击要害。
- 在报告末尾标注实际生成时间。
"""

    return prompt

# ---- 2. 读取环境变量 ----
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

# ---- 3. 调用 DeepSeek ----
def fetch_deepseek_report():
    print(f"开始生成报告...")

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位专业的加密货币与大宗商品策略师。"},
            {"role": "user", "content": get_full_prompt()},
        ],
        "stream": False,
        "temperature": 0.8,
        "max_tokens": 8000,  # 长报告需要更多 Token
    }

    r = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ---- 4. 分段发送 ----
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    max_len = 4000

    parts = []
    while len(text) > max_len:
        split_at = text.rfind('\n', 0, max_len)
        if split_at == -1:
            split_at = max_len
        parts.append(text[:split_at])
        text = text[split_at:].lstrip('\n')
    parts.append(text)

    for i, chunk in enumerate(parts):
        prefix = f"**【第{i+1}/{len(parts)}部分】**\n\n" if len(parts) > 1 else ""
        payload = {"chat_id": CHAT_ID, "text": prefix + chunk}
        r = requests.post(url, json=payload, timeout=30)
        print(f"第{i+1}部分发送: {r.json().get('ok')}")

# ---- 5. 主流程 ----
if __name__ == "__main__":
    report = fetch_deepseek_report()
    send_telegram(report)
    print("✅ 全部流程完成")
