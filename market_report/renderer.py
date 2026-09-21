from __future__ import annotations

from collections import defaultdict

from market_report.models import MarketSnapshot, Quote

CATEGORY_NAMES = {
    "crypto": "加密货币",
    "equity": "美股指数",
    "commodity": "大宗商品",
}


def render_data_report(snapshot: MarketSnapshot, title: str) -> str:
    mode_label = "周末加密简报" if snapshot.mode == "crypto" else "跨资产晨报"
    lines = [
        f"# 📊 {title} · {mode_label}",
        "",
        f"> 数据时间：{snapshot.generated_at:%Y-%m-%d %H:%M %Z}",
        "",
    ]
    grouped: dict[str, list[Quote]] = defaultdict(list)
    for item in snapshot.quotes:
        grouped[item.category].append(item)
    for category in ("crypto", "equity", "commodity"):
        quotes = grouped.get(category, [])
        if not quotes:
            continue
        lines.extend([f"## {CATEGORY_NAMES[category]}", ""])
        for quote in quotes:
            if not quote.available:
                lines.append(f"- **{quote.name}**：数据暂不可用（{quote.error or '未知错误'}）")
                continue
            change = f"{quote.change_pct:+.2f}%" if quote.change_pct is not None else "暂无"
            price = _format_price(quote)
            market_cap = (
                f"，市值 ${quote.market_cap / 1_000_000_000:,.1f}B"
                if quote.market_cap is not None
                else ""
            )
            lines.append(
                f"- **{quote.name}**：{price}，涨跌 {change}{market_cap} "
                f"`来源：{quote.source}`"
            )
        lines.append("")
    if snapshot.fear_greed:
        lines.extend(
            [
                "## 市场情绪",
                "",
                f"- 加密恐慌贪婪指数：**{snapshot.fear_greed[0]}**（{snapshot.fear_greed[1]}）",
                "",
            ]
        )
    lines.extend(["## 今日新闻", ""])
    if snapshot.news:
        for item in snapshot.news:
            lines.append(f"- [{_escape_title(item.title)}]({item.url}) — {item.source}")
    else:
        lines.append("- 新闻源暂不可用，报告仅包含行情数据。")
    if snapshot.warnings:
        lines.extend(["", "## 数据状态", ""])
        lines.extend(f"- ⚠️ {warning}" for warning in snapshot.warnings)
    lines.extend(
        [
            "",
            "---",
            "*本报告由公开数据自动生成，仅供信息参考，不构成投资建议。*",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_ai_prompt(snapshot: MarketSnapshot, deterministic_report: str) -> str:
    cited_news = "\n".join(
        f"{index}. {item.title} | {item.source} | {item.url}"
        for index, item in enumerate(snapshot.news, 1)
    )
    return f"""请根据下方的确定性行情报告和新闻清单，写一份中文 3–5 分钟市场晨报。

硬性要求：
1. 不得修改、补写或推断任何行情数字；行情数字只能来自确定性报告。
2. 不得声称你进行了联网搜索。只能使用给定新闻清单。
3. 每条新闻观点必须保留对应 Markdown 原文链接；没有来源的信息不要写。
4. 结构为：核心速览、隔夜主线、跨资产联动、今日关注、风险提示。
5. 不给出确定性交易指令，不编造 RSI、支撑阻力、ETF 流量或经济数据。
6. 输出飞书可显示的 Markdown；控制在约 1800 个汉字以内。

【确定性行情报告】
{deterministic_report}

【允许引用的新闻】
{cited_news or '无可用新闻，只能总结行情。'}
"""


def combine_report(base_report: str, ai_analysis: str, provider: str) -> str:
    marker = "## 今日新闻"
    heading = (
        f"## AI 市场解读\n\n> 本段由 {provider} 基于上方数据与下方链接生成。\n\n"
        f"{ai_analysis.strip()}\n\n"
    )
    if marker in base_report:
        return base_report.replace(marker, heading + marker, 1)
    return base_report + "\n" + heading


def _format_price(quote: Quote) -> str:
    if quote.price is None:
        return "不可用"
    if quote.category == "crypto" or quote.unit.startswith("USD") or quote.unit.startswith("$"):
        decimals = 4 if quote.price < 1 else 2
        return f"${quote.price:,.{decimals}f} {quote.unit}".strip()
    return f"{quote.price:,.2f} {quote.unit}".strip()


def _escape_title(title: str) -> str:
    return title.replace("[", "［").replace("]", "］")
