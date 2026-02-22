import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from frontend.api_client import start_interview, send_interview_message, finish_interview

st.set_page_config(page_title="Interview", page_icon="🎤", layout="wide")
st.title("🎤 Mock Interview Practice")

if "cv_id" not in st.session_state:
    st.warning("No CV loaded. Please go to **Upload CV** first.")
    st.stop()


def _render_final_report(report: dict):
    st.markdown("---")
    st.header("📊 Final Interview Report")

    overall = report.get("overall_score", 0)
    color = "#4caf50" if overall >= 4 else "#ff9800" if overall >= 3 else "#f44336"
    st.markdown(
        f'<div style="text-align:center;background:{color};color:white;padding:20px;border-radius:10px;font-size:2.5em;font-weight:bold;margin-bottom:20px">{overall:.1f} / 5.0</div>',
        unsafe_allow_html=True,
    )

    criteria = report.get("criteria_scores", {})
    if criteria:
        st.subheader("Criteria Scores")
        criteria_labels = {
            "relevance": "Relevance",
            "clarity": "Clarity",
            "structure": "Structure (STAR)",
            "technical_depth": "Technical Depth",
            "communication": "Communication",
        }
        cols = st.columns(len(criteria))
        for i, (key, label) in enumerate(criteria_labels.items()):
            score = criteria.get(key, 0)
            with cols[i]:
                st.metric(label, f"{score}/5")
                st.progress(score / 5)

    col1, col2 = st.columns(2)
    with col1:
        strengths = report.get("strengths", [])
        st.subheader(f"💪 Strengths ({len(strengths)})")
        for s in strengths:
            st.success(f"• {s}")

    with col2:
        weaknesses = report.get("weaknesses", [])
        st.subheader(f"🔧 Areas to Improve ({len(weaknesses)})")
        for w in weaknesses:
            st.warning(f"• {w}")

    recs = report.get("recommendations", [])
    if recs:
        st.subheader("📋 Recommendations")
        for rec in recs:
            st.info(f"→ {rec}")

    improved = report.get("improved_answers", [])
    if improved:
        st.subheader("✏️ Example Improved Answers")
        for item in improved:
            with st.expander(f"Q: {item.get('question', '')[:80]}..."):
                st.markdown("**Your answer:**")
                st.markdown(
                    f'<div style="background:#ffebee;padding:10px;border-radius:5px">{item.get("original", "")}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("**Improved answer:**")
                st.markdown(
                    f'<div style="background:#e8f5e9;padding:10px;border-radius:5px">{item.get("improved", "")}</div>',
                    unsafe_allow_html=True,
                )


# ── Interview Setup ───────────────────────────────────────────────────────────

if "session_id" not in st.session_state or st.session_state.get("interview_finished"):
    if st.session_state.get("interview_finished"):
        _render_final_report(st.session_state.get("final_report", {}))
        st.markdown("---")
        if st.button("Start a New Interview", type="primary"):
            for key in ["session_id", "interview_messages", "current_question", "interview_finished",
                        "final_report", "question_number", "total_questions", "interview_is_last"]:
                st.session_state.pop(key, None)
            st.rerun()
        st.stop()

    st.subheader("Configure Interview Session")

    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("Experience Level", ["junior", "mid", "senior"], index=0)
        num_questions = st.slider("Number of Questions", min_value=5, max_value=15, value=10)

    with col2:
        jd_id = st.session_state.get("jd_id")
        if jd_id:
            st.success(f"Job Description loaded (ID: {jd_id})")
        else:
            st.info("No JD loaded. Interview will be based on your CV only.")
        company_info = st.text_area(
            "Company Info (optional)",
            placeholder="Brief info about the company, product, or mission...",
            height=100,
        )

    if st.button("Start Interview", type="primary"):
        with st.spinner("Generating interview questions..."):
            try:
                result = start_interview(
                    cv_id=st.session_state["cv_id"],
                    jd_id=jd_id,
                    company_info=company_info.strip() or None,
                    level=level,
                    num_questions=num_questions,
                )
                st.session_state["session_id"] = result["session_id"]
                st.session_state["current_question"] = result["question"]
                st.session_state["question_number"] = result["question_number"]
                st.session_state["total_questions"] = result["total_questions"]
                st.session_state["interview_messages"] = [
                    {"role": "assistant", "content": result["question"]}
                ]
                st.session_state["interview_is_last"] = False
                st.session_state["interview_finished"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Failed to start interview: {e}")
    st.stop()

# ── Active Interview Chat ────────────────────────────────────────────────────

session_id = st.session_state["session_id"]
messages = st.session_state.get("interview_messages", [])
q_num = st.session_state.get("question_number", 1)
total_q = st.session_state.get("total_questions", 10)
is_last = st.session_state.get("interview_is_last", False)

st.markdown(f"**Question {q_num} of {total_q}**")
progress_pct = (q_num - 1) / total_q if total_q > 0 else 0
st.progress(progress_pct)

# Display chat history
for msg in messages:
    with st.chat_message(msg["role"]):
        content = msg["content"]
        # Distinguish feedback from questions
        if content.startswith("[Feedback]"):
            st.markdown(f"*{content.replace('[Feedback] ', '')}*")
        else:
            st.markdown(content)

# Input area
if not is_last:
    answer = st.chat_input("Type your answer here...")

    if answer:
        # Show user message immediately
        messages.append({"role": "user", "content": answer})
        st.session_state["interview_messages"] = messages

        with st.spinner("Getting feedback..."):
            try:
                resp = send_interview_message(session_id, answer)

                feedback = resp["feedback"]
                messages.append({"role": "assistant", "content": f"[Feedback] {feedback}"})

                if resp["is_last"]:
                    st.session_state["interview_is_last"] = True
                    st.session_state["question_number"] = resp["question_number"]
                else:
                    next_q = resp["next_question"]
                    messages.append({"role": "assistant", "content": next_q})
                    st.session_state["question_number"] = resp["question_number"]
                    st.session_state["current_question"] = next_q

                st.session_state["interview_messages"] = messages
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.success("All questions answered! Click below to get your final report.")
    if st.button("Get Final Report", type="primary"):
        with st.spinner("Generating your final interview report..."):
            try:
                result = finish_interview(session_id)
                st.session_state["final_report"] = result["report"]
                st.session_state["interview_finished"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate report: {e}")
