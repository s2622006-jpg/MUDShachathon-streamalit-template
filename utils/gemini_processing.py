import json
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

# ルート階層の .env ファイルから API キーを読み込む
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path)

# Geminiに約束させるデータの設計図（スキーマ）
class Spot(BaseModel):
    day: int = Field(description="何日目か（1始まり。1日プランならすべて1）")
    time: str = Field(description="到着時間または開始時間。例: '10:00'")
    name: str = Field(description="観光スポットや飲食店の名前。実在するもの限定。")
    description: str = Field(description="そのスポットでの過ごし方やおすすめポイントの解説文。")
    latitude: float = Field(description="そのスポットの正確な緯度（数値型）")
    longitude: float = Field(description="そのスポットの正確な経度（数値型）")
    category: str = Field(description="カテゴリ。'nature', 'gourmet', 'adventure', 'culture', 'move', 'other' のいずれか")
    duration_minutes: int = Field(default=60, description="滞在目安時間(分)")
    estimated_cost: int = Field(default=0, description="1人あたりの目安費用(円)")
    transport_to_next: Optional[str] = Field(default="", description="次の場所への移動手段")

class TravelPlan(BaseModel):
    title: str = Field(description="旅行プランの魅力的なタイトル。")
    summary: str = Field(description="プラン全体の概要（2〜3文）")
    spots: List[Spot] = Field(description="タイムライン順に並んだスポットのリスト。")
    total_estimated_cost: int = Field(description="1人あたりの合計目安費用(円)")
    tips: List[str] = Field(default=[], description="持ち物・注意点などのアドバイス")

class TravelPlannerBackend:
    """旅行プランの生成ロジックを担当するバックエンドクラス"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("⚠️ バックエンドエラー: .env から GEMINI_API_KEY を読み込めませんでした。")
        self.client = genai.Client(api_key=api_key)

    # ⭕️ 修正：引数に region を追加
    def generate_plan(self, dep: str, num: int, bg: str, style: str, trans: str, days_count: str, purposes_text: str, longs_traveltime: str, region: str) -> dict:
        """フロントエンドから条件を受け取り、Geminiで旅行プラン(辞書型)を生成する関数"""
        
        # ⭕️ 修正：プロンプトを特定の地方（region）に縛るように修正し、出発地点の具体性も強調
        prompt = f"""
        以下の条件に完全に合致する、{region}限定の旅行プランを1つつくってください。
        
        【条件】
        * 旅行予定の地方: {region}
        * 出発地: {dep} （駅名や施設名などの具体的な出発地点です。必ずここから出発する現実的なルートを構成してください）
        * 旅行人数: {num}人
        * 予算の目安: {bg}円
        * 旅のスタイル: {style}
        * 旅の目的: {purposes_text}
        * 主な移動手段: {trans}
        * 旅行日数: {days_count}日間
        * 移動時間の希望: {longs_traveltime}（「短時間がいい」場合は移動距離が短い近場を提案し、「長時間でもOK」の場合は遠出も含めること）
        
        【絶対厳守の注意点】
        * 提案するスポットは、必ず指定された「{region}」の中にある実在の観光地や飲食店にしてください。
        * 各スポットの緯度(latitude)と経度(longitude)は必ず実在する正しい数値を調べて入れてください。
        * spots は訪問順（時刻順）に並べた配列にすること。旅行日数が2日以上の場合は、各要素の day に何日目かを1始まりで入れること。
        * 予算内に収まるよう total_estimated_cost や各スポットの estimated_cost を調整すること。
        """

        # Gemini APIへ通信
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                # ⭕️ 修正：システムインストラクションも日本全国の地方に対応できるように変更
                system_instruction=f"あなたは{region}をはじめ、日本全国の観光に特化したプロの旅行プランナーです。指定されたJSONスキーマに厳密に従って出力してください。",
                response_mime_type="application/json",
                response_schema=TravelPlan,
                temperature=0.7
            ),
        )
        
        return json.loads(response.text)

def generate_plan(answers: dict) -> dict:
    """フロントエンドの辞書型(answers)での呼び出しを、
    TravelPlannerBackend クラスの形式に変換して実行する仲介関数
    """
    backend = TravelPlannerBackend()
    
    PURPOSE_LABELS = {
        "nature": "自然を堪能したい",
        "gourmet": "グルメを楽しみたい",
        "adventure": "刺激を求めたい",
        "culture": "文化を感じたい",
    }
    purposes_text = "、".join(PURPOSE_LABELS.get(p, p) for p in answers.get("purposes", []))
    
    # ⭕️ 修正：クラス側のメソッドに region を渡すように連携
    return backend.generate_plan(
        dep=answers.get("departure", "東京駅"),
        num=answers.get("num_people", 2),
        bg=str(answers.get("budget", 50000)),
        style=answers.get("pace", "のんびり旅行したい"),
        trans=answers.get("transport", "レンタカー"),
        days_count=str(answers.get("days", 1)),
        purposes_text=purposes_text,
        longs_traveltime=answers.get("long_travel", "あまり気にしない"),
        region=answers.get("region", "関東地方") # ⭕️ 追加：フロントエンドから届いた地方を取得
    )