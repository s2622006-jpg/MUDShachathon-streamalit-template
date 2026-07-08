import streamlit as st

from utils.database import init_plans_db, save_plan
from utils.google_maps import is_available as maps_is_available
from utils.plan_view import render_plan
from utils.gemini_processing import generate_plan

st.set_page_config(page_title="旅行プラン自動作成", page_icon="🧳")

init_plans_db()

st.title("🧳 旅行プラン自動作成")
st.write("8つの質問に答えると、AIが旅行プランを自動作成します。")

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

    # ⭕️ 修正：具体的な場所を入力してもらうための案内を追加
    st.subheader("質問5: 出発地点")
    st.caption("⚠️ より正確な移動ルートを計算するため、駅名や施設名など具体的な場所を入力してください。")
    departure = st.text_input(
        "出発地点（具体的な場所を入力してください）", 
        value="東京駅", 
        placeholder="例: 東京駅、梅田駅、新宿駅、自宅の最寄り駅など"
    )

    st.subheader("旅行日数")
    days = st.number_input("日数", min_value=1, max_value=7, value=1, step=1)

    st.subheader("質問6: 旅行のペース")
    pace = st.radio("ペース", ["のんびり旅行したい", "予定を詰め込みたい"])

    st.subheader("質問7: 移動時間が長くなってもいいか")
    long_travel_choice = st.selectbox(
        "移動時間の希望",
        ["長時間希望", "短時間希望", "あまり気にしない"],
    )

    st.subheader("質問8: 旅行予定の地方")
    region_choice = st.selectbox(
        "地方を選択してください",
        ["関東地方", "関西地方", "北海道", "東北地方", "中部地方", "中国・四国地方", "九州・沖縄"],
    )

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
            "long_travel": long_travel_choice,
            "region": region_choice,
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