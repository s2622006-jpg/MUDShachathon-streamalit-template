import streamlit as st
from pathlib import Path

UPLOAD_DIR = Path("uploads")

st.title("📂 ファイルアップロードのサンプル")
st.write("ファイルをアップロードして保存するサンプルです")

# ── ファイルアップロード ──────────────────────────────────
uploaded_file = st.file_uploader(
    "ファイルを選択してください",
    type=["png", "jpg", "jpeg", "pdf", "txt", "csv", "xlsx"],
)

if uploaded_file is not None:
    save_path = UPLOAD_DIR / uploaded_file.name

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"「{uploaded_file.name}」をアップロードしました！")

    # 画像なら表示
    if uploaded_file.type.startswith("image/"):
        st.image(uploaded_file, caption=uploaded_file.name)

    # CSVならデータを表示
    elif uploaded_file.type == "text/csv":
        import pandas as pd

        df = pd.read_csv(uploaded_file)
        st.dataframe(df)

# ── 保存済みファイルの一覧 ──────────────────────────────────
st.subheader("保存済みファイル一覧")
files = [f for f in UPLOAD_DIR.iterdir() if f.name != ".gitkeep"]

if not files:
    st.info("まだファイルがありません")
else:
    for file in files:
        st.write(f"📜 {file.name}")
