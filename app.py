import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI Content Repurposer", page_icon="📝")

st.title("📝 AI Content Repurposer")
st.write("Turn long content into posts for LinkedIn, Twitter, or Email.")

# Sidebar for API Key
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

# Main Inputs
source_text = st.text_area("Paste your source text here:", height=200)

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("Select Platform", ["LinkedIn Post", "Twitter Thread", "Summary Email"])
with col2:
    tone = st.selectbox("Select Tone", ["Professional", "Casual", "Motivational"])

if st.button("Generate Content"):
    if not api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not source_text:
        st.warning("Please paste some text to transform.")
    else:
        try:
            client = OpenAI(api_key=api_key)
            prompt = f"Repurpose the following content into a {platform} with a {tone} tone:\n\n{source_text}"
            
            with st.spinner("Generating content..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                
            st.success("Generated Content:")
            st.write(response.choices[0].message.content)
        except Exception as e:
            st.error(f"An error occurred: {e}")
