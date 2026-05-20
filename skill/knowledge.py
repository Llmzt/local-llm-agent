"""知识库查询入口。"""

from service.knowledge_store import KnowledgeStore


STOP_WORDS = (
    "查询知识库",
    "搜索知识库",
    "知识库",
    "查询",
    "搜索",
    "检索",
    "查一下",
    "什么是",
    "是什么",
    "请问",
)


def search_knowledge(user_input: str) -> str:
    """清洗用户输入，查询 SQLite 知识库，并返回文本结果。"""
    query = extract_query(user_input)
    if not query:
        return "请提供要查询的关键词。"

    items = KnowledgeStore().search(query, limit=3)
    if not items:
        return "没有找到相关知识。"

    return "\n".join(f"- {item.title}：{item.content}" for item in items)


def extract_query(user_input: str) -> str:
    """去掉常见指令词，留下真正要查询的关键词。"""
    query = user_input.strip()
    for word in STOP_WORDS:
        query = query.replace(word, "")
    return query.strip(" ：:，,。！？!?")
