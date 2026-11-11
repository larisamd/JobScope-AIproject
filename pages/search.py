import streamlit as st
from utils.api import fetch_jobs
from utils.storage import save_job, load_jobs
from utils.ui import apply_theme
import re
from datetime import datetime, timezone

st.set_page_config(page_title="Search Jobs | JobScope", page_icon="⚡", layout="wide")
apply_theme()

# ---------------- CLEAN HTML ----------------
def clean_html(text):
    
    if not text:
        return ""
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'</p>|<p>', ' ', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\s*#\s*', '\n• ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.replace(' •', '\n•')
    return text


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


# ---------------- UI ----------------
st.title("🔍 Job Search")

col1, col2 = st.columns(2)

with col1:
    keyword = st.text_input("Keyword", "developer")

with col2:
    location = st.text_input("Location", "India")

st.caption("Scroll down and click 'Load More' to see more jobs ↓")


# ---------------- SESSION STATE ----------------
if "jobs" not in st.session_state:
    st.session_state.jobs = []

if "page" not in st.session_state:
    st.session_state.page = 1

if "no_more" not in st.session_state:
    st.session_state.no_more = False

if "searched" not in st.session_state:
    st.session_state.searched = False

if "search_error" not in st.session_state:
    st.session_state.search_error = None


# ---------------- SEARCH ----------------
if st.button("Search Jobs"):
    st.session_state.page = 1
    st.session_state.no_more = False
    st.session_state.searched = True
    st.session_state.search_error = None
    with st.spinner("Searching for jobs..."):
        try:
            st.session_state.jobs = fetch_jobs(keyword, location, page=1)
        except Exception as e:
            err = str(e).lower()
            if "getaddrinfo" in err or "nameresolution" in err or "connectionerror" in err or "timeout" in err:
                st.session_state.search_error = "📡 No internet connection. Please check your network and try again."
            else:
                st.session_state.search_error = str(e)
            st.session_state.jobs = []


jobs = st.session_state.jobs

# Pre-load saved links for save button state
saved_links = {j.get("link") for j in load_jobs()}

# ---------------- DISPLAY ----------------
if jobs:
    st.success(f"Showing {len(jobs)} jobs")

    for i, job in enumerate(jobs):
        with st.container():
            st.markdown(f"### {job.get('title', 'No Title')}")
            st.write(f"📍 {job.get('location', 'Unknown')}   🏢 {job.get('company', 'Unknown')}")

            salary = job.get("salary", "")
            if salary and str(salary).strip():
                clean_salary = str(salary).replace("`", "").strip()
                st.text(f"💰 {clean_salary}")

            date_label = format_date_posted(job.get("updated", ""))
            if date_label:
                st.caption(f"🕒 {date_label}")

            snippet = clean_html(job.get("snippet", ""))
            with st.expander("📄 View Job Details"):
                st.markdown(f"""
                <div style="font-size:14px; line-height:1.6; color:#cfcfcf;">
                {snippet}
                </div>
                """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.link_button("Apply 🚀", job.get("link", "#"))

            with col2:
                job_link = job.get("link", "")
                already_saved = job_link in saved_links
                if already_saved:
                    st.button("✅ Saved", key=f"save_{i}", disabled=True)
                else:
                    if st.button("⭐ Save", key=f"save_{i}"):
                        save_job(job)
                        saved_links.add(job_link)
                        st.success("Saved!")

            st.divider()

    # ---------------- LOAD MORE ----------------
    if not st.session_state.no_more:
        if st.button("Load More"):
            next_page = st.session_state.page + 1
            with st.spinner("Loading more jobs..."):
                try:
                    more_jobs = fetch_jobs(keyword, location, page=next_page)
                    st.session_state.page = next_page
                    if more_jobs:
                        st.session_state.jobs.extend(more_jobs)
                    else:
                        st.session_state.no_more = True
                        st.warning("No more jobs found.")
                except Exception as e:
                    err = str(e).lower()
                    if "getaddrinfo" in err or "nameresolution" in err or "connectionerror" in err or "timeout" in err:
                        st.error("📡 No internet connection. Please check your network and try again.")
                    else:
                        st.error(f"Something went wrong: {e}")

elif st.session_state.search_error:
    st.error(st.session_state.search_error)

elif st.session_state.searched:
    st.error(f"No jobs found for '{keyword}' in '{location}'")

else:
    st.info("Search for jobs to begin")