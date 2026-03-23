import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thera.mode.default import (
    split_paragraphs,
    is_short,
    is_already_annotated,
    is_code_block,
    is_punctuation_only,
)


class TestDefaultMode:
    def test_split_paragraphs(self):
        content = "段落1\n\n段落2\n\n段落3"
        result = split_paragraphs(content)
        assert result == ["段落1", "段落2", "段落3"]

    def test_split_paragraphs_empty_strings(self):
        content = "段落1\n\n\n\n段落2"
        result = split_paragraphs(content)
        assert result == ["段落1", "段落2"]

    def test_split_paragraphs_single_paragraph(self):
        content = "只有一个段落"
        result = split_paragraphs(content)
        assert result == ["只有一个段落"]

    def test_is_short_true(self):
        assert is_short("短", 20) is True
        assert is_short("这是一个很短的段落", 20) is True

    def test_is_short_false(self):
        assert is_short("这是一个长度超过二十个中文字符的段落内容", 20) is False

    def test_is_already_annotated_true(self):
        text = "这是段落内容\n\n🤖 观察者注：xxx"
        assert is_already_annotated(text) is True

    def test_is_already_annotated_false(self):
        text = "这是普通段落内容"
        assert is_already_annotated(text) is False

    def test_is_code_block_true(self):
        assert is_code_block("```python\nprint('hello')\n```") is True
        assert is_code_block("```") is True

    def test_is_code_block_false(self):
        assert is_code_block("这是一个普通段落") is False

    def test_is_punctuation_only_true(self):
        assert is_punctuation_only("...,,,!!!") is True
        assert is_punctuation_only("，。、；：") is True

    def test_is_punctuation_only_false(self):
        assert is_punctuation_only("这是文字") is False
        assert is_punctuation_only("文字和标点。") is False
