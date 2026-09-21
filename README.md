# Market Report Bot v2

每天自动生成“加密货币 + 美股指数 + 大宗商品”中文晨报，并通过飞书自定义机器人发送。工作日生成完整跨资产晨报，周末自动切换为加密市场简报。

> 本项目提供市场信息汇总，不构成投资建议。免费数据接口可能延迟、限流或变更，请以交易所和官方数据为准。

## v2 相比原版的改进

- 从单个 `main.py` 拆分为行情、新闻、AI、渲染、飞书、配置和 CLI 模块。
- 加密行情使用 **CoinGecko → Binance** 自动降级。
- 美股与商品使用 **Yahoo Finance → Stooq** 自动降级。
- AI 使用 **DeepSeek → OpenAI** 自动降级；两者都不可用时仍生成纯数据版。
- RSS 新闻先采集再交给 AI 总结，报告保留来源链接，不依赖模型的“联网搜索”参数。
- 数据缺失会明确标记，不再显示成 `$0` 或 `0%`。
- 统一超时、重试、指数退避和 JSON 日志。
- 支持 `--dry-run`，可以预览而不误发消息。
- 增加 pytest、Ruff、GitHub CI、手动工作流和 7 天报告产物。
- 飞书替代 Telegram；密钥只通过环境变量或 GitHub Secrets 注入。

## 项目结构

```text
market-report-bot/
├─ .github/workflows/
│  ├─ schedule.yml        # 每日生成与飞书发送
│  └─ test.yml            # CI 测试
├─ config/default.yml     # 标的、RSS、模型和超时配置
├─ market_report/
│  ├─ providers/          # 行情与 RSS 适配器
│  ├─ ai.py               # DeepSeek/OpenAI 降级
│  ├─ app.py              # 业务编排
│  ├─ cli.py              # 命令行入口
│  ├─ feishu.py           # 飞书卡片推送
│  └─ renderer.py         # 确定性报告与 AI 提示词
├─ tests/
├─ main.py                # 兼容旧入口
└─ requirements.txt
```

## 一、如何复制 GitHub 上的项目

开始前先检查项目根目录的 `LICENSE`。公开可见不等于可以复制、修改或商用：MIT、BSD、Apache-2.0 通常允许修改和再发布，但必须保留相应声明；GPL/AGPL 有更严格的开源义务；没有许可证时默认不应复制发布。

### 方式 1：Clone 到本地

适合你有仓库写权限，或只想在本地阅读和开发：

```powershell
git clone https://github.com/作者/项目.git
cd 项目
```

Clone 会保留 Git 历史，但不会在你的 GitHub 账号中新建仓库。

### 方式 2：Fork 后再 Clone

适合长期维护自己的版本，或者以后向原作者提交 Pull Request：

1. 在原项目页面点击 **Fork**。
2. Clone 你账号下的 Fork。
3. 添加原项目为 `upstream`。

```powershell
git clone https://github.com/你的用户名/项目.git
cd 项目
git remote add upstream https://github.com/原作者/项目.git
git remote -v
```

同步上游：

```powershell
git fetch upstream
git switch main
git merge upstream/main
git push origin main
```

### 方式 3：Use this template

适合把项目当脚手架，创建没有 Fork 关系的新项目。它通常不会保留完整提交历史，也没有一键同步上游能力。

### 方式 4：Download ZIP

适合临时查看。ZIP 没有 `.git` 历史，不能执行 `git pull`，不适合长期开发。

## 二、把 v2 放入你的仓库

推荐在真实仓库中创建分支，不要直接覆盖 `main`：

```powershell
git clone https://github.com/PPPatY/market-report-bot.git
cd market-report-bot
git switch -c refactor/v2
```

把本版本的文件复制到该分支后：

```powershell
git status
git add .
git commit -m "refactor: build resilient cross-asset morning report v2"
git push -u origin refactor/v2
```

然后在 GitHub 创建 Pull Request，等待“测试”工作流通过后再合并到 `main`。

## 三、本地测试

