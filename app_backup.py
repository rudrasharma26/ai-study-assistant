import streamlit as st
from backend.ai_handler import explain_topic

# Page Config
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>

.main {
    background-color: #0E1117;
}

h1 {
    color: #4F8BF9;
    text-align: center;
}

.stTextInput > div > div > input {
    border-radius: 12px;
    padding: 10px;
}

</style>
""", unsafe_allow_html=True)

# Header
st.title("🧠 AI Study Assistant")
st.markdown(
    "Learn smarter. Understand concepts, summaries and quizzes instantly."
)

st.divider()

# Input Box
topic = st.text_input(
    "📚 Enter a topic to study",
    placeholder="Example: PCA, Cloud Computing, DSA"
)

# Generate Button
if st.button("✨ Generate Study Material"):

    if topic.strip() == "":
        st.warning("Please enter a topic first.")

    else:

        with st.spinner("Thinking like a genius... 🧠"):

            result = explain_topic(topic)

        st.success("Study material generated successfully!")

        st.markdown("## 📖 Study Material")

        # Split sections
        sections = result.split("###")

        tab1, tab2, tab3, tab4 = st.tabs([
            "📘 Explanation",
            "📝 Summary",
            "⭐ Important Points",
            "🧠 Quiz"
        ])

        with tab1:
            if len(sections) > 1:
                st.markdown(sections[1])
            else:
                st.markdown(result)

        with tab2:
            if len(sections) > 2:
                st.markdown(sections[2])

        with tab3:
            if len(sections) > 3:
                st.markdown(sections[3])

        with tab4:
            if len(sections) > 4:
                st.markdown(sections[4])