import json
import sqlite3
from pathlib import Path

# DBファイルのパス
DB_PATH = Path("data/app.db")


def get_connection() -> sqlite3.Connection:
    """DBに接続する"""
    conn = sqlite3.connect(DB_PATH)
    # 辞書形式で結果を取得できるようにする
    conn.row_factory = sqlite3.Row
    return conn


# ── 旅行プラン: おすすめスポット ──────────────────────────────────
# category は "nature"(自然) / "gourmet"(グルメ) / "adventure"(刺激) / "culture"(文化) の想定
SPOT_CATEGORIES = ("nature", "gourmet", "adventure", "culture")


def init_spots_db():
    """おすすめスポットテーブルを初期化"""
    conn = get_connection()
    conn.execute("""
        create table if not exists spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        area TEXT NOT NULL,
        category TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        description TEXT,
        address TEXT,
        typical_duration_minutes INTEGER DEFAULT 60,
        recommended_transport TEXT,
        price_range TEXT,
        tags TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def clear_spots():
    """スポットを全削除（再投入前のリセット用）"""
    conn = get_connection()
    conn.execute("DELETE FROM spots")
    conn.commit()
    conn.close()


def insert_spot(spot: dict):
    """スポットを1件追加する

    spot は name, area, category, lat, lng を必須キーとして持つ辞書。
    description / address / typical_duration_minutes / recommended_transport /
    price_range / tags は任意。
    """
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO spots (
            name, area, category, lat, lng, description, address,
            typical_duration_minutes, recommended_transport, price_range, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            spot["name"],
            spot["area"],
            spot["category"],
            spot["lat"],
            spot["lng"],
            spot.get("description", ""),
            spot.get("address", ""),
            spot.get("typical_duration_minutes", 60),
            spot.get("recommended_transport", ""),
            spot.get("price_range", ""),
            spot.get("tags", ""),
        ),
    )
    conn.commit()
    conn.close()


def bulk_insert_spots(spots: list[dict]):
    """スポットをまとめて追加する"""
    for spot in spots:
        insert_spot(spot)


def get_all_areas() -> list[str]:
    """登録済みのエリア一覧を取得する"""
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT area FROM spots ORDER BY area").fetchall()
    conn.close()
    return [row["area"] for row in rows]


def search_spots(categories: list[str] | None = None, area: str | None = None) -> list[dict]:
    """カテゴリ・エリアでおすすめスポットを検索する

    categories: ["nature", "gourmet"] のように複数指定可（OR条件）。Noneなら全カテゴリ対象。
    area: 部分一致で絞り込み。Noneなら全エリア対象。
    """
    conn = get_connection()
    query = "SELECT * FROM spots WHERE 1=1"
    params: list = []

    if categories:
        placeholders = ",".join("?" for _ in categories)
        query += f" AND category IN ({placeholders})"
        params.extend(categories)

    if area:
        query += " AND area LIKE ?"
        params.append(f"%{area}%")

    query += " ORDER BY area, category"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ── 旅行プラン: みんなのプラン共有・コメント ──────────────────────────────────


def init_plans_db():
    """公開プラン・コメントテーブルを初期化"""
    conn = get_connection()
    conn.execute("""
        create table if not exists plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_name TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT,
        departure TEXT,
        purposes TEXT,
        total_estimated_cost INTEGER,
        plan_json TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        create table if not exists plan_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL REFERENCES plans(id),
        author_name TEXT NOT NULL,
        comment TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_plan(author_name: str, plan: dict, answers: dict | None = None) -> int:
    """生成した旅行プランをDBに保存し、公開する

    戻り値: 保存されたプランのid
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO plans (
            author_name, title, summary, departure, purposes, total_estimated_cost, plan_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            author_name,
            plan.get("title", ""),
            plan.get("summary", ""),
            (answers or {}).get("departure", ""),
            ",".join((answers or {}).get("purposes", [])),
            plan.get("total_estimated_cost", 0),
            json.dumps(plan, ensure_ascii=False),
        ),
    )
    conn.commit()
    plan_id = cursor.lastrowid
    conn.close()
    return plan_id


def get_all_plans() -> list[dict]:
    """公開されているプランの一覧を新着順で取得する（plan_jsonは含まない一覧用の情報のみ）"""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, author_name, title, summary, departure, purposes, total_estimated_cost, created_at
        FROM plans ORDER BY created_at DESC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_plan(plan_id: int) -> dict | None:
    """プランの詳細(plan_jsonをパース済み)を取得する"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    plan_row = dict(row)
    plan_row["plan"] = json.loads(plan_row["plan_json"])
    return plan_row


def add_comment(plan_id: int, author_name: str, comment: str):
    """プランにコメントを追加する"""
    conn = get_connection()
    conn.execute(
        "INSERT INTO plan_comments (plan_id, author_name, comment) VALUES (?, ?, ?)",
        (plan_id, author_name, comment),
    )
    conn.commit()
    conn.close()


def get_comments(plan_id: int) -> list[dict]:
    """プランのコメント一覧を古い順で取得する"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM plan_comments WHERE plan_id = ? ORDER BY created_at ASC",
        (plan_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
