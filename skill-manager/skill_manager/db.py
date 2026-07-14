from __future__ import annotations
import sqlite3
import struct
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


VEC_DIM = 384


class Database:
    """SQLite + sqlite-vec database wrapper."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.row_factory = sqlite3.Row
        self._init_vec()
        self._create_schema()

    def _init_vec(self):
        """Load sqlite-vec extension."""
        try:
            import sqlite_vec
            self.conn.enable_load_extension(True)
            sqlite_vec.load(self.conn)
            self.conn.enable_load_extension(False)
        except ImportError:
            raise RuntimeError(
                "sqlite-vec not installed. Run: pip install sqlite-vec"
            )

    def _create_schema(self):
        self.conn.executescript(f"""
            CREATE TABLE IF NOT EXISTS source_dirs (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                label TEXT,
                priority INTEGER DEFAULT 0,
                added_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                source_dir_id INTEGER REFERENCES source_dirs(id),
                dir_path TEXT NOT NULL,
                abs_path TEXT NOT NULL,
                description TEXT,
                frontmatter_json TEXT,
                size_bytes INTEGER,
                install_method TEXT DEFAULT 'discovered',
                source_url TEXT,
                source_repo TEXT,
                source_commit_hash TEXT,
                indexed_at TEXT,
                modified_at TEXT,
                UNIQUE(name, abs_path)
            );

            CREATE TABLE IF NOT EXISTS file_hashes (
                id INTEGER PRIMARY KEY,
                skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
                file_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                mtime REAL,
                UNIQUE(skill_id, file_path)
            );

            CREATE TABLE IF NOT EXISTS skill_chunks (
                id INTEGER PRIMARY KEY,
                skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
                chunk_type TEXT NOT NULL,
                section_heading TEXT,
                content TEXT NOT NULL,
                content_preview TEXT,
                file_path TEXT,
                embedding BLOB
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
                embedding float[{VEC_DIM}]
            );
        """)
        self.conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, params: list) -> sqlite3.Cursor:
        return self.conn.executemany(sql, params)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    # --- CRUD: source_dirs ---

    def add_source_dir(self, path: str, label: str = "") -> int:
        cur = self.execute(
            "INSERT OR IGNORE INTO source_dirs (path, label) VALUES (?, ?)",
            (path, label),
        )
        self.commit()
        if cur.lastrowid:
            return cur.lastrowid
        row = self.execute(
            "SELECT id FROM source_dirs WHERE path = ?", (path,)
        ).fetchone()
        return row["id"]

    def remove_source_dir(self, path: str):
        self.execute("DELETE FROM source_dirs WHERE path = ?", (path,))
        self.commit()

    def get_source_dirs(self) -> List[Dict[str, Any]]:
        rows = self.execute("SELECT * FROM source_dirs ORDER BY priority").fetchall()
        return [dict(r) for r in rows]

    # --- CRUD: skills ---

    def upsert_skill(self, name: str, source_dir_id: int, dir_path: str,
                     abs_path: str, description: str = "",
                     frontmatter_json: str = "", size_bytes: int = 0) -> int:
        cur = self.execute("""
            INSERT INTO skills (name, source_dir_id, dir_path, abs_path,
                                description, frontmatter_json, size_bytes,
                                indexed_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(name, abs_path) DO UPDATE SET
                description = excluded.description,
                frontmatter_json = excluded.frontmatter_json,
                size_bytes = excluded.size_bytes,
                modified_at = datetime('now')
        """, (name, source_dir_id, dir_path, abs_path, description,
              frontmatter_json, size_bytes))
        self.commit()
        if cur.lastrowid:
            return cur.lastrowid
        row = self.execute(
            "SELECT id FROM skills WHERE name = ? AND abs_path = ?",
            (name, abs_path)
        ).fetchone()
        return row["id"] if row else -1

    def delete_skill(self, skill_id: int):
        self.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
        self.commit()

    def delete_skill_by_path(self, abs_path: str):
        self.execute("DELETE FROM skills WHERE abs_path = ?", (abs_path,))
        self.commit()

    def get_skill_by_path(self, abs_path: str) -> Optional[Dict]:
        row = self.execute("""
            SELECT s.*, sd.path as source_dir_path
            FROM skills s
            JOIN source_dirs sd ON s.source_dir_id = sd.id
            WHERE s.abs_path = ?
        """, (abs_path,)).fetchone()
        return dict(row) if row else None

    def get_all_skills(self) -> List[Dict]:
        rows = self.execute("""
            SELECT s.*, sd.path as source_dir_path
            FROM skills s
            JOIN source_dirs sd ON s.source_dir_id = sd.id
            ORDER BY sd.path, s.name
        """).fetchall()
        return [dict(r) for r in rows]

    # --- CRUD: file_hashes ---

    def upsert_file_hash(self, skill_id: int, file_path: str,
                         sha256: str, mtime: float):
        self.execute("""
            INSERT INTO file_hashes (skill_id, file_path, sha256, mtime)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(skill_id, file_path) DO UPDATE SET
                sha256 = excluded.sha256,
                mtime = excluded.mtime
        """, (skill_id, file_path, sha256, mtime))

    def delete_file_hash(self, skill_id: int, file_path: str):
        self.execute(
            "DELETE FROM file_hashes WHERE skill_id = ? AND file_path = ?",
            (skill_id, file_path),
        )

    def get_file_hashes(self, skill_id: int) -> List[Dict]:
        rows = self.execute(
            "SELECT * FROM file_hashes WHERE skill_id = ?", (skill_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_skill_file_paths(self, skill_id: int) -> List[str]:
        rows = self.execute(
            "SELECT file_path FROM file_hashes WHERE skill_id = ?",
            (skill_id,)
        ).fetchall()
        return [r["file_path"] for r in rows]

    # --- CRUD: chunks ---

    def insert_chunk(self, skill_id: int, chunk_type: str,
                     content: str, section_heading: str = "",
                     file_path: str = "") -> int:
        preview = content[:200] + "..." if len(content) > 200 else content
        cur = self.execute("""
            INSERT INTO skill_chunks
                (skill_id, chunk_type, section_heading, content, content_preview, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (skill_id, chunk_type, section_heading, content, preview, file_path))
        return cur.lastrowid if cur.lastrowid else -1

    def delete_chunks_for_file(self, skill_id: int, file_path: str):
        self.execute(
            "DELETE FROM skill_chunks WHERE skill_id = ? AND file_path = ?",
            (skill_id, file_path),
        )

    def delete_all_chunks_for_skill(self, skill_id: int):
        self.execute("DELETE FROM skill_chunks WHERE skill_id = ?", (skill_id,))

    def store_embedding(self, chunk_id: int, embedding: np.ndarray):
        """Store a 384-dim embedding blob and add to vec index."""
        blob = struct.pack(f"{VEC_DIM}f", *embedding.astype(np.float32).flatten())
        self.execute(
            "UPDATE skill_chunks SET embedding = ? WHERE id = ?",
            (blob, chunk_id),
        )
        self.execute(
            "INSERT OR REPLACE INTO vec_chunks(rowid, embedding) VALUES (?, ?)",
            (chunk_id, blob),
        )

    # --- Vector search ---

    def vector_search(self, query_embedding: np.ndarray, top_k: int = 100) -> List[Tuple[int, float]]:
        """Return list of (chunk_id, distance) from vec index."""
        blob = struct.pack(f"{VEC_DIM}f", *query_embedding.astype(np.float32).flatten())
        rows = self.execute("""
            SELECT rowid, distance
            FROM vec_chunks
            WHERE embedding MATCH ?
            ORDER BY distance
            LIMIT ?
        """, (blob, top_k)).fetchall()
        return [(r["rowid"], 1.0 - r["distance"]) for r in rows]  # convert distance to similarity

    def get_chunk_by_id(self, chunk_id: int) -> Optional[Dict]:
        row = self.execute("""
            SELECT sc.*, s.name as skill_name, s.abs_path as skill_abs_path,
                   sd.path as source_dir_path
            FROM skill_chunks sc
            JOIN skills s ON sc.skill_id = s.id
            JOIN source_dirs sd ON s.source_dir_id = sd.id
            WHERE sc.id = ?
        """, (chunk_id,)).fetchone()
        return dict(row) if row else None
