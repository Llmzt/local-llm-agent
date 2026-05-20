"""知识库写入工具。"""

from service.knowledge_store import KnowledgeStore
from service.logger import get_logger

logger = get_logger(__name__)

ADD_PREFIXES = (
    "添加知识：",
    "添加知识:",
    "新增知识：",
    "新增知识:",
    "写入知识：",
    "写入知识:",
)

def add_knowledge(user_input: str) -> str:
    """从用户输入中解析知识，并写入 SQLite。"""
    raw_text = remove_add_prefix(user_input)
    parsed = parse_knowledge_text(raw_text)

    if parsed is None:
        logger.info(
            "knowledge add rejected: invalid format input_length=%s",
            len(user_input),
        )
        return(
            "知识库格式不正确。请使用："
            "添加知识：标题 | 内容 | 关键词"
        )
    
    title, content, keywords = parsed

    item = KnowledgeStore().add(
        title = title,
        content = content,
        keywords = keywords,
    )
    
    logger.info(
        "knowledge added: id=%s title_length=%s content_length=%s",
        item.id,
        len(item.title),
        len(item.content),
    )

    return f"已添加知识：{item.title}"

def remove_add_prefix(user_input: str) ->str:
    """去掉添加知识的指令前缀。"""
    text = user_input.strip()
    for prefix in ADD_PREFIXES:
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    return text

def parse_knowledge_text(text:str) ->tuple[str, str, str] | None:
    """解析：标题｜内容｜关键词"""
    parts = [part.strip() for part in text.split("|")]

    if len(parts) < 2:
        return None
    
    title = parts[0]
    content = parts[1]
    keywords = parts[2]if len(parts) >= 3 else ""

    if not title or not content:
        return None
    
    return title,content,keywords
