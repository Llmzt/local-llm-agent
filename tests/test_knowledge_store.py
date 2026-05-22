"""建临时数据库，测试数据库添加与搜索"""

from service.stores.knowledge_store import KnowledgeStore


def test_add_and_search_knowledge(tmp_path):
    db_path = tmp_path / "knowledge.db"
    store = KnowledgeStore(db_path)

    item = store.add(
        title="山东大学",
        content="山东大学 是一所 综合性 大学。",
        keywords="山大,山东大学",
    )
    
    assert item.id == 1
    assert item.title == "山东大学"

    results = store.search("山东大学")

    assert len(results) == 1
    assert results[0].title == "山东大学"
    assert results[0].content == "山东大学 是一所 综合性 大学。"


def test_search_returns_empty_list_when_not_found(tmp_path):
    db_path = tmp_path / "knowledge.db"
    store = KnowledgeStore(db_path)

    store.add("Python", "Python 是一门编程语言。", "language")

    assert store.search("不存在的内容") == []
