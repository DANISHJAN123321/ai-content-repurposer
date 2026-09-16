import streamlit as st
from openai import OpenAI

# 1. Set Page Title & Layout
st.set_page_config(page_title="AI Content Repurposer", page_icon="📝", layout="wide")

# 2. Sidebar for API Key Input
st.sidebar.title("⚙️ Settings")
st.sidebar.write("Get your API key from [platform.openai.com](https://platform.openai.com)")

api_key = st.sidebar.text_input(
    "Enter OpenAI API Key",
    type="password",
    help="Paste your sk-... key here"
)

# 3. Main Screen UI
st.title("📝 AI Content Repurposer")
st.write("Paste your raw article, notes, or transcript below to transform it for social platforms.")

source_text = st.text_area("Source Text", height=220, placeholder="Paste your raw text here...")

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("Select Target Platform", ["LinkedIn Post", "Twitter Thread", "Newsletter Email"])
with col2:
    tone = st.selectbox("Select Tone of Voice", ["Professional", "Conversational", "Engaging", "Short & Punchy"])

# 4. Processing Logic
if st.button("🚀 Repurpose Content", type="primary"):
    if not api_key.strip():
        st.sidebar.error("⚠️ Please enter your OpenAI API key in the sidebar on the left!")
    elif not source_text.strip():
        st.warning("⚠️ Please paste some text into the box above before generating.")
    else:
        try:
            client = OpenAI(api_key=api_key)
            prompt = f"Repurpose the following content into a {platform} with a {tone} tone:\n\n{source_text}"
            
            with st.spinner("Generating your post..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                
            st.success("✅ Output Generated:")
            st.markdown(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Error: {e}")
