"""Google Mapsで移動時間・営業時間を取得するモジュール

GOOGLE_MAPS_API_KEY が secrets.toml に設定されていない間は、
2地点の直線距離から移動時間を概算するダミー実装で動作する。
APIキーを設定すれば、自動的に実際のGoogle Maps API（Distance Matrix / Places）を使う。

注意: Google Maps Platform の Directions API / Distance Matrix API / Routes API は
日本国内の公共交通機関（TRANSIT）データを提供していない（Google公式ドキュメントに明記された
国別カバレッジ制限）。そのためtransitモードではAPIを呼ばず、最初から直線距離による概算/直線描画に
フォールバックする（無駄なAPI呼び出し・課金を避けるため）。
"""

import math

import googlemaps
import googlemaps.convert
import requests
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

# Routes API (v2) の computeRoutes エンドポイント
# 参考: https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRoutes
ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

# get_travel_time_minutes/get_route_path内部で使うmode → Routes APIのtravelModeへの変換
ROUTES_TRAVEL_MODE_MAP = {
    "driving": "DRIVE",
    "transit": "TRANSIT",
    "walking": "WALK",
    "bicycling": "BICYCLE",
}

# ダミー計算で使う移動手段別の平均速度(km/h)
DUMMY_SPEED_KMH = {
    "driving": 30,
    "transit": 25,
    "walking": 4,
    "bicycling": 15,
}


def transport_to_mode(transport: str | None) -> str:
    """「レンタカー」などの日本語表記をGoogle Mapsのmodeに変換する"""
    for key, mode in TRANSPORT_MODE_MAP.items():
        if transport and key in transport:
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

    # 日本国内はtransitモードのデータをGoogle Maps Platformが提供していないため、
    # 呼び出しても常にZERO_RESULTSになる。無駄なAPI呼び出しを避けるため最初からスキップする。
    if is_available() and mode != "transit":
        client = _get_client()
        result = client.distance_matrix(
            origins=[(origin_lat, origin_lng)],
            destinations=[(dest_lat, dest_lng)],
            mode=mode,
        )
        element = result["rows"][0]["elements"][0]
        if element["status"] == "OK":
            return {"minutes": round(element["duration"]["value"] / 60), "is_estimated": False}

    # APIキー未設定・transitモード・取得失敗時: 直線距離から概算
    distance_km = _haversine_km(origin_lat, origin_lng, dest_lat, dest_lng)
    speed = DUMMY_SPEED_KMH.get(mode, 30)
    minutes = round((distance_km / speed) * 60)
    return {"minutes": max(minutes, 1), "is_estimated": True}


@st.cache_data(show_spinner=False)
def get_route_path(
    origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, transport: str
) -> list[tuple[float, float]] | None:
    """2地点間の道路に沿った経路（緯度経度のリスト）を取得する（Routes APIを使用）

    Google Maps未設定、または経路が見つからない場合は None を返す。
    呼び出し側は None の場合、2地点を直線で結ぶフォールバックを行うこと。
    """
    mode = transport_to_mode(transport)

    # 日本国内はtransitモードのルートデータをGoogle Maps Platformが提供していないため、
    # 呼び出しても常に経路0件になる。無駄なAPI呼び出しを避けるため最初からスキップする。
    if not is_available() or mode == "transit":
        return None

    travel_mode = ROUTES_TRAVEL_MODE_MAP.get(mode, "DRIVE")

    response = requests.post(
        ROUTES_API_URL,
        json={
            "origin": {"location": {"latLng": {"latitude": origin_lat, "longitude": origin_lng}}},
            "destination": {"location": {"latLng": {"latitude": dest_lat, "longitude": dest_lng}}},
            "travelMode": travel_mode,
        },
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": st.secrets["GOOGLE_MAPS_API_KEY"],
            "X-Goog-FieldMask": "routes.polyline.encodedPolyline",
        },
        timeout=10,
    )
    if response.status_code != 200:
        return None

    routes = response.json().get("routes", [])
    if not routes:
        return None

    encoded_polyline = routes[0]["polyline"]["encodedPolyline"]
    points = googlemaps.convert.decode_polyline(encoded_polyline)
    return [(p["lat"], p["lng"]) for p in points]


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
