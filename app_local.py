# app_local.py
# LOCAL VERSION — USES ONLY .env, NO st.secrets

import os
import json
import ast
import pandas as pd
import streamlit as st
import altair as alt
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# ----------------------------------
# Page config & basic theming
# ----------------------------------
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

    .block-container {
        max-width: 1200px;
        padding-top: 1.5rem;
    }

    .stCard {
        background: #f9fafb;
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------------
# Simple keyword definitions
# ----------------------------------
KEYWORD_DEFINITIONS = {
    "threats_of_violence": (
        "Scams where criminals use violent or scary threats to pressure victims into "
        "sending money or giving up information."
    ),
    "ransomware": (
        "Malicious software that locks or encrypts files or systems and demands payment "
        "to restore access."
    ),
    "malware": (
        "Malicious software installed on a device without permission, used to steal data, "
        "spy on users, or damage systems."
    ),
    "phishing": (
        "Fraudulent emails, texts, or websites that pretend to be trusted sources to trick "
        "people into sharing passwords, banking details, or other sensitive information."
    ),
    "extortion": (
        "Scams where criminals threaten to release information, cause harm, or take action "
        "unless the victim pays money or complies with demands."
    ),
    "identity_theft": (
        "Criminals using someone’s personal information, such as Social Security numbers or "
        "account details, to open accounts, make purchases, or commit fraud."
    ),
    "credit_card_fraud": (
        "Unauthorized use of a person’s credit or debit card, or card number, to make purchases "
        "or withdraw money."
    )
}

def describe_keyword(kw: str) -> str:
    """Return a friendly human description for a keyword, if we know it."""
    return KEYWORD_DEFINITIONS.get(kw, "")

def pretty_keyword_name(kw: str) -> str:
    """Turn 'threats_of_violence' into 'Threats Of Violence'."""
    return kw.replace("_", " ").title()

# ----------------------------------
# Supabase client (LOCAL ONLY)
# ----------------------------------
def get_supabase_client():
    """
    LOCAL VERSION:
    Loads .env from the SAME folder as this file.
    """
    base_dir = Path(__file__).resolve().parent
    env_path = base_dir / ".env"

    load_dotenv(dotenv_path=env_path)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        st.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        st.stop()

    return create_client(url, key)

# ----------------------------------
# Load data from Supabase
# ----------------------------------
@st.cache_data
def load_ic3_alerts() -> pd.DataFrame:
    supabase = get_supabase_client()

    resp = supabase.table("ic3_alerts").select("*").execute()

    data = resp.data or []
    df = pd.DataFrame(data)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


@st.cache_data
def build_keyword_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, row in df.iterrows():
        kc = row.get("keyword_counts", None)
        if kc is None:
            continue

        counts = None

        if isinstance(kc, dict):
            counts = kc
        elif isinstance(kc, str):
            try:
                counts = json.loads(kc)
            except Exception:
                try:
                    counts = ast.literal_eval(kc)
                except Exception:
                    counts = None

        if not isinstance(counts, dict):
            continue

        year = None
        if "date" in row and not pd.isna(row["date"]):
            year = row["date"].year

        for kw, cnt in counts.items():
            try:
                val = float(cnt)
            except Exception:
                continue

            rows.append({
                "year": year,
                "keyword": kw,
                "count": val
            })

    if not rows:
        return pd.DataFrame(columns=["year", "keyword", "count"])

    return pd.DataFrame(rows)

# ----------------------------------
# MAIN APP
# ----------------------------------
df_raw = load_ic3_alerts()
df_keywords = build_keyword_dataframe(df_raw)

st.title("Fraud Reports Dashboard")
st.markdown("## DTSC Project Team 2")

if df_keywords.empty:
    st.error("No keyword data found.")
    st.stop()

# ----------------------------------
# SIDEBAR FILTERS
# ----------------------------------
st.sidebar.header("Filters")

years_all = sorted(df_keywords["year"].dropna().unique())
year_choice = st.sidebar.selectbox("Filter by year", ["All years"] + [str(y) for y in years_all])

# Dropdown for keyword focus
overall_kw = (
    df_keywords.groupby("keyword")["count"]
    .sum()
    .sort_values(ascending=False)
)

keyword_options = ["All keywords"] + overall_kw.index.tolist()
keyword_choice = st.sidebar.selectbox("Focus on a specific keyword", keyword_options)

st.sidebar.markdown("---")
st.sidebar.header("Download Data")

# Debug
with st.expander("Debug (Raw Supabase Data)"):
    st.write(df_raw.head())

# ----------------------------------
# FILTERING LOGIC
# ----------------------------------
if year_choice == "All years":
    df_year_filtered = df_keywords.copy()
else:
    df_year_filtered = df_keywords[df_keywords["year"] == int(year_choice)]

if keyword_choice == "All keywords":
    df_filtered = df_year_filtered.copy()
else:
    df_filtered = df_year_filtered[df_year_filtered["keyword"] == keyword_choice]

if df_filtered.empty:
    st.warning("No data for this selection")
    st.stop()

# ----------------------------------
# TOP 5 / TOP 3 LOGIC
# ----------------------------------
top_keywords = (
    df_filtered.groupby("keyword", as_index=False)["count"]
    .sum()
    .sort_values("count", ascending=False)
)

top5 = top_keywords.head(5)
top3 = top_keywords.head(3)
top3_list = top3["keyword"].tolist()

# Trend for line graph
trend_df = (
    df_filtered[df_filtered["keyword"].isin(top3_list)]
    .groupby(["year", "keyword"], as_index=False)["count"]
    .sum()
)

# ----------------------------------
# DOWNLOAD CSV
# ----------------------------------
csv_data = df_filtered.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    "Download Filtered CSV",
    csv_data,
    "fraud_filtered.csv",
    "text/csv"
)

