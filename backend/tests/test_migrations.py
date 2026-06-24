"""SQLite 幂等迁移测试。"""

import sqlite3
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from src.db.migrations import apply_sqlite_migrations


def _create_legacy_user_contexts_table(db_path: Path) -> None:
    """模拟 T-004 旧库：user_contexts 无 clarify_answers_json 列。"""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE user_contexts (
            session_id TEXT PRIMARY KEY,
            goal_type TEXT NOT NULL,
            weekly_outcome TEXT NOT NULL,
            available_time TEXT NOT NULL,
            current_level TEXT NOT NULL,
            failure_reason TEXT NOT NULL,
            preferred_intensity TEXT NOT NULL,
            notes TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def test_migration_adds_clarify_answers_json_column() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as temp_db:
        db_path = Path(temp_db.name)

    try:
        _create_legacy_user_contexts_table(db_path)

        engine = create_engine(f"sqlite:///{db_path}")
        with engine.begin() as conn:
            apply_sqlite_migrations(conn)

        legacy_conn = sqlite3.connect(db_path)
        legacy_conn.row_factory = sqlite3.Row
        columns = {
            row["name"]
            for row in legacy_conn.execute("PRAGMA table_info(user_contexts)").fetchall()
        }
        legacy_conn.close()

        assert "clarify_answers_json" in columns
    finally:
        db_path.unlink(missing_ok=True)


def test_migration_is_idempotent() -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as temp_db:
        db_path = Path(temp_db.name)

    try:
        _create_legacy_user_contexts_table(db_path)
        engine = create_engine(f"sqlite:///{db_path}")

        with engine.begin() as conn:
            apply_sqlite_migrations(conn)
            apply_sqlite_migrations(conn)

        legacy_conn = sqlite3.connect(db_path)
        columns = [
            row[1]
            for row in legacy_conn.execute("PRAGMA table_info(user_contexts)").fetchall()
        ]
        legacy_conn.close()

        assert columns.count("clarify_answers_json") == 1
    finally:
        db_path.unlink(missing_ok=True)
