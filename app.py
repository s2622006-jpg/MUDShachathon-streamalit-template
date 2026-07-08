import streamlit as st

st.set_page_config(
    page_title="旅行プラン自動作成",
    page_icon="🧳",
)

st.title("🧳 旅行プラン自動作成アプリ")
st.write("左のサイドバーの「travel plan」からプラン作成に進んでください。")

st.markdown("""
    ## このアプリでできること
    予算・人数・目的・移動手段・出発地点・旅行のペースを答えるだけで、
    AI（Gemini）が旅行プランを自動作成します。
    プランはおすすめスポットデータベースとGoogle Mapsの情報を参考に組み立てられ、
    地図上でも確認できます。
    """)
