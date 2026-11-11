import streamlit as st


def apply_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        :root {
            --electric-green: #b8ff00;
            --electric-yellow: #ffe44d;
        }
        html, body, [class*="css"] {
            font-family: 'Space Grotesk', sans-serif;
        }
        .stApp {
            background:
                radial-gradient(ellipse at 82% 0%, rgba(184, 255, 0, .08), transparent 35%),
                #080d0a;
        }
        [data-testid="stSidebar"] {
            background: #0c130e;
            border-right: 1px solid rgba(184, 255, 0, .14);
        }
        h1, h2, h3 { letter-spacing: -.035em; }
        h1 { color: #f2ffe3; }
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, #121c14, #0c130e);
            border: 1px solid rgba(184, 255, 0, .2);
            border-radius: 16px;
            padding: 18px 20px;
        }
        [data-testid="stMetricValue"] { color: #c8ff36; }
        a { color: var(--electric-yellow) !important; }
        .stButton > button, .stDownloadButton > button {
            border: 1px solid rgba(184, 255, 0, .4);
            border-radius: 10px;
            transition: all .18s ease;
        }
        .stButton > button[kind="primary"] {
            background: #b8ff00;
            color: #10150a;
            font-weight: 700;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: var(--electric-yellow);
            box-shadow: 0 0 18px rgba(255, 228, 77, .2);
            transform: translateY(-1px);
        }
        [data-testid="stExpander"], [data-testid="stForm"] {
            border-color: rgba(184, 255, 0, .18);
            border-radius: 14px;
        }
        code, .mono { font-family: 'DM Mono', monospace; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown("## ⚡ JobScope")
        st.caption("CAREER COCKPIT")
        st.page_link("app.py", label="Overview", icon="🏠")
        st.markdown("**Discover**")
        st.page_link("pages/search.py", label="Search jobs", icon="🔍")
        st.page_link("pages/matches.py", label="Top matches", icon="🎯")
        st.page_link("pages/insight.py", label="Market insights", icon="📈")
        st.markdown("**AI workbench**")
        st.page_link("pages/resume.py", label="Resume lab", icon="🧬")
        st.page_link("pages/interview.py", label="Mock interview", icon="🎙️")
        st.page_link("pages/rewriter.py", label="Resume rewriter", icon="✍️")
        st.markdown("**Library**")
        st.page_link("pages/saved.py", label="Saved jobs", icon="⭐")
