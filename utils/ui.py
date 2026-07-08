"""アプリ共通のデザイン（テーマCSS・アイコン・イラスト素材）を扱うモジュール"""

import base64
from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
ILLUST_DIR = ASSETS_DIR / "illustrations"

# スポット/目的のカテゴリ → アイコン画像 の対応
CATEGORY_ICONS = {
    "nature": "icon_mountain",
    "gourmet": "icon_fork_knife",
    "adventure": "icon_camera",
    "culture": "icon_passport",
    "move": "icon_signpost",
    "other": "icon_photos_stack",
}


def icon_path(name: str) -> str:
    """アイコン画像の絶対パスを返す"""
    return str(ICONS_DIR / f"{name}.png")


def illust_path(name: str) -> str:
    """イラスト/写真素材の絶対パスを返す"""
    return str(ILLUST_DIR / f"{name}.png")


def category_icon_path(category: str) -> str:
    """カテゴリキーに対応するアイコンのパスを返す（未知のカテゴリはotherにフォールバック）"""
    return icon_path(CATEGORY_ICONS.get(category, CATEGORY_ICONS["other"]))


@st.cache_data
def _image_b64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


def apply_theme():
    """アプリ全体のデザイン（Inter・引き締めた余白・カード階層・ステータスバッジ）をCSSで適用する"""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --accent: #2E9C9C;
            --accent-dark: #1F7A7A;
            --ink: #1A1F24;
            --ink-soft: #5F6B74;
            --card-bg: #F8F9FA;
            --card-border: rgba(15, 23, 42, 0.08);
        }
        html, body, [class*="css"] {
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI",
                         "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif;
        }
        h1, h2, h3 {
            font-weight: 700;
            letter-spacing: -0.01em;
            color: var(--ink);
            margin-top: 0.6rem;
            margin-bottom: 0.3rem;
        }
        p, li, .stMarkdown {
            color: var(--ink-soft);
            line-height: 1.6;
        }
        hr {
            margin: 1.4rem 0;
            border-color: rgba(15, 23, 42, 0.06);
        }

        /* ボタン: primary/secondaryを明確に描き分ける */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.15s ease;
        }
        .stButton > button[kind="primary"] {
            background-color: var(--accent);
            border: 1px solid var(--accent);
            box-shadow: 0 1px 2px rgba(46, 156, 156, 0.25);
        }
        .stButton > button[kind="primary"]:hover {
            background-color: var(--accent-dark);
            border-color: var(--accent-dark);
            box-shadow: 0 2px 10px rgba(46, 156, 156, 0.35);
        }
        .stButton > button[kind="secondary"] {
            background-color: #F1F3F5;
            border: 1px solid transparent;
            color: var(--ink-soft);
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #E9ECEF;
            color: var(--ink);
        }

        /* カード: 面として浮かせて立体感を出す */
        div[data-testid="stForm"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
            border: 1px solid var(--card-border) !important;
            background-color: var(--card-bg) !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03), 0 1px 10px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stForm"] {
            padding: 1.4rem;
        }

        /* 入力欄: カード背景に馴染ませつつ、フォーカス時にアクセントを効かせる */
        .stTextInput input, .stTextArea textarea, .stNumberInput input,
        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid rgba(15, 23, 42, 0.10) !important;
            border-radius: 8px !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(46, 156, 156, 0.15) !important;
        }

        div[data-testid="stMetricValue"] {
            color: var(--accent-dark);
        }
        /* アラート: 種類ごとに色分けを保ちつつ、角丸で統一する */
        div[data-testid="stAlertContainer"] {
            border-radius: 10px;
            border: 1px solid var(--card-border);
        }
        div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentError"]) {
            background-color: #FDEDEC;
            border-color: rgba(217, 48, 37, 0.25);
        }
        div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentWarning"]) {
            background-color: #FDF3E0;
            border-color: rgba(242, 169, 0, 0.3);
        }
        div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentSuccess"]) {
            background-color: #E6F4EA;
            border-color: rgba(52, 168, 83, 0.3);
        }
        div[data-testid="stAlertContainer"]:has(div[data-testid="stAlertContentInfo"]) {
            background-color: var(--card-bg);
            color: var(--ink-soft);
        }

        /* サイドバーナビゲーション */
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNavLink"] {
            border-radius: 8px !important;
            transition: background-color 0.15s ease;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNavLink"][aria-current="page"] {
            background-color: rgba(46, 156, 156, 0.10) !important;
            color: var(--ink) !important;
            font-weight: 600;
        }
        [data-testid="stSidebar"] {
            background-color: #FBFCFD;
            border-right: 1px solid rgba(15, 23, 42, 0.05);
        }

        /* スピナー: 浮かせたピル型に */
        div[data-testid="stSpinner"] {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 0.5rem 1rem;
        }

        .hero-banner {
            transition: transform 0.5s ease;
        }
        .hero-banner:hover {
            transform: scale(1.01);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


_BADGE_COLORS = {
    "info": ("#EEF2F5", "#55636B", "#8A97A0"),
    "success": ("#E6F4EA", "#1E7E34", "#34A853"),
    "warning": ("#FDF3E0", "#A15C00", "#F2A900"),
}


def render_badge(text: str, kind: str = "info"):
    """ドット付きの小さなステータスバッジを表示する（kind: info / success / warning）"""
    bg, fg, dot = _BADGE_COLORS.get(kind, _BADGE_COLORS["info"])
    st.markdown(
        f"""
        <span style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: {bg};
            color: {fg};
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        ">
            <span style="width: 6px; height: 6px; border-radius: 50%; background-color: {dot};"></span>
            {text}
        </span>
        """,
        unsafe_allow_html=True,
    )


def render_hero(illust_name: str, title: str, subtitle: str = "", height: int = 300):
    """ページ上部に写真フルサイズ・タイトルオーバーレイ型のヒーローバナーを表示する"""
    b64 = _image_b64(illust_path(illust_name))
    st.markdown(
        f"""
        <div class="hero-banner" style="
            position: relative;
            width: 100%;
            height: {height}px;
            border-radius: 14px;
            overflow: hidden;
            background-image: linear-gradient(to top, rgba(10,14,17,0.70), rgba(10,14,17,0.05) 55%),
                               url('data:image/png;base64,{b64}');
            background-size: cover;
            background-position: center;
            margin-bottom: 1.4rem;
        ">
            <div style="
                position: absolute;
                left: 1.8rem;
                bottom: 1.4rem;
                right: 1.8rem;
                color: white;
            ">
                <div style="
                    font-weight: 700;
                    font-size: 1.9rem;
                    letter-spacing: -0.01em;
                    text-shadow: 0 2px 12px rgba(0,0,0,0.4);
                ">{title}</div>
                <div style="
                    font-size: 0.92rem;
                    margin-top: 0.3rem;
                    opacity: 0.9;
                    text-shadow: 0 1px 8px rgba(0,0,0,0.4);
                ">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
