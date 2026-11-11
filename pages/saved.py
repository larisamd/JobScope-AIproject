import streamlit as st
import pandas as pd
from utils.storage import load_jobs, remove_job
from utils.ui import apply_theme
from datetime import datetime, timezone
import re

st.set_page_config(page_title="Saved Jobs | JobScope", page_icon="⚡", layout="wide")
apply_theme()

# ---------------- DATE HELPER ----------------
def format_date_posted(date_str):
    if not date_str:
        return None
    try:
        posted = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days = (now - posted).days
        if days == 0:
            return "Posted today"
        elif days == 1:
            return "Posted yesterday"
        elif days < 30:
            return f"Posted {days} days ago"
        elif days < 365:
            months = days // 30
            return f"Posted {months} month{'s' if months > 1 else ''} ago"
        else:
            return f"Posted {days // 365} year(s) ago"
    except Exception:
        return None


# ---------------- CLEAN HTML ----------------
def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ---------------- PAGE ----------------
st.title("⭐ Saved Jobs")

jobs = load_jobs()

if not jobs:
    st.info("No saved jobs yet.")
else:
    # ---------------- CSV EXPORT ----------------
    def build_csv(jobs):
        rows = []
        for job in jobs:
            rows.append({
                "Title": job.get("title", ""),
                "Company": job.get("company", ""),
                "Location": job.get("location", ""),
                "Salary": job.get("salary", ""),
                "Date Posted": job.get("updated", ""),
                "Link": job.get("link", ""),
                "Snippet": clean_html(job.get("snippet", "")),
            })
        return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Export to CSV",
        data=build_csv(jobs),
        file_name=f"saved_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    st.divider()

    # ---------------- JOB CARDS ----------------
    for i, job in enumerate(jobs):
        st.markdown(f"### {job.get('title', 'No Title')}")
        st.write(f"📍 {job.get('location', 'Unknown')}   🏢 {job.get('company', 'Unknown')}")

        salary = job.get("salary", "")
        if salary and str(salary).strip():
            clean_salary = str(salary).replace("`", "").strip()
            st.text(f"💰 {clean_salary}")

        date_label = format_date_posted(job.get("updated", ""))
        if date_label:
            st.caption(f"🕒 {date_label}")

        col1, col2 = st.columns(2)

        with col1:
            st.link_button("Apply 🚀", job.get("link", "#"))

        with col2:
            if st.button("❌ Remove", key=i):
                remove_job(i)
                st.rerun()

        st.divider()