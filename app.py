import streamlit as st
from google import genai

# Page setup
st.set_page_config(page_title="Gemini Streamlit App", page_icon="🤖")
st.title("🤖 Chat with Gemini")

# Retrieve API key from secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Missing GEMINI_API_KEY in secrets. Please set it in secrets.toml or Streamlit Cloud.")
    st.stop()

# Initialize Gemini client
client = genai.Client(api_key=api_key)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process user input
if prompt := st.chat_input("Ask something..."):
    # Render user prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate model response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Uses gemini-2.5-flash (free tier eligible)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                bot_response = response.text
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            except Exception as e:
                st.error(f"Error generating response: {e}")
