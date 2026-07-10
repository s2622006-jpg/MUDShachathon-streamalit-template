"""旅行プランをStreamlit上に表示する共通ロジック

pages/01_travel_plan.py（新規生成したプランの表示）と
pages/02_community_plans.py（みんなのプランの閲覧）の両方から使う。
"""

from itertools import groupby

import folium
import streamlit as st
from streamlit_folium import st_folium

from utils.google_maps import get_route_path
from utils.ui import category_icon_path, render_badge

DAY_COLORS = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue"]


def _render_day_spots(day_num: int, day_spots: list[dict], color: str, fmap: folium.Map) -> list[tuple]:
    """1日分のスポット一覧をカード内に描画し、地図用の座標リストを返す"""
    day_points = []
    transports = []
    with st.container(border=True):
        for spot in day_spots:
            cols = st.columns([1, 1, 3, 1])
            with cols[0]:
                st.write(f"**{spot.get('time', '')}**")
            with cols[1]:
                st.image(category_icon_path(spot.get("category", "other")), width=32)
            with cols[2]:
                st.write(f"**{spot.get('name', '')}**")
                st.caption(spot.get("description", ""))
            with cols[3]:
                st.write(f"{spot.get('estimated_cost', 0):,} 円")

            travel_minutes = spot.get("travel_time_to_next_minutes")
            if travel_minutes is not None:
                st.caption(f"次の場所まで {spot.get('transport_to_next', '')} で 約{travel_minutes}分")

            if spot.get("latitude") is not None and spot.get("longitude") is not None:
                point = (spot["latitude"], spot["longitude"])
                day_points.append(point)
                transports.append(spot.get("transport_to_next", ""))
                folium.Marker(
                    location=point,
                    popup=f"{day_num}日目: {spot.get('name', '')}",
                    tooltip=spot.get("name", ""),
                    icon=folium.Icon(color=color),
                ).add_to(fmap)

    # 隣接スポット間を、道路に沿った経路（取得できない場合は直線）で結ぶ
    for i in range(len(day_points) - 1):
        origin, dest = day_points[i], day_points[i + 1]
        path = get_route_path(origin[0], origin[1], dest[0], dest[1], transports[i])
        folium.PolyLine(path or [origin, dest], color=color, weight=3, opacity=0.7).add_to(fmap)

    return day_points


def render_plan(plan: dict, map_key: str):
    """プランの中身（概要・スケジュール・地図・アドバイス）を表示する

    map_key: st_folium に渡す一意なキー（同じページに複数の地図を出す場合の衝突回避用）
    """
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header(plan.get("title", "旅行プラン"))
            st.write(plan.get("summary", ""))
        with col2:
            st.metric("合計目安費用（1人あたり）", f"{plan.get('total_estimated_cost', 0):,} 円")
        if plan.get("travel_times_are_estimated"):
            render_badge("移動時間は概算値", kind="warning")

    all_points = []
    fmap = folium.Map(location=[35.6812, 139.7671], zoom_start=6)
    spots = plan.get("spots", [])
    days = [(day_num, list(day_spots)) for day_num, day_spots in groupby(spots, key=lambda s: s.get("day", 1))]

    if len(days) > 1:
        tabs = st.tabs([f"{day_num}日目" for day_num, _ in days])
        for tab, (day_num, day_spots) in zip(tabs, days):
            color = DAY_COLORS[(day_num - 1) % len(DAY_COLORS)]
            with tab:
                all_points.extend(_render_day_spots(day_num, day_spots, color, fmap))
    else:
        for day_num, day_spots in days:
            color = DAY_COLORS[(day_num - 1) % len(DAY_COLORS)]
            all_points.extend(_render_day_spots(day_num, day_spots, color, fmap))

    if all_points:
        fmap.fit_bounds(all_points)

    st.caption("プランの地図")
    st_folium(fmap, width=700, height=500, key=map_key)

    tips = plan.get("tips", [])
    if tips:
        with st.container(border=True):
            st.caption("アドバイス")
            for tip in tips:
                st.write(f"- {tip}")
