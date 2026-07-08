"""旅行プランをStreamlit上に表示する共通ロジック

pages/01_travel_plan.py（新規生成したプランの表示）と
pages/02_community_plans.py（みんなのプランの閲覧）の両方から使う。
"""

from itertools import groupby

import folium
import streamlit as st
from streamlit_folium import st_folium

DAY_COLORS = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue"]


def render_plan(plan: dict, map_key: str):
    """プランの中身（概要・スケジュール・地図・アドバイス）を表示する

    map_key: st_folium に渡す一意なキー（同じページに複数の地図を出す場合の衝突回避用）
    """
    st.header(plan.get("title", "旅行プラン"))
    st.write(plan.get("summary", ""))
    st.metric("合計目安費用（1人あたり）", f"{plan.get('total_estimated_cost', 0):,} 円")

    if plan.get("travel_times_are_estimated"):
        st.caption("※移動時間はGoogle Maps APIが未設定のため概算値です")

    all_points = []
    fmap = folium.Map(location=[35.6812, 139.7671], zoom_start=6)
    spots = plan.get("spots", [])

    for day_num, day_spots in groupby(spots, key=lambda s: s.get("day", 1)):
        day_spots = list(day_spots)
        color = DAY_COLORS[(day_num - 1) % len(DAY_COLORS)]

        st.subheader(f"{day_num}日目")

        day_points = []
        for spot in day_spots:
            cols = st.columns([1, 3, 1])
            with cols[0]:
                st.write(f"**{spot.get('time', '')}**")
            with cols[1]:
                st.write(f"**{spot.get('name', '')}**")
                st.caption(spot.get("description", ""))
            with cols[2]:
                st.write(f"{spot.get('estimated_cost', 0):,} 円")

            travel_minutes = spot.get("travel_time_to_next_minutes")
            if travel_minutes is not None:
                st.caption(f"→ 次の場所まで {spot.get('transport_to_next', '')} で 約{travel_minutes}分")

            if spot.get("latitude") is not None and spot.get("longitude") is not None:
                point = (spot["latitude"], spot["longitude"])
                day_points.append(point)
                all_points.append(point)
                folium.Marker(
                    location=point,
                    popup=f"{day_num}日目: {spot.get('name', '')}",
                    tooltip=spot.get("name", ""),
                    icon=folium.Icon(color=color),
                ).add_to(fmap)

        if len(day_points) >= 2:
            folium.PolyLine(day_points, color=color, weight=3, opacity=0.7).add_to(fmap)

        st.divider()

    if all_points:
        fmap.fit_bounds(all_points)

    st.subheader("🗺️ プランの地図")
    st_folium(fmap, width=700, height=500, key=map_key)

    tips = plan.get("tips", [])
    if tips:
        st.subheader("💡 アドバイス")
        for tip in tips:
            st.write(f"- {tip}")
