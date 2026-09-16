import streamlit as st
import re
from google import genai
import pypdf
import docx

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

    /* Tab styling overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 16px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Header Section
st.markdown('<div class="main-title">✨ AI Content Repurposer Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Transform raw text, MP3 audio, PDF, or DOCX files into multi-platform social media posts.</div>', unsafe_allow_html=True)

# 4. Sidebar Configuration
st.sidebar.title("⚙️ Setup & Keys")

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
st.sidebar.write("💡 **Tip:** Uses GEMINI-3.6-FLASH for multimodal processing and fast output generation.")

# 5. Main Inputs Selection
input_type = st.radio(
    "📥 Choose Input Source Type:",
    ["Text Script / Raw Notes", "Upload Document (PDF, DOCX, TXT)", "Upload Audio File (MP3, WAV, M4A)"],
    horizontal=True
)

source_text = ""
uploaded_doc = None
uploaded_audio = None

def extract_text_from_pdf(file):
    reader = pypdf.PdfReader(file)
    extracted_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    return extracted_text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

if input_type == "Text Script / Raw Notes":
    source_text = st.text_area(
        "📝 Paste your source text or topic script here:",
        height=200,
        placeholder="Paste your blog post, script, meeting notes, or raw ideas..."
    )
elif input_type == "Upload Document (PDF, DOCX, TXT)":
    uploaded_doc = st.file_uploader(
        "📄 Upload a document (.pdf, .docx, .txt):",
        type=["pdf", "docx", "txt"]
    )
    if uploaded_doc:
        try:
            if uploaded_doc.type == "application/pdf" or uploaded_doc.name.endswith(".pdf"):
                source_text = extract_text_from_pdf(uploaded_doc)
            elif uploaded_doc.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or uploaded_doc.name.endswith(".docx"):
                source_text = extract_text_from_docx(uploaded_doc)
            else:
                source_text = uploaded_doc.read().decode("utf-8")
            
            st.success(f"✅ Successfully read file: {uploaded_doc.name} ({len(source_text.split())} words detected)")
            with st.expander("🔍 Preview Extracted Text"):
                st.text(source_text[:1000] + ("..." if len(source_text) > 1000 else ""))
        except Exception as e:
            st.error(f"Error processing document: {e}")
else:
    uploaded_audio = st.file_uploader(
        "🎙️ Upload an audio recording (.mp3, .wav, .m4a):",
        type=["mp3", "wav", "m4a"]
    )
    if uploaded_audio:
        st.audio(uploaded_audio, format=uploaded_audio.type)

col1, col2, col3, col4 = st.columns(4)

with col1:
    target_platforms = st.multiselect(
        "🎯 Target Platforms:",
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
        "🎭 Brand Tone:",
        ["High Energy & Viral", "Professional & Insightful", "Casual & Conversational", "Storytelling & Educational"]
    )

with col3:
    post_length = st.selectbox(
        "📏 Output Length:",
        [
            "Short & Punchy (Brevity focus)",
            "Medium / Standard (Balanced)",
            "Detailed Longform (In-depth analysis)"
        ],
        index=1
    )

with col4:
    target_language = st.selectbox(
        "🌐 Output Language:",
        [
            "English",
            "Spanish (Español)",
            "Urdu (اردو)",
            "French (Français)",
            "German (Deutsch)",
            "Arabic (العربية)",
            "Hindi (हिंदी)"
        ],
        index=0
    )

enable_seo = st.checkbox("🔑 Generate SEO Keywords & Hashtags Extractor", value=True)

# 6. Helper Function to Parse Platform Sections
def parse_sections(text):
    """Splits generated text by [PLATFORM: ...] or [SECTION: ...] headers."""
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

# 7. Content Generation Logic
if st.button("🚀 Repurpose Content Across Platforms", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API key in the sidebar or save it in secrets.")
    elif input_type in ["Text Script / Raw Notes", "Upload Document (PDF, DOCX, TXT)"] and not source_text.strip():
        st.warning("⚠️ Please provide source text or upload a valid document.")
    elif input_type == "Upload Audio File (MP3, WAV, M4A)" and uploaded_audio is None:
        st.warning("⚠️ Please upload an audio file first.")
    elif not target_platforms:
        st.warning("⚠️ Please select at least one platform.")
    else:
        try:
            client = genai.Client(api_key=api_key)
            
            platforms_str = ", ".join(target_platforms)
            
            seo_instruction = ""
            if enable_seo:
                seo_instruction = f"""
                Also include a dedicated section at the end formatted strictly as:
                [SECTION: SEO Keywords & Hashtags]
                Provide all keywords and hashtags in {target_language}:
                1. Top 10 High-Volume SEO Keywords
                2. Search Intent / Long-Tail Keywords
                3. Trending Hashtags organized by platform
                """

            prompt = f"""
            Act as a world-class social media strategist and content creator.
            
            Repurpose the core ideas from the provided input into content customized specifically for these platforms: {platforms_str}.
            
            IMPORTANT: Write ALL response content, hooks, captions, scripts, and hashtags entirely in **{target_language}**.
            
            Tone of Voice: {tone}
            Output Length Preference: {post_length}
            
            Length Guidelines:
            - If 'Short & Punchy': Keep posts tight, bullet-point focused, quick hooks, minimal fluff.
            - If 'Medium / Standard': Standard post lengths typical for each social network.
            - If 'Detailed Longform': Expand deeply on points, provide rich context, extended storytelling, and comprehensive explanations.

            STRICT FORMATTING RULE:
            You MUST label every single platform's content with this exact header format in English before the content starts (so tabs render properly):
            [PLATFORM: Platform Name]

            Instructions per platform (translate all output to {target_language}):
            - YouTube Short / Video Script: Include visual hook, video script (tailored to {post_length}), and title ideas.
            - Instagram Caption & Reels Idea: Include caption, visual scene description, and hashtags.
            - TikTok Script & Hook: Focus on fast-paced hook (0-3s), main script, and text overlays.
            - LinkedIn Professional Post: Professional formatting with line breaks and actionable takeaways.
            - Twitter/X Thread: Concise or extended thread format depending on length selected.
            - Newsletter Summary Email: Catchy subject line and newsletter copy.

            {seo_instruction}
            """

            contents_payload = []

            if input_type == "Upload Audio File (MP3, WAV, M4A)":
                audio_bytes = uploaded_audio.read()
                mime_type = uploaded_audio.type or "audio/mp3"
                contents_payload.append({
                    "mime_type": mime_type,
                    "data": audio_bytes
                })
                contents_payload.append(prompt)
            else:
                contents_payload.append(f"Source Material:\n{source_text}\n\n{prompt}")

            with st.spinner(f"✨ Processing input and generating {post_length} content in {target_language}..."):
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=contents_payload
                )
            
            st.success(f"✅ Content Generated Successfully in {target_language}!")
            st.markdown("---")
            
            output_text = response.text
            parsed_content = parse_sections(output_text)
            
            tab_names = list(parsed_content.keys())
            
            if tab_names:
                tabs = st.tabs(tab_names)
                for tab, name in zip(tabs, tab_names):
                    with tab:
                        st.markdown(parsed_content[name])
            else:
                st.markdown(output_text)
            
            st.markdown("---")
            st.download_button(
                label=f"📥 Download All Output ({target_language}) (.txt)",
                data=output_text,
                file_name=f"repurposed_content_{target_language.lower().split()[0]}.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
