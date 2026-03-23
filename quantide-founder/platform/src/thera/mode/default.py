import logging
import re
from typing import List, Optional

from thera.config import load_config
from thera.llm import get_annotation

logger = logging.getLogger(__name__)


def read_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def split_paragraphs(content: str) -> List[str]:
    paragraphs = content.split("\n\n")
    result = []
    for p in paragraphs:
        p = p.strip()
        if p:
            result.append(p)
    return result


def is_short(text: str, min_length: int = 20) -> bool:
    return len(text) < min_length


def is_already_annotated(text: str, marker: str = "🤖 观察者注") -> bool:
    return marker in text


def is_code_block(text: str) -> bool:
    return bool(re.match(r"^```", text.strip()))


def is_punctuation_only(text: str) -> bool:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]", "", text)
    return len(cleaned) == 0


def process_paragraph(
    paragraph: str,
    settings,
) -> Optional[str]:
    if is_code_block(paragraph):
        logger.debug("跳过代码块")
        return None

    if is_punctuation_only(paragraph):
        logger.debug("跳过仅含标点的段落")
        return None

    if is_short(paragraph, settings.filter_min_paragraph_length):
        logger.debug(f"跳过短段落（{len(paragraph)}字符）")
        return None

    if is_already_annotated(paragraph, settings.filter_annotation_marker):
        logger.debug("跳过已批注段落")
        return None

    try:
        annotation = get_annotation(paragraph, settings=settings)
        if annotation is None:
            logger.debug("LLM返回SKIP，跳过该段落")
            return None
        return annotation
    except Exception as e:
        logger.error(f"处理段落失败: {e}")
        return None


def run_default_mode(file_path: str, config_path: str, output_path: str = None) -> None:
    settings = load_config(config_path)
    logger.info(f"开始处理文件: {file_path}")

    content = read_file(file_path)
    paragraphs = split_paragraphs(content)

    logger.info(f"共{len(paragraphs)}个段落")

    new_paragraphs = []
    for i, paragraph in enumerate(paragraphs, 1):
        logger.info(f"处理段落 {i}/{len(paragraphs)}")

        annotation = process_paragraph(paragraph, settings)

        if annotation:
            new_paragraphs.append(paragraph)
            new_paragraphs.append("")
            annotation_lines = annotation.strip().split("\n")
            quoted_lines = []
            for line in annotation_lines:
                stripped = line.lstrip("> ").strip()
                if stripped:
                    quoted_lines.append(f"> {stripped}")
                else:
                    quoted_lines.append(">")
            quoted_annotation = "\n".join(quoted_lines)
            new_paragraphs.append(quoted_annotation)
        else:
            new_paragraphs.append(paragraph)

        if i % 5 == 0:
            logger.info(f"已处理 {i}/{len(paragraphs)} 个段落")

    new_content = "\n\n".join(new_paragraphs)

    if output_path:
        target_file = output_path
        write_file(target_file, new_content)
        logger.info(f"已完成处理，结果已写入: {target_file}")
    else:
        backup_path = file_path + ".bak"
        write_file(backup_path, content)
        logger.info(f"已备份原文件到: {backup_path}")
        write_file(file_path, new_content)
        logger.info(f"已完成处理，结果已写入: {file_path}")
