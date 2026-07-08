"""旅行プラン生成の司令塔モジュール

質問の回答(answers)を受け取り、
DBのおすすめスポット検索 → Geminiでのプラン生成 → Google Mapsでの移動時間補完
までを一気通貫で行う generate_plan() を提供する。
"""

from utils.database import init_spots_db, search_spots
from utils.gemini_client import generate_travel_plan
from utils.google_maps import get_travel_time_minutes


def _collect_candidate_spots(answers: dict) -> list[dict]:
    """AIへの参考情報として渡すおすすめスポットをDBから集める"""
    init_spots_db()

    purposes = answers.get("purposes", [])
    departure = answers.get("departure", "")

    # まず出発地点のエリアで絞り込み、目的カテゴリに合うスポットを探す
    spots = search_spots(categories=purposes, area=departure)

    # 出発地点に合致するスポットが無ければ、エリア指定なしで目的カテゴリのみで探す
    if not spots:
        spots = search_spots(categories=purposes, area=None)

    return spots


def _has_coordinates(spot: dict) -> bool:
    return all(spot.get(k) is not None for k in ("latitude", "longitude"))


def _enrich_with_travel_times(plan: dict, transport: str) -> dict:
    """プラン内の各スポット間(同じ日どうし)の移動時間をGoogle Mapsで補完する"""
    is_any_estimated = False
    spots = plan.get("spots", [])

    for i in range(len(spots) - 1):
        current = spots[i]
        nxt = spots[i + 1]

        # dayが異なる場合は日をまたぐので移動時間を計算しない
        if current.get("day", 1) != nxt.get("day", 1):
            continue
        if not _has_coordinates(current) or not _has_coordinates(nxt):
            continue

        travel = get_travel_time_minutes(
            current["latitude"], current["longitude"], nxt["latitude"], nxt["longitude"], transport
        )
        current["travel_time_to_next_minutes"] = travel["minutes"]
        if travel["is_estimated"]:
            is_any_estimated = True

    plan["travel_times_are_estimated"] = is_any_estimated
    return plan


def generate_plan(answers: dict) -> dict:
    """質問の回答から旅行プランを生成する

    answers: {
        "budget": int,
        "num_people": int,
        "purposes": list[str],   # ["nature", "gourmet"] など2つ
        "transport": str,
        "departure": str,
        "pace": str,
        "days": int,
    }
    戻り値: gemini_client.PLAN_RESPONSE_SCHEMA に沿ったdict
            {"title": str, "summary": str, "spots": [...], "total_estimated_cost": int, "tips": [...]}
            spots の各要素は {"day", "time", "name", "description", "latitude", "longitude",
            "category", "duration_minutes", "estimated_cost", "transport_to_next"} を持つ。
            さらに同日内で travel_time_to_next_minutes を付加し、
            plan["travel_times_are_estimated"] にダミー値使用の有無を格納する。
    """
    candidate_spots = _collect_candidate_spots(answers)
    plan = generate_travel_plan(answers, candidate_spots)
    plan = _enrich_with_travel_times(plan, answers.get("transport", ""))
    return plan
