# app_local.py
# Streamlit dashboard for IC3 fraud reports

import json
import ast
import pandas as pd
import streamlit as st
import altair as alt

# -----------------------------
# Page config & simple theming
# -----------------------------
st.set_page_config(
    page_title="Fraud Reports Dashboard",
    layout="wide"
)

st.markdown(
    """
    <style>
    h1, h2, h3 {
        color: #0B3D91;  
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Load CSV
# -----------------------------
@st.cache_data
def load_pdf_summaries(path: str = "pdf_summaries.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data
def build_keyword_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts 'keyword_counts' column into rows: year, keyword, count.
    Supports JSON & Python dict formats.
    """
    rows = []

    for _, row in df.iterrows():
        kc = row.get("keyword_counts", None)
        if pd.isna(kc):
            continue

        counts = None

        if isinstance(kc, dict):
            counts = kc

        elif isinstance(kc, str):
            text = kc.strip()
            try:
                counts = json.loads(text)
            except Exception:
                try:
                    counts = ast.literal_eval(text)
                except Exception:
                    counts = None

        if not isinstance(counts, dict):
            continue

        year = row["date"].year if not pd.isna(row["date"]) else None

        for kw, cnt in counts.items():
            try:
                value = float(cnt)
            except Exception:
                continue

            rows.append({
                "year": year,
                "keyword": str(kw),
                "count": value
            })

    if not rows:
        return pd.DataFrame(columns=["year", "keyword", "count"])

    return pd.DataFrame(rows)


# -----------------------------
# Load data
# -----------------------------
df_raw = load_pdf_summaries()

st.title("Fraud Reports Dashboard")
st.markdown("## DTSC Project Team 2")   # <-- NEW SECOND HEADER

with st.expander("Debug: sample of keyword_counts column"):
    st.write(df_raw[["title", "keyword_counts"]].head())

df_keywords = build_keyword_dataframe(df_raw)

if df_keywords.empty:
    st.error("No keyword data could be built. Check the 'keyword_counts' examples above.")
    st.stop()

# -----------------------------
# Year filter (search by year)
# -----------------------------
available_years = sorted(df_keywords["year"].dropna().unique())
year_options = ["All years"] + [str(y) for y in available_years]

selected_year = st.selectbox("Filter by year", year_options)

if selected_year == "All years":
    df_filtered = df_keywords.copy()
else:
    year_int = int(selected_year)
    df_filtered = df_keywords[df_keywords["year"] == year_int].copy()

# -----------------------------
# Top keywords (filtered)
# -----------------------------
top_keywords = (
    df_filtered
    .groupby("keyword", as_index=False)["count"]
    .sum()
    .sort_values("count", ascending=False)
)

if top_keywords.empty:
    st.warning("No data for this year selection.")
    st.stop()

top5_keywords = top_keywords.head(5).reset_index(drop=True)

# -----------------------------
# Top 3 fraud trends (filtered)
# -----------------------------
top3_df = top_keywords.head(3).reset_index(drop=True)
top3_trends = top3_df["keyword"].tolist()

trend_df = (
    df_filtered[df_filtered["keyword"].isin(top3_trends)]
    .groupby(["year", "keyword"], as_index=False)["count"]
    .sum()
    .sort_values(["year", "keyword"])
)

# -----------------------------
# Layout: line chart + top 5 table
# -----------------------------
left, right = st.columns([2, 1])

with left:
    st.subheader("Yearly Fraud Type Trends")

    line_chart = (
        alt.Chart(trend_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("count:Q", title="Keyword Count"),
            color=alt.Color("keyword:N", title="Fraud Type"),
            tooltip=["year", "keyword", "count"]
        )
        .properties(height=350)
    )

    st.altair_chart(line_chart, use_container_width=True)

with right:
    st.subheader("Top 5 Keywords")

    tbl5 = top5_keywords.copy()
    tbl5.index = tbl5.index + 1
    tbl5.columns = ["Keyword", "Total Count"]
    st.table(tbl5)

# -----------------------------
# NEW: Bar Chart (Top 5 keywords)
# -----------------------------
st.subheader("Top 5 Keywords (Bar Chart)")

bar_chart = (
    alt.Chart(top5_keywords)
    .mark_bar()
    .encode(
        x=alt.X("keyword:N", title="Keyword"),
        y=alt.Y("count:Q", title="Total Count"),
        tooltip=["keyword", "count"]
    )
    .properties(height=300)
)

st.altair_chart(bar_chart, use_container_width=True)

# -----------------------------
# Top 3 Fraud Trends (table)
# -----------------------------
st.markdown("### Top 3 Fraud Trends")

tbl3 = top3_df.copy()
tbl3.index = tbl3.index + 1
tbl3.columns = ["Fraud Trend", "Total Count"]
st.table(tbl3)

# -----------------------------
# AI Summary
# -----------------------------
st.markdown("### AI Summary")

years_in_filtered = sorted(df_filtered["year"].dropna().unique())
first_year = years_in_filtered[0] if years_in_filtered else None
last_year = years_in_filtered[-1] if years_in_filtered else None

summary_parts = []

if selected_year == "All years" and first_year is not None and last_year is not None:
    summary_parts.append(
        f"The trends from {first_year} to {last_year} show how fraud patterns change over time."
    )
elif selected_year != "All years":
    summary_parts.append(f"This view focuses on fraud activity in **{selected_year}**.")

if len(top3_trends) >= 1:
    summary_parts.append(f"The leading fraud trend is **{top3_trends[0]}**.")
if len(top3_trends) >= 2:
    summary_parts.append(f"Other major trends include **{top3_trends[1]}** and **{top3_trends[2]}**.")

summary_parts.append(
    "The Top 5 Keywords table and bar chart highlight the most frequently mentioned issues in the selected data."
)

st.write(" ".join(summary_parts))


