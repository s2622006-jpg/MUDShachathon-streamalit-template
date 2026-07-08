import streamlit as st

from utils.ui import apply_theme, icon_path

st.set_page_config(
    page_title="旅行プラン自動作成",
    page_icon=icon_path("logo_app_mark"),
)

apply_theme()

pages = [
    st.Page("pages/00_home.py", title="ホーム", icon=":material/home:"),
    st.Page("pages/01_travel_plan.py", title="プランを作成", icon=":material/edit_calendar:"),
    st.Page("pages/02_community_plans.py", title="みんなのプラン", icon=":material/diversity_3:"),
]
st.navigation(pages).run()
