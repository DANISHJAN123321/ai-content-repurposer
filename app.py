import streamlit as st
import re
from google import genai
import pypdf
import docx

# Optional audio preview dependency
try:
    from gtts import gTTS
    import io
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# 1. Page Configuration
st.set_page_config(
    page_title="AI Content Repurposer Studio Pro",
    page_icon="✨",
    layout="wide"
)

# 2. Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF8C00, #4A90E2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #6C757D;
        margin-bottom: 1.8rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 16px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #4A90E2;
    }
</style>
""", unsafe_allow_html=True)

# 3. Header Section
st.markdown('<div class="main-title">✨ AI Content Repurposer Studio Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Transform raw text, documents, or audio into multi-platform campaigns, image prompts, and audio previews.</div>', unsafe_allow_html=True)

# 4. Sidebar Setup
st.sidebar.title("⚙️ Setup & Keys")
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

if not api_key:
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password", help="Get key at aistudio.google.com")
else:
    st.sidebar.success("✅ Gemini API Key Active")

st.sidebar.markdown("---")
st.sidebar.write("⚡ **Engine:** `gemini-2.5-flash`")

# 5. Helper Functions
def extract_text_from_pdf(file):
    reader = pypdf.PdfReader(file)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_sections(text):
    pattern = r'\[(?:PLATFORM|SECTION):\s*(.*?)\]'
    splits = re.split(pattern, text)
    sections = {}
    if len(splits) > 1:
        for i in range(1, len(splits), 2):
            header = splits[i].strip()
            content = splits[i+1].strip() if (i+1) < len(splits) else ""
            sections[header] = content
    else:
        sections["Generated Output"] = text
    return sections

# 6. Inputs Section
input_type = st.radio(
    "📥 Choose Input Source Type:",
    ["Text Script / Raw Notes", "Upload Document (PDF, DOCX, TXT)", "Upload Audio File (MP3, WAV, M4A)"],
    horizontal=True
)

source_text = ""
uploaded_doc = None
uploaded_audio = None

if input_type == "Text Script / Raw Notes":
    source_text = st.text_area("📝 Source Content / Topic Notes:", height=180, placeholder="Paste your script or draft...")
elif input_type == "Upload Document (PDF, DOCX, TXT)":
    uploaded_doc = st.file_uploader("📄 Select Document:", type=["pdf", "docx", "txt"])
    if uploaded_doc:
        try:
            if uploaded_doc.name.endswith(".pdf"):
                source_text = extract_text_from_pdf(uploaded_doc)
            elif uploaded_doc.name.endswith(".docx"):
                source_text = extract_text_from_docx(uploaded_doc)
            else:
                source_text = uploaded_doc.read().decode("utf-8")
            st.success(f"✅ Loaded {uploaded_doc.name} ({len(source_text.split())} words)")
        except Exception as e:
            st.error(f"Error parsing document: {e}")
else:
    uploaded_audio = st.file_uploader("🎙️ Select Audio File:", type=["mp3", "wav", "m4a"])
    if uploaded_audio:
        st.audio(uploaded_audio, format=uploaded_audio.type)

col1, col2, col3, col4 = st.columns(4)
with col1:
    target_platforms = st.multiselect(
        "🎯 Target Platforms:",
        ["YouTube Short / Video Script", "Instagram Caption & Reels Idea", "TikTok Script & Hook", "LinkedIn Professional Post", "Twitter/X Thread", "Newsletter Summary Email"],
        default=["YouTube Short / Video Script", "Instagram Caption & Reels Idea", "TikTok Script & Hook"]
    )

with col2:
    tone = st.selectbox("🎭 Brand Tone:", ["High Energy & Viral", "Professional & Insightful", "Casual & Conversational", "Storytelling & Educational"])

with col3:
    post_length = st.selectbox("📏 Output Depth:", ["Short & Punchy", "Medium / Standard", "Detailed Longform"], index=1)

with col4:
    target_language = st.selectbox("🌐 Target Language:", ["English", "Spanish (Español)", "Urdu (اردو)", "French (Français)", "German (Deutsch)", "Arabic (العربية)", "Hindi (हिंदी)"], index=0)

c_col1, c_col2, c_col3 = st.columns(3)
with c_col1:
    enable_image_prompts = st.checkbox("🎨 Generate AI Image Prompts", value=True)
with c_col2:
    enable_seo = st.checkbox("🔑 Extract SEO & Hashtags", value=True)
with c_col3:
    enable_speech_preview = st.checkbox("🔊 Enable Audio Speech Preview", value=HAS_GTTS, disabled=not HAS_GTTS)

# 7. Generation Trigger
if st.button("🚀 Repurpose Content Across Platforms", type="primary"):
    if not api_key:
        st.error("⚠️ Gemini API key required.")
    elif input_type in ["Text Script / Raw Notes", "Upload Document (PDF, DOCX, TXT)"] and not source_text.strip():
        st.warning("⚠️ Provide source text or a valid document.")
    elif input_type == "Upload Audio File (MP3, WAV, M4A)" and uploaded_audio is None:
        st.warning("⚠️ Upload an audio file first.")
    elif not target_platforms:
        st.warning("⚠️ Select at least one platform.")
    else:
        try:
            client = genai.Client(api_key=api_key)
            platforms_str = ", ".join(target_platforms)
            
            transcript_instruction = "[SECTION: 🎙️ Raw Audio Transcript]\nProvide a full verbatim transcript of the audio file." if input_type == "Upload Audio File (MP3, WAV, M4A)" else ""
            
            image_prompt_instruction = """
            [SECTION: 🎨 AI Image Prompts (Midjourney / DALL-E 3)]
            Provide 4 prompts wrapped inside markdown code blocks (```):
            1. YouTube Thumbnail (16:9)
            2. Instagram Grid (1:1)
            3. TikTok Cover (9:16)
            4. Detailed DALL-E 3 Prompt
            """ if enable_image_prompts else ""

            seo_instruction = f"[SECTION: SEO Keywords & Hashtags]\nProvide top 10 keywords and platform hashtags in {target_language}." if enable_seo else ""

            prompt = f"""
            Act as a master content strategist. 
            {transcript_instruction}
            Repurpose the input content for these target platforms: {platforms_str}.
            Language: Write all posts/scripts in **{target_language}** (Keep image prompts in English).
            Tone: {tone} | Depth: {post_length}

            STRICT FORMAT: Label every section with `[PLATFORM: Platform Name]` or `[SECTION: Section Name]`.

            {image_prompt_instruction}
            {seo_instruction}
            """

            payload = []
            if input_type == "Upload Audio File (MP3, WAV, M4A)":
                payload.append({"mime_type": uploaded_audio.type or "audio/mp3", "data": uploaded_audio.read()})
                payload.append(prompt)
            else:
                payload.append(f"Source Material:\n{source_text}\n\n{prompt}")

            with st.spinner(f"✨ Generating campaign in {target_language}..."):
                response = client.models.generate_content(model="gemini-2.5-flash", contents=payload)

            st.session_state["generated_output"] = response.text
            st.session_state["parsed_content"] = parse_sections(response.text)
            st.success("✅ Content Generated Successfully!")

        except Exception as e:
            st.error(f"Error during generation: {e}")

# 8. Render Results Dashboard & Interactive Assistant
if "parsed_content" in st.session_state:
    parsed_content = st.session_state["parsed_content"]
    raw_output = st.session_state.get("generated_output", "")
    
    st.markdown("---")
    
    # Strategy Insights Dashboard
    st.subheader("📊 Strategy Insights Dashboard")
    d_col1, d_col2, d_col3 = st.columns(3)
    word_count = len(raw_output.split())
    read_time = round(word_count / 200, 1)
    
    with d_col1:
        st.metric("Total Word Count", f"{word_count} words")
    with d_col2:
        st.metric("Est. Reading Time", f"~{read_time} min")
    with d_col3:
        st.metric("Target Platforms", len([k for k in parsed_content if "SECTION" not in k]))

    # Main Output Tabs
    tab_names = list(parsed_content.keys()) + ["💬 AI Editing Assistant"]
    tabs = st.tabs(tab_names)
    
    for idx, name in enumerate(parsed_content.keys()):
        with tabs[idx]:
            content = parsed_content[name]
