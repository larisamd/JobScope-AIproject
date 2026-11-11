import streamlit as st
import pandas as pd
from utils.api import fetch_jobs
import plotly.express as px
import re
from utils.ui import apply_theme

st.set_page_config(page_title="Job Insights | JobScope", page_icon="⚡", layout="wide")
apply_theme()
st.title("📊 Job Insights")
st.subheader("📈 Market Trends Overview")

# ---------------- INPUT ----------------
col1, col2 = st.columns(2)

with col1:
    keyword = st.text_input("Keyword", "developer")

with col2:
    location = st.text_input("Location", "India")

# ---------------- SESSION STATE ----------------
if "insight_jobs" not in st.session_state:
    st.session_state.insight_jobs = []

# ---------------- FETCH ALL PAGES ----------------
if st.button("Generate Insights"):
    all_jobs = []
    page = 1
    MAX_PAGES = 10

    with st.spinner("Fetching all available jobs..."):
        try:
            while page <= MAX_PAGES:
                results = fetch_jobs(keyword, location, page=page)
                if not results:
                    break
                all_jobs.extend(results)
                page += 1
            st.session_state.insight_jobs = all_jobs
        except Exception as e:
            err = str(e).lower()
            if "getaddrinfo" in err or "nameresolution" in err or "connectionerror" in err or "timeout" in err:
                st.error("📡 No internet connection. Please check your network and try again.")
            else:
                st.error(f"Something went wrong: {e}")
            st.session_state.insight_jobs = []

jobs = st.session_state.insight_jobs

# ---------------- DISPLAY ----------------
if jobs:
    st.success(f"Analyzing {len(jobs)} jobs")

    df = pd.DataFrame(jobs)

    # ---- TOP JOB TITLES ----
    if "title" in df.columns:
        top_titles = df["title"].value_counts().head(10)
        fig1 = px.bar(
            x=top_titles.values,
            y=top_titles.index,
            orientation='h',
            title="Top Job Titles"
        )
        fig1.update_layout(yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig1, use_container_width=True)

    # ---- TOP COMPANIES ----
    if "company" in df.columns:
        top_companies = df["company"].value_counts().head(10)
        fig3 = px.bar(
            x=top_companies.values,
            y=top_companies.index,
            orientation='h',
            title="Top Hiring Companies"
        )
        fig3.update_layout(yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig3, use_container_width=True)

    # ---- TRENDING KEYWORDS ----
    if "title" in df.columns:
        all_titles = " ".join(df["title"].dropna().tolist()).lower()
        all_titles = re.sub(r'[^a-zA-Z\s]', ' ', all_titles)
        words = all_titles.split()

        stopwords = {
            "and", "or", "the", "to", "of", "in", "for", "with",
            "a", "an", "on", "at", "by", "from", "is", "are",
            "developer", "engineer", "senior", "junior", "sr", "jr"
        }

        filtered_words = [w for w in words if w not in stopwords and len(w) > 2]
        word_freq = pd.Series(filtered_words).value_counts().head(10).reset_index()
        word_freq.columns = ["keyword", "count"]

        fig4 = px.bar(
            word_freq,
            x="count",
            y="keyword",
            orientation='h',
            title="Trending Skills / Keywords"
        )
        fig4.update_layout(yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("Enter search criteria and click 'Generate Insights'")