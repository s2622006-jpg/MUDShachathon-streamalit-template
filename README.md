# 🧳 旅行プラン自動作成アプリ

いくつかの質問に答えるだけで、AI（Gemini）が旅行プランを自動作成するアプリです。

---

## 📁 ファイル構成

```
hackathon-streamlit-template/
│
├── .streamlit/
│   ├── config.toml           # テーマ・サーバーの設定ファイル
│   └── secrets.toml.example  # シークレット（APIキーなど）の記述例
│
├── pages/
│   └── 01_travel_plan.py     # 質問フォーム→AIプラン生成→地図表示ページ
│
├── utils/
│   ├── database.py           # おすすめスポットDB（SQLite）の操作関数
│   ├── gemini_client.py      # プロンプト生成・Gemini API呼び出し
│   ├── google_maps.py        # 移動時間・営業時間の取得（Google Maps）
│   └── travel_plan.py        # 上記をまとめて呼び出す司令塔関数
│
├── data/
│   ├── app.db                 # SQLiteのDBファイル（Turso未設定時はこれを使用）
│   └── seed_spots.py          # サンプルスポットをDBに投入するスクリプト
├── app.py                    # アプリのトップページ
├── .gitignore                # Git に含めないファイルの一覧
├── pyproject.toml            # プロジェクト・依存パッケージの設定
└── README.md                 # このファイル
```

---

## 🚀 アプリの使い方

### 📍 Step 1 : トップページを開く

アプリを起動すると、左メニューに **「ホーム」「プランを作成」「みんなのプラン」** の3ページが表示されます。

---

### 📝 Step 2 : 「プランを作成」ページで質問に答える

以下の項目を入力します。

- 予算（1人あたり）／人数
- 目的（自然・グルメ・刺激・文化から2つ選択）
- 主な移動手段
- 出発地点（駅名や施設名など具体的な場所ほど、移動ルートの精度が上がります）
- 旅行日数／旅行のペース
- 移動時間の希望
- 旅行予定の地方

---

### ✨ Step 3 : AIがプランを自動生成する

**「プランを作成する」** ボタンを押すと、Gemini が条件に合った旅行プランを生成します（数十秒かかります）。

---

### 🗺️ Step 4 : プランを確認する

生成されたプランには、タイムスケジュール・地図・移動時間の目安・アドバイスが表示されます。
旅行日数が2日以上の場合は、日ごとにタブで切り替えて確認できます。

---

### 📢 Step 5 : プランを公開する（任意）

表示名を入力して **「公開する」** ボタンを押すと、プランが「みんなのプラン」ページに公開され、他のユーザーが閲覧できるようになります。

---

### 💬 Step 6 : みんなのプランを見る・コメントする

**「みんなのプラン」** ページでは、他のユーザーが公開したプランを閲覧し、コメントを投稿できます。

---

## ☁️ 「みんなのプラン」をチームで共有したい場合（任意）

デフォルトでは `data/app.db`（ローカルのSQLiteファイル）が使われるため、各自の環境で生成・公開したプランは他のメンバーには見えません。
チーム全員が同じデータを見られるようにしたい場合は、[Turso](https://turso.tech/)（SQLite互換のクラウドDB）に切り替えられます。

1. Turso CLIをインストールし、DBを作成する

   ```bash
   curl -sSfL https://get.tur.so/install.sh | bash
   turso auth login
   turso db create travel-app-db
   turso db show travel-app-db --url
   turso db tokens create travel-app-db
   ```

2. `secrets.toml` に発行された値を記入する

   ```toml
   TURSO_DATABASE_URL = "libsql://travel-app-db-xxxxx.turso.io"
   TURSO_AUTH_TOKEN = "xxxxx"
   ```

3. アプリを再起動すれば、以降は自動でTursoのDBが使われます。

> 💡 `TURSO_DATABASE_URL` が未設定の場合は、従来通り `data/app.db` が使われるので、Tursoを使わない開発者にも影響はありません。
> `TURSO_AUTH_TOKEN` は秘密情報なので、Slackなど安全な経路でチームに共有してください（Gitには含めないでください）。

---

## 🔑 APIキーなどの秘密情報を使いたい場合

`.streamlit/secrets.toml.example` をコピーして `secrets.toml` にリネームし、値を記入してください。

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

> ⚠️ `secrets.toml` は `.gitignore` に含まれているため、**Git には絶対にアップロードされません。**

---

## 🚫 .gitignore について

`.gitignore` には **Git で管理しないファイル** を記述しています。

| 記述内容 | 理由 |
|---|---|
| `.venv/` | 仮想環境は人それぞれ異なるため共有不要 |
| `__pycache__/` | Python が自動生成するキャッシュファイル |
| `.streamlit/secrets.toml` | APIキーなどの秘密情報を守るため |
| `.env` | 環境変数ファイル（秘密情報を含む場合がある） |
| `data/*.db` | DBファイルは各自で生成されるため共有不要 |
| `.DS_Store` | Mac が自動生成するファイル（不要） |

> 💡 **重要：** 秘密情報は最初から絶対に `git add` しないように注意しましょう！