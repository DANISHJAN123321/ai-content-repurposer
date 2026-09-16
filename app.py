import io
import os
import streamlit as st
from google import genai
from pypdf import PdfReader
from docx import Document
from youtube_transcript_api import YouTubeTranscriptApi
from gtts import gTTS
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Content Repurposer Studio",
    page_icon="🎬",
    layout="wide"
)

# --- Custom CSS Styling Injection ---
st.markdown("""
<style>
    /* Main Page Styling */
    .stApp {
        background-color: #F8FAFC;
    }
    .custom-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        background: linear-gradient(90deg, #2563EB, #7C3AED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .custom-card {
        background-color: #FFFFFF;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    /* Streamlit Button Styling */
    div.stButton > button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #1D4ED8;
        color: white;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Function: PDF Generator ---
def generate_pdf_bytes(title, content):
    """Converts output markdown text into a formatted PDF byte buffer."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontSize=20, leading=24, textColor=colors.HexColor('#1E3A8A'), spaceAfter=15
    )
    heading_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'],
        fontSize=13, leading=16, textColor=colors.HexColor('#2563EB'), spaceBefore=12, spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyTextCustom', parent=styles['BodyText'],
        fontSize=10, leading=14, textColor=colors.HexColor('#1F2937'), spaceAfter=8
    )

    story = [Paragraph(title, title_style), Spacer(1, 10)]
    
    for line in content.split('\n'):
        line_clean = line.strip()
        if not line_clean:
            story.append(Spacer(1, 4))
            continue
        safe_line = line_clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        if safe_line.startswith('#') or safe_line.startswith('[PLATFORM:'):
            header_text = safe_line.lstrip('#').replace('[', '').replace(']', '').strip()
            story.append(Paragraph(header_text, heading_style))
        else:
            story.append(Paragraph(safe_line, body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- Helper Function: Extract YouTube Video ID ---
def get_youtube_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url

# --- Header Section ---
st.markdown('<div class="custom-header">🎬 AI Content Repurposer Studio</div>', unsafe_allow_html=True)
st.markdown("<p style='color: #64748B;'>Transform long-form text, documents, or YouTube transcripts into multi-platform social media scripts instantly.</p>", unsafe_allow_html=True)

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google AI Studio API key")
    
    target_language = st.selectbox(
        "🌐 Output Language",
        ["English", "Urdu (اردو)", "Spanish (Español)", "French (Français)", "German (Deutsch)", "Hindi (हिंदी)"]
    )
    
    selected_platforms = st.multiselect(
        "📱 Select Output Platforms",
        ["YouTube Shorts", "TikTok Script", "Instagram Reel", "Twitter/X Thread", "LinkedIn Article"],
        default=["YouTube Shorts", "TikTok Script", "Twitter/X Thread"]
    )

# --- Main Input Options ---
st.markdown('<div class="custom-card">', unsafe_allow_html=True)
input_type = st.radio("Select Source Material Type:", ["Text Input", "File Upload (.pdf, .docx, .txt)", "YouTube URL"], horizontal=True)

raw_text = ""

if input_type == "Text Input":
    raw_text = st.text_area("Paste your article, video transcript, or document content here:", height=200)

elif input_type == "File Upload (.pdf, .docx, .txt)":
    uploaded_file = st.file_uploader("Upload document", type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".txt"):
            raw_text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(".pdf"):
            pdf_reader = PdfReader(uploaded_file)
            raw_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        elif uploaded_file.name.endswith(".docx"):
            doc = Document(uploaded_file)
            raw_text = "\n".join([p.text for p in doc.paragraphs])
        st.success(f"✅ Loaded file: {uploaded_file.name} ({len(raw_text)} characters extracted)")

elif input_type == "YouTube URL":
    yt_url = st.text_input("Paste YouTube Video Link:")
    if yt_url:
        try:
            video_id = get_youtube_id(yt_url)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            raw_text = " ".join([t['text'] for t in transcript_list])
            st.success(f"✅ Extracted transcript from YouTube video ID: {video_id}")
        except Exception as e:
            st.error(f"Could not retrieve YouTube transcript: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# --- Processing & Generation ---
if st.button("🚀 Generate Social Scripts", use_container_width=True):
    if not api_key:
        st.error("Please provide a valid Gemini API Key in the sidebar.")
    elif not raw_text.strip():
        st.warning("Please provide source material before generating.")
    else:
        with st.spinner("Analyzing content and generating social media scripts..."):
            try:
                client = genai.Client(api_key=api_key)
                
                prompt = f"""
                You are an expert social media content creator and copywriter.
                Repurpose the following content into structured scripts/posts for these platforms: {', '.join(selected_platforms)}.
                
                Target Language: {target_language}
                
                SOURCE CONTENT:
                {raw_text[:8000]}
                
                For each requested platform, provide:
                1. A strong hook to capture attention.
                2. Main content/script formatted with timestamps, visual prompts, or slide markers where applicable.
                3. Clear Call to Action (CTA) and relevant hashtags.
                
                Format the final response cleanly using distinct headers: [PLATFORM: <Name>]
                """

                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                )

                output_text = response.text
                st.session_state['output_text'] = output_text

            except Exception as gen_err:
                st.error(f"Generation failed: {gen_err}")

# --- Output & Export Display Section ---
if 'output_text' in st.session_state:
    output_text = st.session_state['output_text']
    
    st.markdown("### 📝 Generated Scripts")
    st.markdown(output_text)

    # --- Text-To-Speech Audio Preview ---
    st.markdown("---")
    st.markdown("### 🎧 Listen to Script Preview")
    
    lang_codes = {
        "English": "en",
        "Spanish (Español)": "es",
        "Urdu (اردو)": "ur",
        "French (Français)": "fr",
        "German (Deutsch)": "de",
        "Hindi (हिंदी)": "hi"
    }
    tts_lang = lang_codes.get(target_language, "en")
    preview_text = output_text[:1000]

    if st.button("🔊 Generate Audio Narration Preview"):
        with st.spinner("Synthesizing audio preview..."):
            try:
                tts = gTTS(text=preview_text, lang=tts_lang, slow=False)
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                st.audio(audio_fp, format="audio/mp3")
                st.success("✅ Audio ready! Click play above.")
            except Exception as tts_err:
                st.error(f"Audio generation failed: {tts_err}")

    # --- Export Download Options ---
    st.markdown("---")
    d_col1, d_col2 = st.columns(2)

    with d_col1:
        st.download_button(
            label=f"📥 Download Raw TXT ({target_language})",
            data=output_text,
            file_name=f"repurposed_content_{target_language.lower().split()[0]}.txt",
            mime="text/plain",
            use_container_width=True
        )

    with d_col2:
        pdf_data = generate_pdf_bytes(
            title=f"AI Content Repurposer Studio - {target_language}",
            content=output_text
        )
        st.download_button(
            label=f"📄 Download PDF Document ({target_language})",
            data=pdf_data,
            file_name=f"repurposed_content_{target_language.lower().split()[0]}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
