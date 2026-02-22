import streamlit as st

st.set_page_config(
    page_title="CV AI Helper",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("CV AI Helper & Interview Preparation Platform")

st.markdown("""
Welcome! This platform helps you:

| Step | Module | Description |
|------|--------|-------------|
| 1️⃣ | **Upload CV** | Upload your resume (PDF or TXT) and extract its sections |
| 2️⃣ | **CV Analysis** | Get AI-powered feedback, issues, and improvement tips |
| 3️⃣ | **JD Match** | Paste a job description and see how well your CV matches |
| 4️⃣ | **Interview** | Practice a mock interview and get a final assessment report |

---

### How to get started

1. Go to **Upload CV** in the sidebar
2. Upload your resume file
3. Continue through each step

> **Note:** Start with uploading your CV — it's required for all other modules.
""")

if "cv_id" in st.session_state:
    st.success(f"CV loaded (ID: {st.session_state.cv_id}). Use the sidebar to navigate.")
else:
    st.info("No CV loaded yet. Go to **Upload CV** to start.")
