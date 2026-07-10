import json

import libsql_client
import streamlit as st

# TURSO_DATABASE_URL が未設定の場合は、従来通りローカルのSQLiteファイルを使う
DB_PATH = "data/app.db"


def get_connection() -> libsql_client.ClientSync:
    """DBに接続する（Turso設定済みならクラウドDB、未設定ならローカルファイル）"""
    turso_url = st.secrets.get("TURSO_DATABASE_URL", "")
    if turso_url:
        # libsql:// (WebSocket/Hrana経由) は手元のlibsql-clientのバージョンとサーバー側の
        # プロトコルが噛み合わずハンドシェイクに失敗するため、https:// (HTTP経由) に変換して使う
        https_url = turso_url.replace("libsql://", "https://", 1)
        return libsql_client.create_client_sync(
            url=https_url,
            auth_token=st.secrets.get("TURSO_AUTH_TOKEN", ""),
        )
    return libsql_client.create_client_sync(url=f"file:{DB_PATH}")


# ── 旅行プラン: おすすめスポット ──────────────────────────────────
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
    conn.close()


def clear_spots():
    """スポットを全削除（再投入前のリセット用）"""
    conn = get_connection()
    conn.execute("DELETE FROM spots")
    conn.close()


def insert_spot(spot: dict):
    """スポットを1件追加する"""
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
    conn.close()


def bulk_insert_spots(spots: list[dict]):
    """スポットをまとめて追加する"""
    for spot in spots:
        insert_spot(spot)


def get_all_areas() -> list[str]:
    """登録済みのエリア一覧を取得する"""
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT area FROM spots ORDER BY area").rows
    conn.close()
    return [row["area"] for row in rows]


def search_spots(categories: list[str] | None = None, area: str | None = None) -> list[dict]:
    """カテゴリ・エリアでおすすめスポットを検索する"""
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
    rows = conn.execute(query, params).rows
    conn.close()
    return [row.asdict() for row in rows]


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
        region TEXT, -- ⭕️ 追加：質問8の地方を保存するカラム
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

    # 既存のplansテーブルに旧スキーマ（region列なし）が残っている場合への移行措置
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(plans)").rows}
    if "region" not in existing_columns:
        conn.execute("ALTER TABLE plans ADD COLUMN region TEXT")

    conn.close()


def save_plan(author_name: str, plan: dict, answers: dict | None = None) -> int:
    """生成した旅行プランをDBに保存し、公開する"""
    
    # ⭕️ 修正：Geminiが必ずsummaryを返すスキーマになったため、綺麗に直接取得
    summary = plan.get("summary", "旅行プランの概要")

    # ⭕️ 修正：Geminiが計算した正確なプラン合計金額（total_estimated_cost）を保存
    estimated_cost = plan.get("total_estimated_cost", (answers or {}).get("budget", 0))

    conn = get_connection()
    result = conn.execute(
        """
        INSERT INTO plans (
            author_name, title, summary, departure, purposes, region, total_estimated_cost, plan_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            author_name,
            plan.get("title", "無題の旅行プラン"),
            summary,
            (answers or {}).get("departure", ""),
            ",".join((answers or {}).get("purposes", [])),
            (answers or {}).get("region", "未設定"), # ⭕️ 追加：質問8の地方を保存
            estimated_cost,
            json.dumps(plan, ensure_ascii=False),
        ),
    )
    plan_id = result.last_insert_rowid
    conn.close()
    return plan_id


def get_all_plans() -> list[dict]:
    """公開されているプランの一覧を新着順で取得する"""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, author_name, title, summary, departure, purposes, region, total_estimated_cost, created_at
        FROM plans ORDER BY created_at DESC
        """
    ).rows
    conn.close()
    return [row.asdict() for row in rows]


def get_plan(plan_id: int) -> dict | None:
    """プランの詳細(plan_jsonをパース済み)を取得する"""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).rows
    conn.close()
    if not rows:
        return None
    plan_row = rows[0].asdict()
    plan_row["plan"] = json.loads(plan_row["plan_json"])
    return plan_row


def add_comment(plan_id: int, author_name: str, comment: str):
    """プランにコメントを追加する"""
    conn = get_connection()
    conn.execute(
        "INSERT INTO plan_comments (plan_id, author_name, comment) VALUES (?, ?, ?)",
        (plan_id, author_name, comment),
    )
    conn.close()


def get_comments(plan_id: int) -> list[dict]:
    """プランのコメント一覧を古い順で取得する"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM plan_comments WHERE plan_id = ? ORDER BY created_at ASC",
        (plan_id,),
    ).rows
    conn.close()
    return [row.asdict() for row in rows]