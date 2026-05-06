import streamlit as st
from utils.auth import login, logout

st.title("🔐 ログイン機能サンプル")

if not login():
    st.stop()  # 未ログインならここで止める

# ─ ログイン後の画面 ──────────────────────────────────
st.success(f"ようこそ、{st.session_state.username}さん！")
st.write("このエリアはログインしないと見れません。")

if st.button("ログアウト"):
    logout()
