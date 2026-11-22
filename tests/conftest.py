import pytest

from backend import evidence, tools
from backend.embeddings import EmbeddingUnavailable
from backend.retrieval import search


@pytest.fixture(autouse=True)
def avoid_model_downloads_in_unit_tests(monkeypatch):
    """Unit tests stay offline; embedding behavior is injected where relevant."""
    def unavailable(*_args,**_kwargs):
        raise EmbeddingUnavailable('offline unit test')
    monkeypatch.setattr(evidence,'embedding_search',unavailable)
    def lexical_tool_search(query,items,*,kind,limit=3,min_score=None,source=None):
        return search(
            query,items,kind=kind,limit=limit,
            min_score=0.30 if min_score is None else min_score,source=source,
        )
    monkeypatch.setattr(tools,'semantic_search',lexical_tool_search)
