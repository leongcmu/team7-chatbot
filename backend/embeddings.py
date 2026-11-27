"""Local semantic retrieval over approved knowledge-base records."""
from dataclasses import dataclass
from functools import lru_cache

from .config import ROOT, get_settings
from .knowledge_base import all_records


class EmbeddingUnavailable(RuntimeError):
    """Raised when the optional local embedding runtime cannot be loaded."""


@dataclass(frozen=True)
class EmbeddingHit:
    record_id: str
    score: float


def _record_texts(item: dict) -> list[str]:
    values=[
        item.get('question'),item.get('name'),item.get('title'),
        *item.get('alternate_phrasings',[]),item.get('answer'),
        item.get('description'),item.get('summary'),*item.get('topics',[]),
    ]
    return [str(value) for value in values if value]


def _cache_ready(model_name: str) -> bool:
    model_cache=ROOT/'.model_cache'/('models--'+model_name.replace('/','--'))
    return any(model_cache.rglob('modules.json'))


@lru_cache
def _index(model_name: str, local_files_only: bool):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise EmbeddingUnavailable(
            'sentence-transformers is not installed; run pip install -r requirements.txt'
        ) from exc
    items=all_records()
    phrases=[]
    record_ids=[]
    for item in items:
        for phrase in _record_texts(item):
            phrases.append(phrase)
            record_ids.append(item['id'])
    try:
        model=SentenceTransformer(
            model_name,cache_folder=str(ROOT/'.model_cache'),
            local_files_only=local_files_only,
        )
        vectors=model.encode(
            phrases,
            normalize_embeddings=True,show_progress_bar=False,
        )
    except Exception as exc:
        raise EmbeddingUnavailable(str(exc)) from exc
    return model,tuple(record_ids),vectors


def embedding_search(query: str, *, limit: int=1,
                     min_score: float | None=None,
                     allowed_ids: set[str] | None=None) -> list[EmbeddingHit]:
    """Return candidate record IDs ranked by semantic cosine similarity."""
    settings=get_settings()
    threshold=settings.embedding_min_score if min_score is None else min_score
    model,record_ids,vectors=_index(
        settings.embedding_model,_cache_ready(settings.embedding_model),
    )
    query_vector=model.encode(
        [query],normalize_embeddings=True,show_progress_bar=False,
    )[0]
    scores=vectors @ query_vector
    best_by_record={}
    for index,record_id in enumerate(record_ids):
        if allowed_ids is not None and record_id not in allowed_ids:
            continue
        best_by_record[record_id]=max(best_by_record.get(record_id,-1.0),float(scores[index]))
    ranking=sorted(best_by_record,key=best_by_record.get,reverse=True)
    return [
        EmbeddingHit(record_id,round(best_by_record[record_id],4))
        for record_id in ranking[:limit] if best_by_record[record_id] >= threshold
    ]


def preload_embeddings(*, allow_download: bool=True) -> None:
    """Download/load the configured model and build the record index."""
    settings=get_settings()
    _index(settings.embedding_model,not allow_download)
