import argparse
import logging
import sys
from pathlib import Path

from thera.mode.default import run_default_mode


def main():
    parser = argparse.ArgumentParser(
        description="Thera - 写作观察者，为文本添加结构化批注"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="要处理的文件路径（默认: 当前目录下的 journal.md）",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="配置文件路径（默认: config.yaml）",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="显示详细日志",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="输出文件路径（默认: 覆盖原文件）",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.file:
        file_path = Path(args.file)
    else:
        file_path = Path.cwd() / "journal.md"

    if not file_path.exists():
        logging.error(f"文件不存在: {file_path}")
        sys.exit(1)

    config_path = args.config
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    try:
        run_default_mode(str(file_path), str(config_path), args.output)
    except Exception as e:
        logging.error(f"处理失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
