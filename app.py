import streamlit as st
from datetime import datetime

from utils.storage import load_activity, load_jobs
from utils.ui import apply_theme


st.set_page_config(page_title="JobScope | Career cockpit", page_icon="⚡", layout="wide")
apply_theme()

st.markdown(
    """
    <div style="padding: 28px 4px 18px">
      <div style="color:#b8ff00; letter-spacing:.18em; font-size:12px; font-weight:700">
        YOUR CAREER, ACCELERATED
      </div>
      <h1 style="font-size:48px; margin:8px 0 4px">JobScope <span style="color:#ffe44d">/</span></h1>
      <div style="color:#a2b4a6; font-size:18px">
        A smarter cockpit for your next opportunity.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

jobs = load_jobs()
activity = load_activity()
scores = [
    float(item["score"])
    for item in activity
    if item.get("kind") in {"resume_score", "interview"}
    and isinstance(item.get("score"), (int, float))
]
average_score = sum(scores) / len(scores) if scores else None
interviews = sum(item.get("kind") == "interview" for item in activity)

metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("Saved jobs", len(jobs), help="Roles in your saved-job list")
metric2.metric(
    "Average AI score",
    f"{average_score:.1f}/10" if average_score is not None else "—",
    help="Resume match and completed mock-interview scores",
)
metric3.metric("Interviews completed", interviews)
metric4.metric("Recent activity", len(activity[:7]), help="Actions recorded in your recent activity")

st.divider()
left, right = st.columns([1.25, 1])
with left:
    st.subheader("⚡ Your AI toolkit")
    st.markdown(
        """
        - **Resume Lab** — parse your resume and compare it with a target role.
        - **Top Matches** — rank searched and saved jobs by resume similarity.
        - **AI Mock Interview** — practice tailored questions and get answer feedback.
        - **Resume Rewriter** — sharpen bullets while keeping your experience factual.
        """
    )
    st.caption("Choose a workspace from the sidebar to get started.")

with right:
    st.subheader("⏱ Recent activity")
    if not activity:
        st.info("Your activity will appear here as you use JobScope.")
    else:
        for item in activity[:7]:
            timestamp = item.get("timestamp", "")
            try:
                date_label = datetime.fromisoformat(timestamp).astimezone().strftime("%b %d · %H:%M")
            except (TypeError, ValueError):
                date_label = ""
            st.markdown(f"**{item.get('label', 'Activity')}**")
            detail = item.get("detail", "")
            st.caption(" · ".join(part for part in (date_label, detail) if part))