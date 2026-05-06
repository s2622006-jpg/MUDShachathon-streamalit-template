import streamlit as st
from utils.database import init_db, insert_message, get_all_messages

# 起動時にテーブルを初期化
init_db()

st.title("🗄️ データベースサンプル")
st.write("入力したメッセージを SQLite に保存・表示するサンプル")

# ── 入力フォーム ──────────────────────────────────
st.subheader("メッセージを投稿する")
name = st.text_input("名前")
message = st.text_area("メッセージ")

if st.button("投稿"):
    if not name or not message:
        st.error("名前とメッセージを入力してください")
    else:
        insert_message(name, message)
        st.success("投稿しました！")


# ── 投稿一覧 ──────────────────────────────────
st.subheader("投稿一覧")
rows = get_all_messages()

if not rows:
    st.info("まだ投稿がありません")
else:
    for row in rows:
        st.markdown(f"**{row['name']}** - {row['created_at']}")
        st.write(row["message"])
        st.divider()