要求 Python 3.11 或更高版本。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
ruff check .
pytest
```

生成预览（不会发送飞书）：

```powershell
python -m market_report --dry-run --mode full --output report.md
```

在周末测试完整报告时显式使用 `--mode full`；正常计划任务使用 `--mode auto`，会按北京时间自动判断。

没有 DeepSeek/OpenAI Key 时也可以运行：程序会跳过 AI，产出确定性数据版。行情和 RSS 仍需要网络。

## 四、创建飞书机器人

1. 在目标飞书群打开 **设置 → 群机器人 → 添加机器人 → 自定义机器人**。
2. 设置名称和头像。
3. 复制 Webhook 地址。
4. 不要把 Webhook 粘贴进代码、Issue、聊天记录或 README。

Webhook 应类似：

```text
https://open.feishu.cn/open-apis/bot/v2/hook/……
```

如果为机器人启用了“关键词”安全设置，请确保允许晨报标题中的关键词；也可以使用飞书提供的签名校验方案扩展 `FeishuSender`。

## 五、配置 GitHub Secrets

打开仓库：**Settings → Secrets and variables → Actions → New repository secret**，依次添加：

| Secret | 必需 | 用途 |
|---|---:|---|
| `FEISHU_WEBHOOK_URL` | 是 | 飞书自定义机器人地址 |
| `DEEPSEEK_API_KEY` | 建议 | 主 AI 模型 |
| `OPENAI_API_KEY` | 建议 | DeepSeek 失败时自动兜底 |

不要把 Key 发给他人，也不要提交 `.env`。`.env.example` 只有变量名，可以安全提交。

## 六、首次在 GitHub 上验收

1. 进入仓库 **Actions**。
2. 选择 **生成并发送每日晨报**。
3. 点击 **Run workflow**。
4. 第一次将 `dry_run` 设为 `true`，模式选 `full`。
5. 运行成功后，在该次运行的 **Artifacts** 下载 `market-report-*`，检查 `report.md`。
6. 再运行一次，把 `dry_run` 设为 `false`，验证飞书收到消息。

定时表达式为 `30 23 * * *`，即北京时间次日约 07:30。GitHub 明确不保证定时工作流准点，高峰期可能排队；若必须精确到分钟，应改用云服务器或专业调度服务。

## 七、自定义标的、新闻源和模型

修改 `config/default.yml`：

- `assets.crypto`：需要 CoinGecko ID 和 Binance USDT 交易对。
- `assets.equities` / `assets.commodities`：需要 Yahoo 与 Stooq 的符号。
- `news.feeds`：可增加公开 RSS；不要绕过付费墙，也不要抓取或重新发布完整文章。
- `ai.providers`：按数组顺序尝试。模型名和接口地址均可修改。

示例：加入纳斯达克 100 指数：

```yaml
- symbol: NDX
  name: 纳斯达克100
  yahoo_symbol: ^NDX
  stooq_symbol: ^ndx
  unit: 点
```

## 八、失败和降级逻辑

```text
CoinGecko 失败 ──> Binance
Yahoo 失败 ─────> Stooq
RSS 部分失败 ───> 保留其他新闻源并显示警告
DeepSeek 失败 ──> OpenAI
全部 AI 失败 ──> 纯数据版
个别行情失败 ──> 标记“数据暂不可用”，其余报告继续
飞书失败 ───────> 工作流失败，不伪装成发送成功
```

日志不会输出 API Key 或飞书 Webhook。每次 Actions 运行会保存 `report.md` 七天，便于检查失败前生成的内容。

## 九、参考项目与许可证

本次重构的设计参考了下列 MIT 开源项目的公开功能与架构思路，没有移植 AGPL 项目代码：

- [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis)：多数据源、多模型、多通知渠道与配置化设计。
- [yukipanpan/marketbrief](https://github.com/yukipanpan/marketbrief)：跨资产晨报、RSS 与 GitHub Actions 流水线。
- [mutaaf/MarketDigest](https://github.com/mutaaf/MarketDigest)：美股摘要与无 AI 降级思路。

本仓库自身采用 [MIT License](LICENSE)。若以后直接复制其他项目的实质性代码，请保留其许可证、版权声明和必要署名。
