import streamlit as st

from utils.database import init_plans_db, save_plan
from utils.google_maps import is_available as maps_is_available
from utils.plan_view import render_plan
from utils.travel_plan import generate_plan
from utils.ui import category_icon_path, render_badge, render_hero

init_plans_db()

render_hero(
    "illust_ferris_wheel_city",
    "旅行プラン自動作成",
    "6つの質問に答えると、AIが旅行プランを自動作成します。",
)

PURPOSE_OPTIONS = {
    "nature": "自然を堪能したい",
    "gourmet": "グルメを楽しみたい",
    "adventure": "刺激を求めたい",
    "culture": "文化を感じたい",
}

if not maps_is_available():
    render_badge("概算値モード（Google Maps 未接続）", kind="warning")

with st.form("travel_plan_form"):
    with st.container(border=True):
        st.caption("予算・人数")
        col1, col2 = st.columns(2)
        with col1:
            budget = st.number_input("予算（1人あたり・円）", min_value=0, value=50000, step=5000)
        with col2:
            num_people = st.number_input("人数", min_value=1, value=2, step=1)

    with st.container(border=True):
        st.caption("目的（2つ選択）")
        purpose_cols = st.columns(len(PURPOSE_OPTIONS))
        purpose_checks = {}
        for col, (key, label) in zip(purpose_cols, PURPOSE_OPTIONS.items()):
            with col:
                st.image(category_icon_path(key), width=48)
                purpose_checks[key] = st.checkbox(label, key=f"purpose_{key}")
        purposes_labels = [PURPOSE_OPTIONS[key] for key, checked in purpose_checks.items() if checked]

    with st.container(border=True):
        st.caption("移動手段・出発地・旅程")
        col1, col2 = st.columns(2)
        with col1:
            transport_choice = st.selectbox(
                "主な移動手段",
                ["レンタカー", "公共交通機関", "徒歩・自転車", "その他"],
            )
            if transport_choice == "その他":
                transport_choice = st.text_input("移動手段を入力してください", value="徒歩")
            days = st.number_input("旅行日数", min_value=1, max_value=7, value=1, step=1)
        with col2:
            departure = st.text_input("出発地点（例: 東京、大阪 など）", value="東京")
            pace = st.radio("旅行のペース", ["のんびり旅行したい", "予定を詰め込みたい"])

    submitted = st.form_submit_button("プランを作成する", type="primary", icon=":material/auto_awesome:")

if submitted:
    if len(purposes_labels) != 2:
        st.error("質問3の目的は2つ選択してください。")
    elif not departure:
        st.error("出発地点を入力してください。")
    else:
        label_to_key = {v: k for k, v in PURPOSE_OPTIONS.items()}
        answers = {
            "budget": int(budget),
            "num_people": int(num_people),
            "purposes": [label_to_key[label] for label in purposes_labels],
            "transport": transport_choice,
            "departure": departure,
            "days": int(days),
            "pace": pace,
        }
        with st.spinner("AIが旅行プランを作成しています..."):
            try:
                st.session_state["travel_plan"] = generate_plan(answers)
                st.session_state["travel_plan_answers"] = answers
                st.session_state["travel_plan_error"] = None
                st.session_state["travel_plan_saved_id"] = None
            except Exception as e:
                st.session_state["travel_plan"] = None
                st.session_state["travel_plan_error"] = str(e)

if st.session_state.get("travel_plan_error"):
    st.error(f"プラン生成でエラーが発生しました: {st.session_state['travel_plan_error']}")

plan = st.session_state.get("travel_plan")

if plan:
    st.divider()
    render_plan(plan, map_key="generated_plan_map")

    with st.container(border=True):
        st.caption("このプランをみんなに公開する")
        if st.session_state.get("travel_plan_saved_id"):
            render_badge("公開済み", kind="success")
            st.caption("「みんなのプラン」ページから見られます。")
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                author_name = st.text_input("表示名（ニックネームでOK）", key="author_name_input")
            with col2:
                st.write("")
                publish = st.button("公開する", type="primary", icon=":material/publish:")
            if publish:
                if not author_name:
                    st.error("表示名を入力してください。")
                else:
                    plan_id = save_plan(author_name, plan, st.session_state.get("travel_plan_answers", {}))
                    st.session_state["travel_plan_saved_id"] = plan_id
                    st.rerun()
