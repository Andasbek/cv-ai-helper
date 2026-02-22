import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from frontend.api_client import upload_cv, get_cv, delete_cv

st.set_page_config(page_title="Upload CV", page_icon="📤", layout="wide")
st.title("📤 Upload Your CV")

# Show current CV status
if "cv_id" in st.session_state:
    st.success(f"Current CV loaded (ID: {st.session_state.cv_id})")
    if st.button("Remove current CV and upload a new one", type="secondary"):
        try:
            delete_cv(st.session_state.cv_id)
        except Exception:
            pass
        for key in ["cv_id", "cv_sections", "cv_raw_text", "jd_id", "session_id"]:
            st.session_state.pop(key, None)
        st.rerun()

st.markdown("Upload your resume in **PDF** or **TXT** format (max 20 MB).")

uploaded_file = st.file_uploader(
    "Choose your CV file",
    type=["pdf", "txt"],
    help="PDF (text-based) or plain text files are supported.",
)

if uploaded_file is not None and "cv_id" not in st.session_state:
    with st.spinner("Uploading and parsing your CV..."):
        try:
            result = upload_cv(uploaded_file.read(), uploaded_file.name)
            cv_id = result["cv_id"]
            st.session_state["cv_id"] = cv_id

            # Fetch sections
            cv_data = get_cv(cv_id)
            st.session_state["cv_sections"] = cv_data["sections"]
            st.session_state["cv_raw_text"] = cv_data["raw_text"]

            st.success(f"CV uploaded successfully! (ID: {cv_id})")
        except Exception as e:
            st.error(f"Upload failed: {e}")
            st.stop()

# Display sections
if "cv_sections" in st.session_state:
    sections = st.session_state["cv_sections"]
    st.markdown("---")
    st.subheader("Detected Sections")

    if not sections:
        st.warning("No sections were detected. The CV may be in an unusual format.")
    else:
        cols = st.columns(2)
        section_icons = {
            "contacts": "📞",
            "summary": "👤",
            "skills": "🛠️",
            "experience": "💼",
            "education": "🎓",
            "projects": "🚀",
            "certifications": "📜",
            "languages": "🌍",
            "other": "📋",
        }
        for i, section in enumerate(sections):
            icon = section_icons.get(section["section_name"], "📋")
            col = cols[i % 2]
            with col:
                with st.expander(f"{icon} {section['section_name'].capitalize()}", expanded=False):
                    st.text(section["content"])

    st.markdown("---")
    st.info("Proceed to **CV Analysis** in the sidebar for AI feedback on your resume.")

    with st.expander("View raw extracted text", expanded=False):
        st.text(st.session_state.get("cv_raw_text", ""))
