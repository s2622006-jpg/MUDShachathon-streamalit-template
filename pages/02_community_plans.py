import streamlit as st

from utils.database import add_comment, get_all_plans, get_comments, get_plan, init_plans_db
from utils.plan_view import render_plan
from utils.ui import render_hero

init_plans_db()

render_hero(
    "illust_tropical_beach",
    "みんなの旅行プラン",
    "他の人が作成・公開した旅行プランを閲覧してコメントできます。",
)

plans = get_all_plans()

if not plans:
    st.caption("まだ公開されたプランがありません。「プランを作成」ページでプランを作成して公開してみましょう。")
else:
    if "selected_plan_id" not in st.session_state:
        st.session_state["selected_plan_id"] = plans[0]["id"]

    st.caption("プラン一覧")
    for p in plans:
        with st.container(border=True):
            cols = st.columns([4, 2, 2, 1])
            with cols[0]:
                st.write(f"**{p['title']}**")
                st.caption(p.get("summary", ""))
            with cols[1]:
                st.write(f"投稿者: {p['author_name']}")
                st.caption(p["created_at"])
            with cols[2]:
                st.write(f"{p.get('total_estimated_cost', 0):,} 円")
            with cols[3]:
                if st.button("見る", key=f"view_{p['id']}", icon=":material/visibility:"):
                    st.session_state["selected_plan_id"] = p["id"]
                    st.rerun()

    selected_id = st.session_state["selected_plan_id"]
    detail = get_plan(selected_id)

    if detail:
        st.divider()
        st.caption(f"投稿者: {detail['author_name']} ・ {detail['created_at']}")
        render_plan(detail["plan"], map_key=f"community_map_{selected_id}")

        st.divider()
        st.caption("コメント")
        comments = get_comments(selected_id)
        if not comments:
            st.caption("まだコメントはありません。最初のコメントを投稿してみましょう。")
        for c in comments:
            with st.container(border=True):
                st.write(f"**{c['author_name']}** ・ {c['created_at']}")
                st.write(c["comment"])

        with st.container(border=True):
            comment_author = st.text_input("表示名", key=f"comment_author_{selected_id}")
            comment_text = st.text_area("コメント", key=f"comment_text_{selected_id}")
            if st.button(
                "コメントを投稿する",
                key=f"comment_submit_{selected_id}",
                type="primary",
                icon=":material/send:",
            ):
                if not comment_author or not comment_text:
                    st.error("表示名とコメントを入力してください。")
                else:
                    add_comment(selected_id, comment_author, comment_text)
                    st.rerun()
