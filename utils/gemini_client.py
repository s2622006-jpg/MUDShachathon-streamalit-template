"""Gemini APIを使って旅行プランを生成するモジュール

流れ:
    1. build_prompt() で質問の回答とDBのおすすめスポットから指示文を組み立てる
    2. generate_travel_plan() でGeminiにプロンプトを投げ、JSONでプランを受け取る
"""

import json

import streamlit as st
from google import genai
from google.genai import types

MODEL_NAME = "gemini-2.5-flash"

# Geminiに厳密にこの形のJSONを返させるためのスキーマ
# spots はフラットな配列（time順）。複数日プランの場合のみ day(1始まり)を付与する。
PLAN_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "旅行プラン全体のタイトル"},
        "summary": {"type": "string", "description": "プラン全体の概要（2〜3文）"},
        "spots": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer", "description": "何日目か（1始まり。1日プランなら1）"},
                    "time": {"type": "string", "description": "開始予定時刻 例: 09:00"},
                    "name": {"type": "string", "description": "スポット名・食事名など"},
                    "description": {"type": "string", "description": "内容の説明（1〜2文）"},
                    "latitude": {"type": "number", "description": "緯度"},
                    "longitude": {"type": "number", "description": "経度"},
                    "category": {
                        "type": "string",
                        "enum": ["nature", "gourmet", "adventure", "culture", "move", "other"],
                    },
                    "duration_minutes": {"type": "integer", "description": "滞在目安時間(分)"},
                    "estimated_cost": {"type": "integer", "description": "目安費用(円/人)"},
                    "transport_to_next": {
                        "type": "string",
                        "description": "次の場所への移動手段",
                    },
                },
                "required": ["day", "time", "name", "description", "latitude", "longitude"],
            },
        },
        "total_estimated_cost": {"type": "integer", "description": "1人あたりの合計目安費用(円)"},
        "tips": {
            "type": "array",
            "items": {"type": "string"},
            "description": "持ち物・注意点などのアドバイス",
        },
    },
    "required": ["title", "summary", "spots", "total_estimated_cost"],
}

PURPOSE_LABELS = {
    "nature": "自然を堪能したい",
    "gourmet": "グルメを楽しみたい",
    "adventure": "刺激を求めたい",
    "culture": "文化を感じたい",
}


def _get_api_key() -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key or api_key == "your-gemini-api-key":
        raise RuntimeError(
            ".streamlit/secrets.toml の GEMINI_API_KEY が未設定です。"
            "Gemini APIキーを設定してください。"
        )
    return api_key


def build_prompt(answers: dict, candidate_spots: list[dict]) -> str:
    """質問の回答とDBのおすすめスポットから、Geminiへの指示文を組み立てる"""
    purpose_text = "・".join(PURPOSE_LABELS.get(p, p) for p in answers.get("purposes", []))

    if candidate_spots:
        spots_text = "\n".join(
            f"- {s['name']}（{s['category']} / {s['area']} / 緯度経度: {s['lat']},{s['lng']} / "
            f"目安滞在時間: {s.get('typical_duration_minutes', 60)}分 / {s.get('description', '')}）"
            for s in candidate_spots
        )
    else:
        spots_text = "（該当する登録スポットなし。あなたの知識で提案してください）"

    prompt = f"""あなたは旅行プランナーです。以下の条件に合う旅行プランを作成してください。

# 旅行者の条件
- 予算: 1人あたり {answers.get("budget")} 円
- 人数: {answers.get("num_people")} 人
- 旅行の目的: {purpose_text}
- 主な移動手段: {answers.get("transport")}
- 出発地点: {answers.get("departure")} 🔴（駅名や施設名など、この具体的な場所からスタートするルートを組んでください）
- 旅行予定の地方: {answers.get("region", "指定なし")} 🔴 修正：指定された地方内の観光地を中心に選定してください
- 旅行日数: {answers.get("days", 1)} 日
- 旅行のペース: {answers.get("pace")}（のんびりしたい場合は詰め込みすぎない、予定を詰めたい場合は多めにスポットを入れる）
- 移動時間の希望: {answers.get("long_travel", "あまり気にしない")}

# 参考: おすすめスポット（データベースより。可能な限りこの中から選んでください。緯度経度も正確に引用すること）
{spots_text}

# 出力ルール
- 必ず指定された旅行予定の地方（{answers.get("region", "指定なし")}）に準じたプランを作成すること
- 提示された具体的な出発地点（{answers.get("departure")}）から、選択された移動手段（{answers.get("transport")}）を使って現実的に移動しやすい範囲・順序・時間配分でルートを構成すること
- 移動時間の希望（{answers.get("long_travel", "あまり気にしない")}）を考慮し、「短時間がいい」と言われた場合は移動時間を短く近場でまとめ、「長時間でもOK」と言われた場合は少し遠出のスポットも含めてルートを構成すること
- 予算の大体60~100%のプランを考えること。ただし、どうしても厳しい場合はおすすめのお土産を紹介しこれを達成してください。
- spots は訪問順（時刻順）に並べたフラットな配列にすること。旅行日数が2日以上の場合は、各要素の day に何日目かを1始まりで入れること。1日プランなら全要素 day=1 とすること
- 各スポットには必ず正確な緯度(latitude)と経度(longitude)を含めること。地図表示に使うため絶対に省略しないこと（参考スポットにあるものはその値をそのまま使い、独自提案する場合は実在する正確な緯度経度を入れること）
- 予算内に収まるよう total_estimated_cost を調整すること
- 出力は指定されたJSONスキーマに厳密に従うこと
"""
    return prompt


def generate_travel_plan(answers: dict, candidate_spots: list[dict]) -> dict:
    """Gemini APIを呼び出し、旅行プランをdict(JSON)で返す"""
    prompt = build_prompt(answers, candidate_spots)

    client = genai.Client(api_key=_get_api_key())
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PLAN_RESPONSE_SCHEMA,
            temperature=0.7,
        ),
    )

    return json.loads(response.text)


# ⭕️ 追加：フロントエンド（01_travel_plan.py）からの呼び出し名を一致させるための仲介関数
def generate_plan(answers: dict) -> dict:
    """フロントエンドの単一引数(answers)による呼び出しを
    このモジュールの generate_travel_plan に繋ぐためのラッパー関数
    """
    # 必要に応じてDBからおすすめスポットを検索するロジック（なければ空リスト）を入れる
    # 現状は空リストを渡してGemini自身の知識でフル生成させます
    candidate_spots = []
    return generate_travel_plan(answers, candidate_spots)