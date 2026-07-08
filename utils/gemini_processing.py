import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# Geminiに約束させるデータの設計図（スキーマ）
class Spot(BaseModel):
    time: str = Field(description="到着時間または開始時間。例: '10:00'")
    name: str = Field(description="観光スポットや飲食店の名前。実在するもの限定。")
    description: str = Field(description="そのスポットでの過ごし方やおすすめポイントの解説文。")
    latitude: float = Field(description="そのスポットの正確な緯度（数値型）")
    longitude: float = Field(description="そのスポットの正確な経度（数値型）")

class TravelPlan(BaseModel):
    title: str = Field(description="旅行プランの魅力的なタイトル。")
    spots: List[Spot] = Field(description="タイムライン順に並んだスポットのリスト。")

class TravelPlannerBackend:
    """旅行プランの生成ロジックを担当するバックエンドクラス"""
    
    def __init__(self, api_key: str):
        # クラスが呼び出された時にGeminiクライアントを初期化
        self.client = genai.Client(api_key=api_key)

    def generate_plan(self, dep: str, num: int, bg: str, style: str, trans: str, days_count: str, purposes_text: str,longs_traveltime:str) -> dict:
        """フロントエンドから条件を受け取り、Geminiで旅行プラン(辞書型)を生成する関数"""
        
        # AIへの指示文（プロンプト）の組み立て
        prompt = f"""
        以下の条件に完全に合致する、関東エリア（東京・神奈川・埼玉・千葉・茨城・栃木・群馬）限定の旅行プランを1つつくってください。
        
        【条件】
        * 出発地: {dep}
        * 旅行人数: {num}人
        * 予算の目安: {bg}
        * 旅のスタイル: {style}
        * 旅の目的: {purposes_text}
        * 主な移動手段: {trans}
        * 旅行日数: {days_count}
        * 移動時間: {longs_traveltime}
        
        【絶対厳守の注意点】
        * 各スポットの緯度(latitude)と経度(longitude)は必ず実在する正しい数値を調べて入れてください。
        * 日数（日帰りや1泊2日など）に応じた自然なタイムラインにしてください。
        """

        # Gemini APIへ通信
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="あなたは関東地方の観光に特化したプロの旅行プランナーです。",
                response_mime_type="application/json",
                response_schema=TravelPlan,
                temperature=0.7
            ),
        )
        
        # 文字列として返ってきたJSONを、Pythonの「辞書型（dict）」に変換してフロントエンドへ返す
        return json.loads(response.text)