# ----------------------------------
# CHARTS AND TABLES (BAR LEFT, LINE RIGHT)
# ----------------------------------
st.markdown('<div class="stCard">', unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])

# LEFT COLUMN → BAR CHART
with col1:
    st.subheader("Top 5 Keywords (Bar Chart)")

    bar_chart = (
        alt.Chart(top5)
        .mark_bar()
        .encode(
            x="keyword:N",
            y="count:Q",
            tooltip=["keyword", "count"]
        )
        .properties(height=350)
    )

    st.altair_chart(bar_chart, use_container_width=True)

# RIGHT COLUMN → LINE CHART + TABLE
with col2:
    st.subheader("Yearly Fraud Type Trends (Top 3 Keywords)")

    line_chart = (
        alt.Chart(trend_df)
        .mark_line(
            point=alt.OverlayMarkDef(filled=True, size=90),
            strokeWidth=5     # THICK LINE
        )
        .encode(
            x=alt.X("year:O", title="Year", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("count:Q", title="Mentions"),
            color=alt.Color("keyword:N", title="Keyword"),
            tooltip=["year", "keyword", "count"]
        )
        .properties(height=220)
    )

    st.altair_chart(line_chart, use_container_width=True)

    st.subheader("Top 5 Keywords (Table)")
    top5_display = top5.copy()
    top5_display.index = top5_display.index + 1
    top5_display.columns = ["Keyword", "Total Count"]
    st.table(top5_display)

st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------
# HEATMAP
# ----------------------------------
st.markdown('<div class="stCard">', unsafe_allow_html=True)
st.subheader("Keyword Intensity Heatmap (Top 10 Keywords)")

heat_base = df_keywords.dropna(subset=["year"])
top10 = (
    heat_base.groupby("keyword")["count"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .index
)

heat_df = (
    heat_base[heat_base["keyword"].isin(top10)]
    .groupby(["year", "keyword"], as_index=False)["count"]
    .sum()
)

heatmap = (
    alt.Chart(heat_df)
    .mark_rect()
    .encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("keyword:N", title="Keyword"),
        color=alt.Color("count:Q", title="Total Count"),
        tooltip=["year", "keyword", "count"]
    )
    .properties(height=350)
)

st.altair_chart(heatmap, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------
# KEYWORD DETAILS SECTION
# ----------------------------------
st.markdown('<div class="stCard">', unsafe_allow_html=True)
st.subheader("Keyword Details & Summary")

if keyword_choice == "All keywords":
    st.write("Select a keyword on the left to see detailed trends for a single fraud type.")
else:
    kw_df = df_keywords[df_keywords["keyword"] == keyword_choice]

    if kw_df.empty:
        st.write("No data available for this keyword.")
    else:
        kw_year = (
            kw_df.dropna(subset=["year"])
            .groupby("year", as_index=False)["count"]
            .sum()
            .sort_values("year")
        )

        kw_chart = (
            alt.Chart(kw_year)
            .mark_line(
                point=True,
                strokeWidth=5
            )
            .encode(
                x=alt.X("year:O", title="Year"),
                y=alt.Y("count:Q", title="Mentions"),
                tooltip=["year", "count"]
            )
            .properties(height=250)
        )

        st.altair_chart(kw_chart, use_container_width=True)

        total = int(kw_year["count"].sum())
        peak_row = kw_year.loc[kw_year["count"].idxmax()]
        peak_year = int(peak_row["year"])
        peak_val = int(peak_row["count"])

        st.markdown(f"**Total mentions:** {total}")
        st.markdown(f"**Highest activity:** {peak_val} mentions in **{peak_year}**")

        # Add definition if we know this keyword
        desc = describe_keyword(keyword_choice)
        if desc:
            st.markdown(f"**What this keyword means:** {desc}")

st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------
# AI SUMMARY OF VIEW (WITH DEFINITIONS)
# ----------------------------------
st.markdown('<div class="stCard">', unsafe_allow_html=True)
st.subheader("AI-Generated Summary")

summary_lines = []

years_in_view = sorted(df_filtered["year"].dropna().unique())

# Time window
if year_choice == "All years":
    if len(years_in_view) >= 2:
        summary_lines.append(
            f"- This dashboard shows fraud activity from **{years_in_view[0]} to {years_in_view[-1]}**."
        )
    elif len(years_in_view) == 1:
        summary_lines.append(
            f"- This dashboard shows fraud activity for the year **{years_in_view[0]}**."
        )
else:
    summary_lines.append(f"- Showing results for **{year_choice}**.")

# Keyword focus
if keyword_choice != "All keywords":
    pretty_name = pretty_keyword_name(keyword_choice)
    summary_lines.append(f"- The view is focused on the fraud keyword **{pretty_name}**.")
    desc = describe_keyword(keyword_choice)
    if desc:
        summary_lines.append(f"  - {pretty_name}: {desc}")

# Top 3 trends (names + definitions)
if len(top3_list) >= 1:
    main_kw = top3_list[0]
    main_name = pretty_keyword_name(main_kw)
    summary_lines.append(f"- The most common trend in this view is **{main_name}**.")
    main_desc = describe_keyword(main_kw)
    if main_desc:
        summary_lines.append(f"  - {main_name}: {main_desc}")

if len(top3_list) >= 2:
    for extra_kw in top3_list[1:]:
        extra_name = pretty_keyword_name(extra_kw)
        summary_lines.append(f"- Another major trend is **{extra_name}**.")
        extra_desc = describe_keyword(extra_kw)
        if extra_desc:
            summary_lines.append(f"  - {extra_name}: {extra_desc}")

# Total counts
total_mentions = int(df_filtered["count"].sum())
summary_lines.append(f"- The filtered dataset contains **{total_mentions} total keyword mentions**.")
summary_lines.append("- The heatmap highlights which fraud types are most active across different years.")
summary_lines.append("- These patterns can help identify where education, monitoring, and prevention efforts should focus.")

st.markdown("\n".join(summary_lines))
st.markdown('</div>', unsafe_allow_html=True)
