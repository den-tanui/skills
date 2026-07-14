from __future__ import annotations
from collections import defaultdict
from typing import List, Optional

from .config import Config
from .db import Database
from .embedder import MockEmbedder
from .models import SearchResult


def search_skills(db: Database, query: str, embedder=None,
                  config: Optional[Config] = None,
                  top_k: int = 10,
                  section_filter: Optional[str] = None,
                  dir_filter: Optional[str] = None) -> List[SearchResult]:
    """Search for skills matching the query. Returns ranked results."""
    if embedder is None:
        embedder = MockEmbedder()
    if config is None:
        config = Config()

    query_vec = embedder.embed(query)

    chunk_results = db.vector_search(query_vec, top_k=100)

    skill_scores = defaultdict(list)

    for chunk_id, similarity in chunk_results:
        chunk = db.get_chunk_by_id(chunk_id)
        if not chunk:
            continue

        if section_filter and not chunk["chunk_type"].startswith(section_filter):
            continue
        if dir_filter and dir_filter not in chunk.get("source_dir_path", ""):
            continue

        weight = config.get_weight(chunk["chunk_type"])
        skill_scores[chunk["skill_id"]].append((similarity, weight))

    scored_skills = []
    for skill_id, scores_and_weights in skill_scores.items():
        total_weighted = sum(s * w for s, w in scores_and_weights)
        total_weight = sum(w for _, w in scores_and_weights)
        avg_score = total_weighted / total_weight if total_weight > 0 else 0

        skill = db.execute("""
            SELECT s.*, sd.path as source_dir_path
            FROM skills s
            JOIN source_dirs sd ON s.source_dir_id = sd.id
            WHERE s.id = ?
        """, (skill_id,)).fetchone()

        if skill:
            file_paths = db.get_skill_file_paths(skill_id)
            scored_skills.append(SearchResult(
                name=skill["name"],
                description=skill["description"] or "",
                score=avg_score,
                source_dir=skill["source_dir_path"],
                abs_path=skill["abs_path"],
                files=file_paths,
                file_count=len(file_paths),
                source_url=skill["source_url"],
                source_commit_hash=skill["source_commit_hash"],
                install_method=skill["install_method"],
            ))

    scored_skills.sort(key=lambda r: r.score, reverse=True)
    return scored_skills[:top_k]
