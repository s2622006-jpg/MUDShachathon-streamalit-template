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
│   ├── app.db                 # SQLiteのDBファイル（おすすめスポット等）
│   └── seed_spots.py          # サンプルスポットをDBに投入するスクリプト
├── app.py                    # アプリのトップページ
├── Dockerfile                 # Docker イメージのビルド定義
├── docker-compose.yml         # Docker での起動設定
├── .dockerignore              # Docker イメージに含めないファイルの一覧
├── .gitignore                # Git に含めないファイルの一覧
├── pyproject.toml            # プロジェクト・依存パッケージの設定
└── README.md                 # このファイル
```

---

## 🍴 Step 1 : Fork する

> **Fork とは？** GitHub 上にある他の人のリポジトリを、自分のアカウントにコピーする機能です。

1. このページ右上の **「Fork」** ボタンをクリック
2. **「Create fork」** をクリック
3. 自分のアカウントにリポジトリがコピーされます

---

## 💻 Step 2 : Clone する

> **Clone とは？** GitHub 上のリポジトリを自分のパソコンにダウンロードする操作です。

1. Fork したリポジトリのページを開く
2. 緑色の **「Code」** ボタンをクリック
3. 表示された URL をコピー
4. ターミナルで以下を実行：

```bash
git clone コピーしたURL
cd hackathon-streamlit-template
```

---

## 🐍 Step 3 : 仮想環境を作成する

> **仮想環境とは？** プロジェクトごとに独立した Python の環境を作る仕組みです。
> 他のプロジェクトと依存パッケージが混ざらないようにするために使います。

```bash
uv venv
```

実行すると `.venv/` フォルダが作成されます。

---

## ✅ Step 4 : 仮想環境に入る

**Mac / Linux の場合：**
```bash
source .venv/bin/activate
```

**Windows の場合：**
```bash
.venv\Scripts\activate
```

成功すると、ターミナルの先頭に `(.venv)` と表示されます。

> ⚠️ **作業するたびに毎回実行** する必要があります！

---

## 📦 Step 5 : 依存パッケージをインストールする

```bash
uv sync
```

`pyproject.toml` に書かれたパッケージが自動でインストールされます。

---

## ▶️ Step 6 : アプリを起動する

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動で開きます 🎉

---

## 🐳 Docker で環境を統一したい場合（任意）

Python/uv のバージョンなどを開発メンバー全員で揃えたい場合は、Docker でも起動できます。
Step 3〜6（仮想環境の作成など）は不要になり、以下の2コマンドだけで動きます。

```bash
docker compose up -d
```

ブラウザで `http://localhost:8501` を開いてください。停止する場合は次のコマンドです。

```bash
docker compose down
```

> 💡 プロジェクトフォルダ全体をコンテナと同期しているので、`data/app.db` などのSQLiteファイルはホスト側にそのまま残ります。
> `.streamlit/secrets.toml` や `.env` を使う場合は、通常通りこのフォルダの中に作成しておけばコンテナ側からも自動で読み込まれます（次の「APIキーなどの秘密情報を使いたい場合」を参照）。
> `.venv` だけはOS間の互換性の問題を避けるため、コンテナ専用のボリュームに分離しています。

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