import streamlit as st
from google import genai

# 1. Page Configuration
st.set_page_config(
    page_title="AI Content Repurposer Studio",
    page_icon="✨",
    layout="wide"
)

# 2. Custom CSS for Stylish UI
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF8C00, #4A90E2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* Subtitle styling */
    .sub-title {
        font-size: 1.1rem;
        color: #6C757D;
        margin-bottom: 2rem;
    }
    
    /* Output container cards */
    .content-card {
        background-color: #F8F9FA;
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #FF4B4B;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Header Section
st.markdown('<div class="main-title">✨ AI Content Repurposer Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Transform your article, transcript, or raw notes into platform-ready social posts in seconds.</div>', unsafe_allow_html=True)

# 4. Sidebar Configuration
st.sidebar.title("⚙️ Setup & Keys")

# Get API key from Streamlit secrets or user input
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

if not api_key:
    api_key = st.sidebar.text_input(
        "Enter Google Gemini API Key",
        type="password",
        help="Get your key at aistudio.google.com"
    )
else:
    st.sidebar.success("✅ Gemini API Key detected!")

st.sidebar.markdown("---")
st.sidebar.write("💡 **Tip:** GEMINI-2.0-FLASH is fast and free to test via Google AI Studio.")

# 5. Main Inputs
source_text = st.text_area(
    "📝 Paste your source text or topic script here:",
    height=200,
    placeholder="Paste your blog post, script, meeting notes, or raw ideas..."
)

col1, col2 = st.columns(2)

with col1:
    target_platforms = st.multiselect(
        "🎯 Select Target Platforms:",
        [
            "YouTube Short / Video Script",
            "Instagram Caption & Reels Idea",
            "TikTok Script & Hook",
            "LinkedIn Professional Post",
            "Twitter/X Thread",
            "Newsletter Summary Email"
        ],
        default=["YouTube Short / Video Script", "Instagram Caption & Reels Idea", "TikTok Script & Hook"]
    )

with col2:
    tone = st.selectbox(
        "🎭 Select Brand Tone:",
        ["High Energy & Viral", "Professional & Insightful", "Casual & Conversational", "Storytelling & Educational"]
    )

# 6. Content Generation Logic
if st.button("🚀 Repurpose Content Across Platforms", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API key in the sidebar or save it in secrets.")
    elif not source_text.strip():
        st.warning("⚠️ Please paste some source text first.")
    elif not target_platforms:
        st.warning("⚠️ Please select at least one platform.")
    else:
        try:
            client = genai.Client(api_key=api_key)
            
            platforms_str = ", ".join(target_platforms)
            prompt = f"""
            Act as a world-class social media strategist and content creator.
            repurpose the following source text into content customized specifically for these platforms: {platforms_str}.
            
            Tone of Voice: {tone}
            
            Source Text:
            {source_text}

            Instructions per platform selected:
            - YouTube: Include a strong visual hook, short video script, and video title ideas.
            - Instagram: Include an engaging caption, visual scene description for Reels, and 5 relevant hashtags.
            - TikTok: Focus on a fast-paced hook (0-3s), main script, and text overlay ideas.
            - LinkedIn: Professional formatting with line breaks, clear takeaways, and actionable advice.
            - Twitter/X: A concise 3-tweet thread format.
            - Email: Catchy subject line and punchy newsletter copy.

            Clearly divide each platform's output with section headers starting with '[PLATFORM: name]'.
            """
            
            with st.spinner("✨ Crafting multi-platform content with Gemini..."):
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            
            st.success("✅ Content Generated Successfully!")
            st.markdown("---")
            
            output_text = response.text
            
            # Display generated content
            st.subheader("📲 Generated Outputs")
            st.markdown(output_text)
            
            st.markdown("---")
            st.download_button(
                label="📥 Download All Output (.txt)",
                data=output_text,
                file_name="repurposed_content.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
