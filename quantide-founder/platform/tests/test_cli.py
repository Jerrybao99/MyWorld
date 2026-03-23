import os
import sys
import pytest
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestCLI:
    def test_cli_help(self, capsys):
        with pytest.raises(SystemExit):
            from thera.cli import main

            sys.argv = ["thera", "--help"]
            main()
        captured = capsys.readouterr()
        assert "Thera" in captured.out or "usage" in captured.out.lower()

    def test_cli_missing_file(self, capsys, tmp_path):
        from thera.cli import main

        sys.argv = ["thera", str(tmp_path / "nonexistent.md")]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_cli_with_test_file(self, tmp_path):
        test_file = tmp_path / "test.md"
        test_file.write_text("测试内容\n\n这是第二段内容，需要超过二十个字符用于测试")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
deepseek:
  api_key: "test_key"
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"
  max_retries: 1
  timeout: 30

filter:
  min_paragraph_length: 20

output:
  max_retries: 1
  retry_delay: 0
""")

        from thera.cli import main

        sys.argv = ["thera", str(test_file), "-c", str(config_file)]

        main()

        backup_file = test_file.with_suffix(".md.bak")
        assert backup_file.exists(), "备份文件应该存在"
