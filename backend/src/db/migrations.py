"""SQLite 幂等 schema 补丁（已有库补列，不破坏数据）。"""

from sqlalchemy.engine import Connection


def apply_sqlite_migrations(sync_conn: Connection) -> None:
    """对已有 SQLite 表执行增量补列。"""
    cursor = sync_conn.connection.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_contexts'"
    )
    if cursor.fetchone() is None:
        return

    cursor.execute("PRAGMA table_info(user_contexts)")
    columns = {row[1] for row in cursor.fetchall()}

    if "clarify_answers_json" not in columns:
        cursor.execute(
            "ALTER TABLE user_contexts ADD COLUMN clarify_answers_json TEXT"
        )

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='goals'"
    )
    if cursor.fetchone() is None:
        return

    cursor.execute("PRAGMA table_info(goals)")
    goal_columns = {row[1] for row in cursor.fetchall()}

    if "preview_json" not in goal_columns:
        cursor.execute("ALTER TABLE goals ADD COLUMN preview_json TEXT")

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='quests'"
    )
    if cursor.fetchone() is None:
        return

    cursor.execute("PRAGMA table_info(quests)")
    quest_columns = {row[1] for row in cursor.fetchall()}

    if "review_json" not in quest_columns:
        cursor.execute("ALTER TABLE quests ADD COLUMN review_json TEXT")
