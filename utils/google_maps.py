"""Google Mapsで移動時間・営業時間を取得するモジュール

GOOGLE_MAPS_API_KEY が secrets.toml に設定されていない間は、
2地点の直線距離から移動時間を概算するダミー実装で動作する。
APIキーを設定すれば、自動的に実際のGoogle Maps API（Distance Matrix / Places）を使う。
"""

import math

import googlemaps
import streamlit as st

# 移動手段の日本語表記 → Google Maps APIのmodeへの変換
TRANSPORT_MODE_MAP = {
    "レンタカー": "driving",
    "車": "driving",
    "公共交通機関": "transit",
    "電車": "transit",
    "バス": "transit",
    "徒歩": "walking",
    "自転車": "bicycling",
}

# ダミー計算で使う移動手段別の平均速度(km/h)
DUMMY_SPEED_KMH = {
    "driving": 30,
    "transit": 25,
    "walking": 4,
    "bicycling": 15,
}


def transport_to_mode(transport: str) -> str:
    """「レンタカー」などの日本語表記をGoogle Mapsのmodeに変換する"""
    for key, mode in TRANSPORT_MODE_MAP.items():
        if key in transport:
            return mode
    return "driving"


def is_available() -> bool:
    """Google Maps APIキーが設定されているか"""
    api_key = st.secrets.get("GOOGLE_MAPS_API_KEY", "")
    return bool(api_key)


def _get_client() -> googlemaps.Client:
    return googlemaps.Client(key=st.secrets["GOOGLE_MAPS_API_KEY"])


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """2地点間の直線距離(km)を計算する"""
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def get_travel_time_minutes(
    origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, transport: str
) -> dict:
    """2地点間の移動時間(分)を取得する

    戻り値: {"minutes": int, "is_estimated": bool}
    is_estimated=True の場合は、APIキー未設定によるダミー概算値。
    """
    mode = transport_to_mode(transport)

    if is_available():
        client = _get_client()
        result = client.distance_matrix(
            origins=[(origin_lat, origin_lng)],
            destinations=[(dest_lat, dest_lng)],
            mode=mode,
        )
        element = result["rows"][0]["elements"][0]
        if element["status"] == "OK":
            return {"minutes": round(element["duration"]["value"] / 60), "is_estimated": False}

    # APIキー未設定 or 取得失敗時: 直線距離から概算
    distance_km = _haversine_km(origin_lat, origin_lng, dest_lat, dest_lng)
    speed = DUMMY_SPEED_KMH.get(mode, 30)
    minutes = round((distance_km / speed) * 60)
    return {"minutes": max(minutes, 1), "is_estimated": True}


def get_opening_hours(place_name: str, lat: float, lng: float) -> dict:
    """スポットの営業時間情報を取得する

    戻り値: {"text": str, "is_estimated": bool}
    """
    if is_available():
        client = _get_client()
        found = client.find_place(
            input=place_name,
            input_type="textquery",
            location_bias=f"point:{lat},{lng}",
            fields=["place_id"],
        )
        candidates = found.get("candidates", [])
        if candidates:
            place_id = candidates[0]["place_id"]
            details = client.place(place_id=place_id, fields=["opening_hours"])
            hours = details.get("result", {}).get("opening_hours", {}).get("weekday_text")
            if hours:
                return {"text": "\n".join(hours), "is_estimated": False}

    return {"text": "営業時間情報は取得できませんでした（Google Maps API未設定）", "is_estimated": True}
