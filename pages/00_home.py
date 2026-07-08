import streamlit as st

from utils.ui import render_hero

render_hero(
    "illust_santorini",
    "旅行プラン自動作成アプリ",
    "左のメニューの「プランを作成」から始めてください。",
    height=380,
)

st.subheader("このアプリでできること")

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.markdown(":material/quiz: **6つの質問に答えるだけ**")
        st.caption("予算・人数・目的・移動手段・出発地点・旅行のペースを答えるだけでOK。")
with col2:
    with st.container(border=True):
        st.markdown(":material/auto_awesome: **AIがプランを自動作成**")
        st.caption("Gemini がおすすめスポットデータベースを参考にプランを組み立てます。")
with col3:
    with st.container(border=True):
        st.markdown(":material/map: **地図とルートを確認**")
        st.caption("Google Maps の情報をもとに、移動時間つきで地図上に表示します。")
