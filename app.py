# app_local.py
# LOCAL VERSION — Uses ONLY Supabase tables:
#   - fraud_reports
#   - fraud_keywords
# First bar chart removed, chart titles simplified, detailed summary kept

import os
import pandas as pd
import streamlit as st
import altair as alt
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# --------------------------------------
# Page config + theme
# --------------------------------------
st.set_page_config(page_title="Fraud Dashboard", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif !important; }
h1,h2,h3,h4 { font-family:'Poppins',sans-serif!important;font-weight:600;color:#0B3D91; }
.block-container {max-width:1200px;padding-top:1rem;}
.stCard {background:#f9fafb;padding:1.1rem;border-radius:.75rem;
         box-shadow:0 2px 6px rgba(0,0,0,0.05);margin-bottom:1.5rem;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------
# Helpers
# --------------------------------------
def pretty_keyword_name(kw: str) -> str:
    if kw is None:
        return ""
    return str(kw).replace("_", " ").title()

def get_supabase_client():
    base = Path(__file__).resolve().parent
    load_dotenv(base / ".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        st.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        st.stop()
    return create_client(url, key)

# --------------------------------------
# Load data from Supabase
# --------------------------------------
@st.cache_data
def load_fraud_keywords() -> pd.DataFrame:
    sb = get_supabase_client()
    try:
        resp = sb.table("fraud_keywords").select("*").execute()
        df = pd.DataFrame(resp.data or [])
    except Exception:
        return pd.DataFrame()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["year"] = df["date"].dt.year
    elif "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
    else:
        df["year"] = pd.NA

    return df

@st.cache_data
def load_fraud_reports() -> pd.DataFrame:
    sb = get_supabase_client()
    resp = sb.table("fraud_reports").select("*").execute()
    df = pd.DataFrame(resp.data or [])
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
    if "count" in df.columns:
        df["count"] = pd.to_numeric(df["count"], errors="coerce")
    return df

# --------------------------------------
# MAIN
# --------------------------------------
df_fk = load_fraud_keywords()
df_keywords = load_fraud_reports()

st.title("Fraud Reports Dashboard")
st.markdown("## DTSC Project Team 2")
st.markdown("##### Authors: Taylor Foster · Sam McClure · Jayson Allman · Yousef Eddin")

if df_keywords.empty:
    st.error("No keyword data found in fraud_reports.")
    st.stop()

# --------------------------------------
# Sidebar filters
# --------------------------------------
years_all = sorted(df_keywords["year"].dropna().unique())
year_choice = st.sidebar.selectbox("Filter by Year", ["All"] + [str(y) for y in years_all])

kw_overall = (
    df_keywords.groupby("keyword")["count"]
    .sum()
    .sort_values(ascending=False)
)

keyword_options = ["All Keywords"] + kw_overall.index.tolist()
keyword_choice = st.sidebar.selectbox("Keyword Focus", keyword_options)

st.sidebar.markdown("---")

# --------------------------------------
# Filtering
# --------------------------------------
# fraud_reports filtered by year
if year_choice == "All":
    df_rep = df_keywords.copy()
else:
    df_rep = df_keywords[df_keywords["year"] == int(year_choice)]

# fraud_reports filtered by keyword
if keyword_choice == "All Keywords":
    df_rep_kw = df_rep.copy()
else:
    df_rep_kw = df_rep[df_rep["keyword"] == keyword_choice]

if df_rep_kw.empty:
    st.warning("No data for this view.")
    st.stop()

# fraud_keywords filtered by year (for table + summary)
if not df_fk.empty:
    if "year" not in df_fk.columns:
        if "date" in df_fk.columns:
            df_fk["date"] = pd.to_datetime(df_fk["date"], errors="coerce")
            df_fk["year"] = df_fk["date"].dt.year
        else:
            df_fk["year"] = pd.NA

    if year_choice == "All":
        df_fk_filtered = df_fk.copy()
    else:
        df_fk_filtered = df_fk[df_fk["year"] == int(year_choice)]
else:
    df_fk_filtered = pd.DataFrame()

# --------------------------------------
# Aggregations (fraud_reports)
# --------------------------------------
top_keywords = (
    df_rep_kw.groupby("keyword", as_index=False)["count"]
    .sum()
    .sort_values("count", ascending=False)
)

top5 = top_keywords.head(5)
top3 = list(top5["keyword"].head(3))

trend_df = (
    df_rep_kw[df_rep_kw["keyword"].isin(top3)]
    .groupby(["year", "keyword"], as_index=False)["count"]
    .sum()
)

heat_df = (
    df_keywords.groupby(["year", "keyword"], as_index=False)["count"]
    .sum()
)

# --------------------------------------
# CARD 1 — Top 5 Keywords (Bar Chart)
# --------------------------------------
st.markdown('<div class="stCard">', unsafe_allow_html=True)
st.subheader("Top 5 Fraud Keywords")

bar_chart = (
    alt.Chart(top5)
    .mark_bar()
    .encode(
        x=alt.X("keyword:N", title="Keyword"),
        y=alt.Y("count:Q", title="Total Mentions"),
        tooltip=["keyword", "count"]
    )
    .properties(height=350)
)

st.altair_chart(bar_chart, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------
# CARD 2 — Line Trends + Top 5 Table
# --------------------------------------
st.markdown('<div class="stCard">', unsafe_allow_html=True)
st.subheader("Yearly Fraud Trends – Top 3")

line_chart = (
    alt.Chart(trend_df)
    .mark_line(
        point=alt.OverlayMarkDef(filled=True, size=90),
        strokeWidth=5
    )
    .encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("count:Q", title="Mentions"),
        color=alt.Color("keyword:N", title="Keyword"),
        tooltip=["year", "keyword", "count"]
    )
    .properties(height=250)
)

st.altair_chart(line_chart, use_container_width=True)

st.subheader("Top 5 Keywords (Table)")
top5_table = top5.copy()
top5_table = top5_table.rename(columns={"keyword": "Keyword", "count": "Total Mentions"})
top5_table.index = top5_table.index + 1
st.table(top5_table)
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------
# CARD 3 — Heatmap
# --------------------------------------
st.markdown('<div class="stCard">', unsafe_allow_html=True)
st.subheader("Keyword Intensity Heatmap")

heatmap = (
    alt.Chart(heat_df)
    .mark_rect()
    .encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("keyword:N", title="Keyword"),
        color=alt.Color("count:Q", title="Intensity"),
        tooltip=["year", "keyword", "count"]
    )
    .properties(height=350)
)

st.altair_chart(heatmap, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------
# CARD 4 — Fraud Keywords Records Table
# --------------------------------------
st.markdown('<div class="stCard">', unsafe_allow_html=True)
st.subheader("Keyword Records")

if df_fk_filtered.empty:
    st.write("No keyword records available for this selection.")
else:
    preferred_cols = ["year", "date", "keyword", "count", "title"]
    cols_to_show = [c for c in preferred_cols if c in df_fk_filtered.columns]

    if cols_to_show:
        df_fk_display = df_fk_filtered[cols_to_show].copy()
    else:
        df_fk_display = df_fk_filtered.copy()

    if "date" in df_fk_display.columns:
        df_fk_display = df_fk_display.sort_values("date", ascending=False)
    elif "year" in df_fk_display.columns:
        df_fk_display = df_fk_display.sort_values("year", ascending=False)

    rename_map = {
        "year": "Year",
        "date": "Date",
        "keyword": "Keyword",
        "count": "Count",
        "title": "Title"
    }
    df_fk_display = df_fk_display.rename(
        columns={k: v for k, v in rename_map.items() if k in df_fk_display.columns}
    )

    st.dataframe(df_fk_display, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------
# CARD 5 — Detailed AI-Style Summary
# --------------------------------------
st.markdown('<div class="stCard">', unsafe_allow_html=True)
st.subheader("Summary Insights")

summary_lines = []

# Years in view from fraud_reports
years_in_view = sorted(df_rep_kw["year"].dropna().unique())

# Time window summary
if year_choice == "All":
    if len(years_in_view) >= 2:
        summary_lines.append(
            f"- This view covers fraud keyword activity from **{years_in_view[0]} to {years_in_view[-1]}**."
        )
    elif len(years_in_view) == 1:
        summary_lines.append(
            f"- This view shows fraud keyword activity for the year **{years_in_view[0]}**."
        )
else:
    summary_lines.append(f"- The charts are filtered to the year **{year_choice}**.")

# Data source context
summary_lines.append(
    "- The charts are built using keyword counts from the project’s Supabase tables. "
    "Counts are grouped by year and keyword to highlight key fraud patterns."
)

# Keyword focus
if keyword_choice != "All Keywords":
    pretty_focus = pretty_keyword_name(keyword_choice)
    summary_lines.append(f"- The current focus is on the keyword **{pretty_focus}**.")
    summary_lines.append(
        "- The line chart and keyword details reflect how often this keyword appears over time."
    )

# Top trends from top3
if len(top3) >= 1:
    main_name = pretty_keyword_name(top3[0])
    summary_lines.append(
        f"- The most common trend in this view is **{main_name}**, which appears more often than other keywords."
    )

if len(top3) >= 2:
    other_names = [pretty_keyword_name(k) for k in top3[1:]]
    if other_names:
        summary_lines.append(
            "- Other major keywords in this view include: "
            + ", ".join(f"**{name}**" for name in other_names) + "."
        )

# Top 5 overview with counts
summary_lines.append("- In this filtered view, the **Top 5 fraud keywords by total mentions** are:")
for _, row in top5.iterrows():
    kw = row["keyword"]
    cnt = int(row["count"])
    name = pretty_keyword_name(kw)
    summary_lines.append(f"  - **{name}** – {cnt} mentions.")

# Total mentions
total_mentions = int(df_rep_kw["count"].sum())
summary_lines.append(
    f"- Across all selected records, there are **{total_mentions} total keyword mentions** in this view."
)

# fraud_keywords records context
if not df_fk_filtered.empty:
    fk_years = sorted(df_fk_filtered["year"].dropna().unique())
    summary_lines.append(
        f"- There are **{len(df_fk_filtered)} individual keyword records** under the current filter, "
        f"with entries from years: {', '.join(str(y) for y in fk_years)}."
    )

# High-level interpretation
summary_lines.append(
    "- Together, the bar chart, line chart, heatmap, and records table show which fraud types are most common, "
    "how they change over time, and how many individual records support those trends."
)

st.markdown("\n".join(summary_lines))
st.markdown('</div>', unsafe_allow_html=True)
