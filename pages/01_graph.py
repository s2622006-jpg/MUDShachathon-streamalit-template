import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📊 グラフサンプル")

# ── サンプルデータの作成 ──────────────────────────
df = pd.DataFrame(
    {
        "月": [
            "1月",
            "2月",
            "3月",
            "4月",
            "5月",
            "6月",
            "7月",
            "8月",
            "9月",
            "10月",
            "11月",
            "12月",
        ],
        "売上": [100, 150, 120, 180, 160, 200, 180, 220, 200, 240, 220, 260],
    }
)

# ── 折れ線グラフ ──────────────────────────────────
st.subheader("折れ線グラフ")
fig = px.line(df, x="月", y="売上", markers=True)
st.plotly_chart(fig)

# ── 棒グラフ ──────────────────────────────────────
st.subheader("棒グラフ")
fig2 = px.bar(df, x="月", y="売上")
st.plotly_chart(fig2)

# ── データテーブル ────────────────────────────────
st.subheader("データテーブル")
st.dataframe(df)
