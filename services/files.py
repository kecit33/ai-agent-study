"""课程资料文件解析：txt / md / docx 纯文本提取（仅标准库）。

安全约束：
- 类型白名单：.txt .md .markdown .docx（拒绝可执行文件与其它二进制）
- 大小上限：单文件 2 MB
- 不保存原始文件到磁盘，仅提取文本入库，避免任意文件落盘
"""
import io
import re
import zipfile

ALLOWED_EXT = {".txt", ".md", ".markdown", ".docx"}
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 20000  # 单份资料入库上限，防止撑爆课程上下文


def _decode_text(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _extract_docx(data: bytes) -> str:
    """docx 本质是 zip：读取 word/document.xml 并拼接 <w:t> 文本，按段落换行。"""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    paragraphs = []
    for para in re.split(r"</w:p>", xml):
        texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", para, re.S)
        line = "".join(texts)
        line = (line.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
        if line.strip():
            paragraphs.append(line.strip())
    return "\n".join(paragraphs)


def extract_text(filename: str, data: bytes) -> dict:
    """返回 {title, text, ext, size}；不合法时抛出 ValueError。"""
    name = (filename or "").strip()
    if not name:
        raise ValueError("未选择文件")
    ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXT:
        raise ValueError("仅支持 .txt / .md / .docx 文件，收到：%s" % (ext or "无扩展名"))
    if not data:
        raise ValueError("文件内容为空")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("文件超过 2 MB 上限")

    if ext == ".docx":
        try:
            text = _extract_docx(data)
        except (zipfile.BadZipFile, KeyError):
            raise ValueError("docx 解析失败：文件损坏或不是有效的 Word 文档")
    else:
        text = _decode_text(data)

    text = (text or "").strip()
    if not text:
        raise ValueError("未能从文件中提取到文字内容")

    truncated = len(text) > MAX_TEXT_CHARS
    return {
        "title": name.rsplit(".", 1)[0],
        "text": text[:MAX_TEXT_CHARS],
        "ext": ext,
        "size": len(data),
        "chars": len(text),
        "truncated": truncated,
    }
