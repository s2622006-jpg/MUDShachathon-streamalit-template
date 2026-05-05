import streamlit as st

st.set_page_config(
    page_title="Hackathon App",
    page_icon="🚀",
)

st.title("🚀 Hackathon Streamlit Template")
st.write("左のサイドバーからページを選んでください！")

st.markdown("""
    ## このテンプレートでできること
    - 📊 **グラフページ** : データの可視化サンプル
    - 📝 **フォームページ** : 入力フォームのサンプル
    - 🗄️ **データベースページ** : SQLiteを使ったデータ保存サンプル
    - 🌐 **APIページ** : 外部API連携サンプル
    - 🔐 **認証ページ** : ログイン機能サンプル
    - 📁 **アップロードページ** : ファイルアップロードサンプル
    """)
