from __future__ import annotations

import argparse
import sys
from pathlib import Path

from market_report.app import deliver_report, generate_report
from market_report.config import load_settings
from market_report.logging_utils import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成并发送跨资产市场晨报")
    parser.add_argument("--config", default="config/default.yml", help="YAML 配置路径")
    parser.add_argument(
        "--mode", choices=("auto", "full", "crypto"), default="auto", help="报告模式"
    )
    parser.add_argument("--dry-run", action="store_true", help="只生成，不发送飞书")
    parser.add_argument("--output", default="report.md", help="预览文件路径")
    parser.add_argument("--verbose", action="store_true", help="输出调试日志")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)
    try:
        settings = load_settings(args.config)
        report, _snapshot = generate_report(settings, args.mode)
        output = Path(args.output)
        output.write_text(report, encoding="utf-8")
        print(f"报告已写入: {output.resolve()}")
        if args.dry_run:
            print("dry-run：未发送飞书消息")
        else:
            deliver_report(settings, report)
            print("飞书发送成功")
        return 0
    except Exception as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1
