import streamlit as st
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import json

# -------------------------
# Load .env and connect to Supabase
# -------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("SUPABASE_URL or SUPABASE_KEY is missing in .env")
    st.stop()

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Failed to create Supabase client: {e}")
    st.stop()

# -------------------------
# Data loaders (Supabase only)
# -------------------------
@st.cache_data
def load_keyword_data():
    """
    Load fraud keyword data from Supabase table fraud_keywords.
    Expected columns: year, keyword, count.
    """
    try:
        data = supabase.table("fraud_keywords").select("*").execute()
        df = pd.DataFrame(data.data)
        return df
    except Exception as e:
        st.error(f"Error loading fraud_keywords from Supabase: {e}")
        return pd.DataFrame()

@st.cache_data
def load_report_text():
    """
    Load fraud report text from Supabase table fraud_reports.
    Expected columns: year, title, report_text.
    """
    try:
        data = supabase.table("fraud_reports").select("*").execute()
        df = pd.DataFrame(data.data)
        return df
    except Exception as e:
        st.error(f"Error loading fraud_reports from Supabase: {e}")
        return pd.DataFrame()

@st.cache_data
def load_ic3_alerts():
    """
    Load IC3 alerts from Supabase table ic3_alerts.
    Expected columns: title, date, quarter, keyword_counts, summary.
    """
    try:
        data = supabase.table("ic3_alerts").select("*").execute()
        df = pd.DataFrame(data.data)
        return df
    except Exception as e:
        st.error(f"Error loading ic3_alerts from Supabase: {e}")
        return pd.DataFrame()

# -------------------------
# Load data
# -------------------------
df = load_keyword_data()
df_reports = load_report_text()
df_alerts = load_ic3_alerts()

# If no keyword data, stop the app
if df.empty:
    st.error("No data found in fraud_keywords table.")
    st.stop()

# -------------------------
# Streamlit Page Setup
# -------------------------
st.set_page_config(page_title="Fraud Dashboard", layout="centered")

