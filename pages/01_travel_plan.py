import streamlit as st

from utils.database import init_plans_db, save_plan
from utils.google_maps import is_available as maps_is_available
from utils.plan_view import render_plan
from utils.travel_plan import generate_plan

st.set_page_config(page_title="旅行プラン自動作成", page_icon="🧳")

init_plans_db()

st.title("🧳 旅行プラン自動作成")
st.write("6つの質問に答えると、AIが旅行プランを自動作成します。")

PURPOSE_OPTIONS = {
    "nature": "自然を堪能したい",
    "gourmet": "グルメを楽しみたい",
    "adventure": "刺激を求めたい",
    "culture": "文化を感じたい",
}

if not maps_is_available():
    st.info(
        "ℹ️ Google Maps APIキーが未設定のため、移動時間・営業時間は概算値（ダミー）で表示されます。",
        icon="ℹ️",
    )

with st.form("travel_plan_form"):
    st.subheader("質問1: 予算（1人あたり）")
    budget = st.number_input("円", min_value=0, value=50000, step=5000)

    st.subheader("質問2: 人数")
    num_people = st.number_input("人", min_value=1, value=2, step=1)

    st.subheader("質問3: なんとなくの目的（2つ選択）")
    purposes_labels = st.multiselect(
        "目的を2つ選んでください",
        options=list(PURPOSE_OPTIONS.values()),
        max_selections=2,
    )

    st.subheader("質問4: 主な移動手段")
    transport_choice = st.selectbox(
        "移動手段",
        ["レンタカー", "公共交通機関", "徒歩・自転車", "その他"],
    )
    if transport_choice == "その他":
        transport_choice = st.text_input("移動手段を入力してください", value="徒歩")

    st.subheader("質問5: 出発地点")
    departure = st.text_input("出発地点（例: 東京、大阪 など）", value="東京")

    st.subheader("旅行日数")
    days = st.number_input("日数", min_value=1, max_value=7, value=1, step=1)

    st.subheader("質問6: 旅行のペース")
    pace = st.radio("ペース", ["のんびり旅行したい", "予定を詰め込みたい"])

    submitted = st.form_submit_button("プランを作成する")

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

    st.divider()
    st.subheader("📢 このプランをみんなに公開する")
    if st.session_state.get("travel_plan_saved_id"):
        st.success("このプランは公開済みです。「みんなのプラン」ページから見られます。")
    else:
        author_name = st.text_input("表示名（ニックネームでOK）", key="author_name_input")
        if st.button("プランを公開する"):
            if not author_name:
                st.error("表示名を入力してください。")
            else:
                plan_id = save_plan(author_name, plan, st.session_state.get("travel_plan_answers", {}))
                st.session_state["travel_plan_saved_id"] = plan_id
                st.rerun()
