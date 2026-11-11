import streamlit as st

from utils.ai import groq_chat_json
from utils.storage import load_jobs, record_activity
from utils.ui import apply_theme


st.set_page_config(page_title="Resume Rewriter | JobScope", page_icon="⚡", layout="wide")
apply_theme()
st.title("✍️ Resume bullet rewriter")
st.caption("Sharper, ATS-friendly bullets—without inventing experience or metrics.")

saved_jobs = load_jobs()
use_saved_job = st.toggle("Use a saved job description")
if use_saved_job and saved_jobs:
    job_labels = [
        f"{job.get('title', 'Role')} @ {job.get('company', 'Company')}"
        for job in saved_jobs
    ]
    selected_job = st.selectbox("Choose a role", range(len(saved_jobs)), format_func=lambda i: job_labels[i])
    job = saved_jobs[selected_job]
    job_description = (
        f"{job.get('title', '')} at {job.get('company', '')}\n"
        f"{job.get('snippet', '')}"
    )
    st.text_area("Job description", job_description, height=160, disabled=True)
else:
    if use_saved_job and not saved_jobs:
        st.info("No saved jobs yet. Paste a job description below.")
    job_description = st.text_area(
        "Job description",
        height=180,
        placeholder="Paste the target role's requirements...",
    )

bullets = st.text_area(
    "Resume bullets to improve",
    value=st.session_state.get("resume_text", ""),
    height=220,
    placeholder="Paste one achievement per line. Include real outcomes and metrics where available.",
)

if st.button("Rewrite bullets", type="primary"):
    if not bullets.strip() or not job_description.strip():
        st.warning("Provide both resume content and a target job description.")
    else:
        with st.spinner("Improving clarity and role alignment..."):
            try:
                result = groq_chat_json(
                    [
                        {
                            "role": "system",
                            "content": (
                                "You are an ATS resume editor. Return JSON with a "
                                '"rewrites" array of objects, each containing original, '
                                "revised, and aligned_keywords (array of strings). Use "
                                "clear action verbs and concise language. Preserve the "
                                "candidate's facts exactly: never invent tools, outcomes, "
                                "responsibilities, or metrics. Only align a keyword when "
                                "the source supports it."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"RESUME BULLETS:\n{bullets[:20000]}\n\n"
                                f"JOB DESCRIPTION:\n{job_description[:15000]}"
                            ),
                        },
                    ]
                )
                rewrites = result.get("rewrites")
                if not isinstance(rewrites, list):
                    raise RuntimeError("The AI did not return rewritten bullets.")
                st.session_state.rewrites = rewrites
                record_activity(
                    "resume_rewrite",
                    f"Rewrote {len(rewrites)} resume bullets",
                    "ATS-aligned rewrite",
                )
            except Exception as error:
                st.error(f"Could not rewrite these bullets: {error}")

for rewrite in st.session_state.get("rewrites", []):
    st.markdown(f"**Before**  \n{rewrite.get('original', '')}")
    st.markdown(f"**After**  \n{rewrite.get('revised', '')}")
    keywords = rewrite.get("aligned_keywords", [])
    if keywords:
        st.caption("Aligned keywords: " + " · ".join(keywords))
    st.divider()