# White theme
st.markdown("""
<style>
    body { background-color: white; color: black; }
    .stApp { background-color: white; }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 Fraud Keyword Analysis Dashboard")
st.markdown("<h3><b>DTSC Project Team 2</b></h3>", unsafe_allow_html=True)

# -------------------------
# YEAR FILTER
# -------------------------
st.subheader("🔽 Filter by Year (Fraud Keywords)")

if "year" in df.columns:
    years = ["All Years"] + sorted(df["year"].dropna().unique().tolist())
else:
    years = ["All Years"]

selected_year = st.selectbox("Choose a year:", years)

if selected_year != "All Years" and "year" in df.columns:
    filtered_df = df[df["year"] == selected_year]
else:
    filtered_df = df.copy()

# -------------------------
# SHOW FILTERED KEYWORD DATA
# -------------------------
st.subheader("Filtered Fraud Keyword Data (fraud_keywords)")
st.dataframe(filtered_df)

# -------------------------
# DOWNLOAD BUTTON
# -------------------------
csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.subheader("⬇️ Download Filtered Data")
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv_data,
    file_name="filtered_fraud_keywords.csv",
    mime="text/csv"
)

# -------------------------
# FRAUD KEYWORDS SUMMARY
# -------------------------
st.subheader("📋 Fraud Keywords Summary (Aggregated)")

if not filtered_df.empty and {"keyword", "count"}.issubset(filtered_df.columns):
    summary = (
        filtered_df.groupby("keyword")["count"]
        .sum()
        .reset_index()
        .sort_values("count", ascending=False)
    )
    st.dataframe(summary)
else:
    st.info("Cannot build summary – 'keyword' and 'count' columns are required.")

# -------------------------
# TOP 5 KEYWORDS (BAR + PIE)
# -------------------------
st.subheader("🏆 Top 5 Keywords (Filtered)")

if not filtered_df.empty and {"keyword", "count"}.issubset(filtered_df.columns):
    top5 = (
        filtered_df.groupby("keyword")["count"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    st.bar_chart(top5)

    st.subheader("🥧 Keyword Share (Top 5)")

    fig, ax = plt.subplots()
    ax.pie(top5.values, labels=top5.index, autopct="%1.1f%%")
    ax.set_title("Top 5 Keyword Share")
    st.pyplot(fig)
else:
    st.info("Cannot compute Top 5 – 'keyword' and 'count' columns are required.")

# -------------------------
# TOP 3 TRENDS
# -------------------------
st.subheader("📈 Top 3 Fraud Trends Over Time (All Data)")

if {"year", "count"}.issubset(df.columns):
    trends = (
        df.groupby("year")["count"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
    )
    st.line_chart(trends)
else:
    st.info("Cannot compute trends – 'year' and 'count' columns are required.")

# -------------------------
# FRAUD REPORT TEXT
# -------------------------
st.subheader("📝 Fraud Report Text (fraud_reports)")

if df_reports.empty:
    st.info("No data found in fraud_reports table.")
else:
    # Make sure year/title/report_text exist
    if "year" in df_reports.columns and "title" in df_reports.columns and "report_text" in df_reports.columns:
        years_reports = sorted(df_reports["year"].dropna().unique().tolist())
        selected_report_year = st.selectbox("Select report year:", years_reports)

        reports_filtered = df_reports[df_reports["year"] == selected_report_year]

        titles = reports_filtered["title"].tolist()
        selected_title = st.selectbox("Choose a report:", titles)

        row = reports_filtered[reports_filtered["title"] == selected_title].iloc[0]
        st.markdown("**Full Report Text:**")
        st.write(row["report_text"])
    else:
        st.info("fraud_reports table must include 'year', 'title', and 'report_text' columns.")

# -------------------------
# IC3 ALERTS SECTION
# -------------------------
st.subheader("🚨 IC3 Alerts Overview (ic3_alerts)")

if df_alerts.empty:
    st.info("No IC3 alerts found in ic3_alerts table.")
else:
    # Show basic alerts table
    view_cols = [c for c in ["title", "date", "quarter", "summary"] if c in df_alerts.columns]
    if view_cols:
        st.dataframe(df_alerts[view_cols])

    # Filter by quarter if available
    if "quarter" in df_alerts.columns:
        quarter_options = ["All"] + sorted(df_alerts["quarter"].dropna().unique().tolist())
        selected_quarter = st.selectbox("Filter IC3 Alerts by Quarter:", quarter_options)

        if selected_quarter != "All":
            alerts_filtered = df_alerts[df_alerts["quarter"] == selected_quarter]
        else:
            alerts_filtered = df_alerts.copy()
    else:
        alerts_filtered = df_alerts.copy()

    if not alerts_filtered.empty and "title" in alerts_filtered.columns:
        alert_titles = alerts_filtered["title"].tolist()
        selected_alert = st.selectbox("Select an IC3 Alert:", alert_titles)

        alert_row = alerts_filtered[alerts_filtered["title"] == selected_alert].iloc[0]

        # Title, date, quarter
        st.markdown(f"### {alert_row.get('title', '')}")
        date_val = alert_row.get("date", "")
        q_val = alert_row.get("quarter", "")
        st.markdown(f"**Date:** {date_val}  •  **Quarter:** Q{q_val}")

        # Summary
        st.markdown("**Summary:**")
        st.write(alert_row.get("summary", ""))

        # Keyword counts from JSONB
        if "keyword_counts" in alert_row:
            st.subheader("🔑 IC3 Alert Keyword Counts")

            kc = alert_row["keyword_counts"]

            # Convert JSON string to dict if needed
            if isinstance(kc, str):
                try:
                    kc = json.loads(kc)
                except Exception:
                    kc = {}

            if isinstance(kc, dict) and kc:
                kc_df = pd.DataFrame(
                    [{"keyword": k, "count": v} for k, v in kc.items()]
                ).sort_values("count", ascending=False)

                st.dataframe(kc_df)
                st.bar_chart(kc_df.set_index("keyword")["count"])
            else:
                st.info("No valid keyword_counts data for this alert.")
    else:
        st.info("IC3 alerts table is missing expected columns like 'title'.")
# -------------------------
# FOOTER
# -------------------------
st.markdown("---")
