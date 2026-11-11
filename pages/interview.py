import streamlit as st

from utils.ai import groq_chat_json
from utils.storage import load_jobs, record_activity
from utils.ui import apply_theme


st.set_page_config(page_title="Mock Interview | JobScope", page_icon="⚡", layout="wide")
apply_theme()
st.title("🎙️ AI mock interview")
st.caption("Practice role-specific questions and get direct, actionable feedback.")

resume_text = st.session_state.get("resume_text", "")
if not resume_text:
    st.info("Parse your resume in Resume Lab to personalize the interview.")

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
        st.info("No saved roles yet. Paste the job description below.")
    job_description = st.text_area(
        "Job description",
        height=180,
        placeholder="Paste the role requirements and responsibilities...",
    )

if st.button("Start interview", type="primary"):
    if not resume_text:
        st.warning("Parse your resume in Resume Lab first.")
    elif not job_description.strip():
        st.warning("Add a job description to tailor your questions.")
    else:
        with st.spinner("Creating your interview..."):
            try:
                result = groq_chat_json(
                    [
                        {
                            "role": "system",
                            "content": (
                                "You are a thoughtful technical interviewer. Return JSON "
                                'with one key, "questions", containing exactly five concise '
                                "questions grounded in the candidate resume and target role. "
                                "Mix experience, technical, and behavioral questions. "
                                "Do not ask for information not in the supplied context."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"RESUME:\n{resume_text[:30000]}\n\n"
                                f"JOB DESCRIPTION:\n{job_description[:15000]}"
                            ),
                        },
                    ]
                )
                questions = result.get("questions")
                if not isinstance(questions, list) or not questions:
                    raise RuntimeError("The AI did not return interview questions.")
                st.session_state.interview_questions = [
                    str(question) for question in questions[:5]
                ]
                st.session_state.interview_index = 0
                st.session_state.interview_history = []
                st.session_state.interview_finished = False
            except Exception as error:
                st.error(f"Could not create the interview: {error}")

questions = st.session_state.get("interview_questions", [])
history = st.session_state.get("interview_history", [])
index = st.session_state.get("interview_index", 0)
if questions and index < len(questions):
    st.progress(index / len(questions), text=f"Question {index + 1} of {len(questions)}")
    st.subheader(questions[index])
    with st.form("interview_answer"):
        answer = st.text_area(
            "Your answer",
            height=180,
            placeholder="Answer as you would in a real interview...",
        )
        submitted = st.form_submit_button("Evaluate answer", type="primary")
    if submitted:
        if not answer.strip():
            st.warning("Write an answer before requesting feedback.")
        else:
            with st.spinner("Reviewing your answer..."):
                try:
                    evaluation = groq_chat_json(
                        [
                            {
                                "role": "system",
                                "content": (
                                    "Evaluate interview answers fairly and specifically. "
                                    "Return JSON with score (integer 1-10), feedback "
                                    "(string), strengths (array of strings), and improvements "
                                    "(array of strings). Do not reward unsupported claims."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"ROLE:\n{job_description[:12000]}\n\n"
                                    f"QUESTION:\n{questions[index]}\n\n"
                                    f"CANDIDATE ANSWER:\n{answer[:12000]}"
                                ),
                            },
                        ]
                    )
                    score = max(1, min(10, int(evaluation.get("score", 1))))
                    history.append(
                        {
                            "question": questions[index],
                            "score": score,
                            "feedback": str(evaluation.get("feedback", "")),
                            "strengths": evaluation.get("strengths", []),
                            "improvements": evaluation.get("improvements", []),
                        }
                    )
                    st.session_state.interview_history = history
                    st.session_state.interview_index = index + 1
                    if index + 1 == len(questions):
                        st.session_state.interview_finished = True
                        average = sum(item["score"] for item in history) / len(history)
                        record_activity(
                            "interview",
                            "Completed a mock interview",
                            f"Average answer score: {average:.1f}/10",
                            score=average,
                        )
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not evaluate your answer: {error}")

for item in history:
    with st.expander(f"{item['question']} · {item['score']}/10"):
        st.write(item["feedback"])
        if item["strengths"]:
            st.markdown("**What worked**")
            for strength in item["strengths"]:
                st.markdown(f"- {strength}")
        if item["improvements"]:
            st.markdown("**Try next time**")
            for improvement in item["improvements"]:
                st.markdown(f"- {improvement}")

if st.session_state.get("interview_finished"):
    average = sum(item["score"] for item in history) / len(history)
    st.success(f"Interview complete · average score {average:.1f}/10")
    if st.button("Start a new interview"):
        for key in (
            "interview_questions",
            "interview_index",
            "interview_history",
            "interview_finished",
        ):
            st.session_state.pop(key, None)
        st.rerun()
