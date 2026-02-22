import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from frontend.api_client import create_jd, match_cv_jd

st.set_page_config(page_title="JD Match", page_icon="🎯", layout="wide")
st.title("🎯 Job Description Matching")

if "cv_id" not in st.session_state:
    st.warning("No CV loaded. Please go to **Upload CV** first.")
    st.stop()

st.markdown("Paste the job description below to see how well your CV matches.")

jd_text = st.text_area(
    "Job Description",
    height=300,
    placeholder="Paste the full job description here...",
    key="jd_input",
)

col1, col2 = st.columns([1, 3])
with col1:
    submit_jd = st.button("Extract Requirements", type="primary", disabled=not jd_text.strip())

if submit_jd and jd_text.strip():
    with st.spinner("Extracting requirements from JD..."):
        try:
            jd_result = create_jd(jd_text)
            st.session_state["jd_id"] = jd_result["jd_id"]
            st.session_state["jd_requirements"] = jd_result["extracted_requirements"]
            st.session_state.pop("match_result", None)
            st.rerun()
        except Exception as e:
            st.error(f"Failed to process JD: {e}")

if "jd_requirements" in st.session_state:
    req = st.session_state["jd_requirements"]
    st.markdown("---")
    st.subheader("Extracted Requirements")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Hard Skills / Technologies:**")
        for skill in req.get("hard_skills", []):
            st.markdown(f"- `{skill}`")

        st.markdown("**Keywords:**")
        keywords = req.get("keywords", [])
        if keywords:
            st.markdown(" ".join([f"`{k}`" for k in keywords]))

    with col2:
        st.markdown("**Soft Skills:**")
        for skill in req.get("soft_skills", []):
            st.markdown(f"- {skill}")

        st.markdown("**Key Responsibilities:**")
        for resp in req.get("responsibilities", [])[:5]:
            st.markdown(f"- {resp}")

    st.markdown("---")

    if st.button("Run CV vs JD Match", type="primary"):
        with st.spinner("Comparing your CV to the job description..."):
            try:
                match = match_cv_jd(st.session_state["cv_id"], st.session_state["jd_id"])
                st.session_state["match_result"] = match
                st.rerun()
            except Exception as e:
                st.error(f"Matching failed: {e}")

if "match_result" in st.session_state:
    match = st.session_state["match_result"]
    score = match.get("match_score", 0)

    st.markdown("---")
    st.subheader("Match Results")

    # Score display
    col_score, col_bar = st.columns([1, 3])
    with col_score:
        color = "#4caf50" if score >= 70 else "#ff9800" if score >= 40 else "#f44336"
        st.markdown(
            f'<div style="text-align:center;background:{color};color:white;padding:20px;border-radius:10px;font-size:2.5em;font-weight:bold">{score}%</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='text-align:center;margin-top:5px'>Match Score</div>", unsafe_allow_html=True)
    with col_bar:
        st.progress(score / 100)
        if score >= 70:
            st.success("Great match! Your CV aligns well with this role.")
        elif score >= 40:
            st.warning("Moderate match. Consider adding missing skills.")
        else:
            st.error("Low match. Significant gaps found — see recommendations below.")

    col1, col2 = st.columns(2)
    with col1:
        matched = match.get("matched_skills", [])
        st.subheader(f"✅ Matched Skills ({len(matched)})")
        for skill in matched:
            st.success(f"✓ {skill}")

    with col2:
        missing = match.get("missing_skills", [])
        st.subheader(f"❌ Missing Skills ({len(missing)})")
        for skill in missing:
            st.error(f"✗ {skill}")

    recommendations = match.get("recommendations", [])
    if recommendations:
        st.markdown("---")
        st.subheader("📋 Recommendations")
        for rec in recommendations:
            st.info(f"→ {rec}")

    st.markdown("---")
    st.info("Proceed to **Interview** to practice a mock interview for this role.")
