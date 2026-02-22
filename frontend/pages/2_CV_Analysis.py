import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from frontend.api_client import analyze_cv

st.set_page_config(page_title="CV Analysis", page_icon="🔍", layout="wide")
st.title("🔍 CV Analysis")

if "cv_id" not in st.session_state:
    st.warning("No CV loaded. Please go to **Upload CV** first.")
    st.stop()

st.markdown(f"Analyzing CV (ID: **{st.session_state['cv_id']}**)")

if "cv_analysis" not in st.session_state:
    if st.button("Run AI Analysis", type="primary"):
        with st.spinner("Analyzing your CV with AI... (this may take 20-40 seconds)"):
            try:
                result = analyze_cv(st.session_state["cv_id"])
                st.session_state["cv_analysis"] = result
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")
else:
    if st.button("Re-run Analysis", type="secondary"):
        del st.session_state["cv_analysis"]
        st.rerun()

if "cv_analysis" in st.session_state:
    analysis = st.session_state["cv_analysis"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"⚠️ Issues Found ({len(analysis.get('issues', []))})")
        issues = analysis.get("issues", [])
        if issues:
            for issue in issues:
                st.error(f"• {issue}")
        else:
            st.success("No major issues found!")

    with col2:
        st.subheader(f"💡 Tips & Recommendations ({len(analysis.get('tips', []))})")
        tips = analysis.get("tips", [])
        if tips:
            for tip in tips:
                st.success(f"• {tip}")
        else:
            st.info("No additional tips.")

    rewrites = analysis.get("rewrites", [])
    if rewrites:
        st.markdown("---")
        st.subheader(f"✏️ Suggested Rewrites ({len(rewrites)})")
        st.markdown("Here are improved versions of weak phrases found in your CV:")
        for rw in rewrites:
            col_before, col_after = st.columns(2)
            with col_before:
                st.markdown("**Before:**")
                st.markdown(
                    f'<div style="background:#ffebee;padding:10px;border-radius:5px;border-left:4px solid #f44336">{rw.get("original", "")}</div>',
                    unsafe_allow_html=True,
                )
            with col_after:
                st.markdown("**After:**")
                st.markdown(
                    f'<div style="background:#e8f5e9;padding:10px;border-radius:5px;border-left:4px solid #4caf50">{rw.get("improved", "")}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("")

    st.markdown("---")
    st.info("Proceed to **JD Match** to compare your CV against a job description.")
