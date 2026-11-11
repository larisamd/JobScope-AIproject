import streamlit as st

from utils.ai import groq_chat_json
from utils.documents import extract_resume_text
from utils.storage import load_jobs, record_activity
from utils.ui import apply_theme


st.set_page_config(page_title="Resume Lab | JobScope", page_icon="⚡", layout="wide")
apply_theme()
st.title("🧬 Resume Lab")
st.caption(
    "Upload a PDF or DOCX to extract and structure your experience. "
    "Resume text stays in your session, not in local storage."
)
st.caption(
    "When you run an AI tool, relevant resume and job text is sent to Groq; "
    "semantic matching uses Gemini embeddings."
)

parse_tab, score_tab = st.tabs(["Parse resume", "Score against a role"])

with parse_tab:
    uploaded_resume = st.file_uploader(
        "Upload your resume",
        type=["pdf", "docx"],
        help="Text-based PDF and DOCX files up to 10 MB are supported.",
    )
    pasted_resume = st.text_area(
        "Or paste resume text",
        value=st.session_state.get("resume_text", ""),
        height=220,
        placeholder="Paste resume text here if you prefer not to upload a file...",
    )
    if st.button("Extract and structure resume", type="primary"):
        try:
            if uploaded_resume:
                resume_text = extract_resume_text(
                    uploaded_resume.name, uploaded_resume.getvalue()
                )
            else:
                resume_text = pasted_resume.strip()
                if not resume_text:
                    raise ValueError("Upload a resume or paste its text first.")
            with st.spinner("Extracting skills, education, and experience..."):
                profile = groq_chat_json(
                    [
                        {
                            "role": "system",
                            "content": (
                                "Extract only facts explicitly present in the resume. "
                                "Return valid JSON with keys: summary (string), skills "
                                "(array of strings), education (array of objects with "
                                "institution, degree, field, dates), and experience "
                                "(array of objects with role, company, dates, highlights "
                                "as an array of strings). Use empty strings or arrays "
                                "when information is absent. Never infer credentials."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"RESUME:\n{resume_text[:30000]}",
                        },
                    ]
                )
            st.session_state.resume_text = resume_text
            st.session_state.resume_profile = profile
            record_activity(
                "resume_parsed",
                "Parsed a resume",
                f"{len(profile.get('skills', []))} skills identified",
            )
        except Exception as error:
            st.error(f"Could not parse this resume: {error}")

    profile = st.session_state.get("resume_profile")
    if profile:
        st.success("Resume profile ready")
        st.markdown(f"**Profile summary**  \n{profile.get('summary', '—')}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Skills")
            skills = profile.get("skills", [])
            st.write(" · ".join(skills) if skills else "No skills were identified.")
            st.markdown("#### Education")
            if profile.get("education"):
                for education in profile["education"]:
                    st.markdown(
                        f"- **{education.get('degree', 'Qualification')}** "
                        f"{education.get('field', '')} — "
                        f"{education.get('institution', 'Institution not listed')} "
                        f"({education.get('dates', '')})"
                    )
            else:
                st.write("No education details were identified.")
        with col2:
            st.markdown("#### Experience")
            if profile.get("experience"):
                for experience in profile["experience"]:
                    st.markdown(
                        f"**{experience.get('role', 'Role')}** · "
                        f"{experience.get('company', 'Company not listed')} "
                        f"({experience.get('dates', '')})"
                    )
                    for highlight in experience.get("highlights", []):
                        st.markdown(f"- {highlight}")
            else:
                st.write("No experience details were identified.")
        with st.expander("View structured profile data"):
            st.json(profile)

with score_tab:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 Your resume")
        resume_text = st.text_area(
            "Resume text",
            value=st.session_state.get("resume_text", ""),
            height=280,
            placeholder="Parse a resume above or paste its full text here...",
            key="resume_score_text",
        )
    with col2:
        st.subheader("💼 Target role")
        saved_jobs = load_jobs()
        use_saved = st.toggle("Use a saved job")
        if use_saved and saved_jobs:
            job_labels = [
                f"{job.get('title', 'Role')} @ {job.get('company', 'Company')}"
                for job in saved_jobs
            ]
            selected_index = st.selectbox(
                "Choose a role", range(len(saved_jobs)), format_func=lambda i: job_labels[i]
            )
            job = saved_jobs[selected_index]
            job_description = (
                f"{job.get('title', '')} at {job.get('company', '')} "
                f"in {job.get('location', '')}.\n\n{job.get('snippet', '')}"
            )
            st.text_area("Job details", value=job_description, height=220, disabled=True)
        elif use_saved and not saved_jobs:
            st.info("No saved jobs yet. Paste a job description below.")
            job_description = st.text_area("Job description", height=220)
        else:
            job_description = st.text_area(
                "Job description",
                height=220,
                placeholder="Paste the job description or requirements...",
            )

    if st.button("⚡ Score my resume", type="primary"):
        if not resume_text.strip():
            st.warning("Please provide your resume text.")
        elif not job_description.strip():
            st.warning("Please provide a job description.")
        else:
            with st.spinner("Comparing your experience with the role..."):
                try:
                    result = groq_chat_json(
                        [
                            {
                                "role": "system",
                                "content": (
                                    "You are a strict, experienced technical recruiter. "
                                    "Return JSON with overall_score, skills_match, "
                                    "experience_match, keyword_match (each integer 1-10), "
                                    "summary (string), and strengths, gaps, tips (arrays "
                                    "of strings). Score only demonstrated alignment; "
                                    "do not inflate scores or invent experience."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"RESUME:\n{resume_text[:30000]}\n\n"
                                    f"JOB DESCRIPTION:\n{job_description[:15000]}"
                                ),
                            },
                        ],
                        temperature=0.1,
                    )
                    st.session_state.resume_score_result = result
                    score = max(1, min(10, int(result.get("overall_score", 1))))
                    record_activity(
                        "resume_score",
                        "Scored a resume against a role",
                        f"Overall match: {score}/10",
                        score=score,
                    )
                except (ValueError, TypeError, RuntimeError) as error:
                    st.error(f"Could not score this resume: {error}")

    result = st.session_state.get("resume_score_result")
    if result:
        st.divider()
        st.subheader("📊 Match report")
        overall = max(1, min(10, int(result.get("overall_score", 1))))
        st.metric("Overall match", f"{overall}/10")
        c1, c2, c3 = st.columns(3)
        c1.metric("Skills", f"{result.get('skills_match', 0)}/10")
        c2.metric("Experience", f"{result.get('experience_match', 0)}/10")
        c3.metric("Keywords", f"{result.get('keyword_match', 0)}/10")
        st.markdown(f"**Summary**  \n{result.get('summary', '')}")
        columns = st.columns(3)
        for column, title, key in zip(
            columns,
            ("✅ Strengths", "⚠️ Gaps", "💡 Tips to improve"),
            ("strengths", "gaps", "tips"),
        ):
            with column:
                st.markdown(f"#### {title}")
                for item in result.get(key, []):
                    st.markdown(f"- {item}")
