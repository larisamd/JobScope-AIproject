import re

import streamlit as st

from utils.ai import cosine_similarity, gemini_embeddings
from utils.storage import load_jobs, record_activity
from utils.ui import apply_theme


st.set_page_config(page_title="Top Matches | JobScope", page_icon="⚡", layout="wide")
apply_theme()
st.title("🎯 Top matches for you")
st.caption("Semantic ranking compares your resume with real job descriptions.")

resume_text = st.session_state.get("resume_text", "")
if not resume_text:
    st.info("Upload and parse your resume in Resume Lab before matching jobs.")

source = st.radio(
    "Jobs to rank",
    ["Current search + saved jobs", "Saved jobs only"],
    horizontal=True,
)
jobs = load_jobs()
if source == "Current search + saved jobs":
    jobs = st.session_state.get("jobs", []) + jobs

unique_jobs = []
seen_links = set()
for job in jobs:
    link = job.get("link") or f"{job.get('title', '')}|{job.get('company', '')}"
    if link not in seen_links:
        seen_links.add(link)
        unique_jobs.append(job)

if not unique_jobs:
    st.info("Search for jobs or save jobs first, then return here to rank them.")
elif st.button("✨ Rank my matches", type="primary"):
    if not resume_text:
        st.warning("Parse a resume in Resume Lab before ranking jobs.")
    else:
        st.session_state.match_results = []
        texts = [
            " ".join(
                str(job.get(field, ""))
                for field in ("title", "company", "location", "snippet")
            )[:12000]
            for job in unique_jobs
        ]
        texts = [
            re.sub(r"<[^>]+>", " ", text).strip() or str(job.get("title", ""))
            for text, job in zip(texts, unique_jobs)
        ]
        with st.spinner("Comparing your resume with the job descriptions..."):
            try:
                resume_vector = gemini_embeddings([resume_text], "RETRIEVAL_QUERY")[0]
                job_vectors = gemini_embeddings(texts, "RETRIEVAL_DOCUMENT")
                ranked = sorted(
                    (
                        (
                            max(0.0, cosine_similarity(resume_vector, vector)) * 100,
                            job,
                        )
                        for job, vector in zip(unique_jobs, job_vectors)
                    ),
                    key=lambda item: item[0],
                    reverse=True,
                )
                st.session_state.match_results = ranked
                record_activity(
                    "semantic_match",
                    f"Ranked {len(ranked)} jobs",
                    "Gemini semantic matching",
                )
            except Exception as error:
                st.error(f"Could not rank jobs: {error}")

for score, job in st.session_state.get("match_results", []):
    st.markdown(f"### {job.get('title', 'Untitled role')}")
    st.write(
        f"🏢 {job.get('company', 'Company not listed')}  ·  "
        f"📍 {job.get('location', 'Location not listed')}"
    )
    st.progress(min(int(score), 100), text=f"{score:.0f}% resume similarity")
    if job.get("link"):
        st.link_button("View role ↗", job["link"])
    st.divider()
