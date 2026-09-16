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

# Page setup
st.set_page_config(page_title="AI Content Repurposer Studio", page_icon="🎬", layout="wide")

# Helper function for PDF export
def generate_pdf_bytes(title, content):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, spaceAfter=12)
    heading_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=12, leading=15, spaceBefore=10, spaceAfter=5)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['BodyText'], fontSize=10, leading=14, spaceAfter=6)

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

def get_youtube_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url

# Header
st.title("🎬 AI Content Repurposer Studio")
st.write("Transform text, documents, or YouTube transcripts into multi-platform social media scripts.")

# Sidebar
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    target_language = st.selectbox(
        "Output Language",
        ["English", "Urdu (اردو)", "Spanish (Español)", "French (Français)", "German (Deutsch)", "Hindi (हिंदी)"]
    )
    selected_platforms = st.multiselect(
        "Output Platforms",
        ["YouTube Shorts", "TikTok Script", "Instagram Reel", "Twitter/X Thread", "LinkedIn Article"],
        default=["YouTube Shorts", "TikTok Script", "Twitter/X Thread"]
    )

# Input Section
input_type = st.radio("Select Input Source:", ["Text Input", "File Upload (.pdf, .docx, .txt)", "YouTube URL"], horizontal=True)

raw_text = ""

if input_type == "Text Input":
    raw_text = st.text_area("Paste content here:", height=200)

elif input_type == "File Upload (.pdf, .docx, .txt)":
    uploaded_file = st.file_uploader("Upload file", type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".txt"):
            raw_text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(".pdf"):
            pdf_reader = PdfReader(uploaded_file)
            raw_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        elif uploaded_file.name.endswith(".docx"):
            doc = Document(uploaded_file)
            raw_text = "\n".join([p.text for p in doc.paragraphs])
        st.success(f"Loaded: {uploaded_file.name}")

elif input_type == "YouTube URL":
    yt_url = st.text_input("Paste YouTube Video URL:")
    if yt_url:
        try:
            video_id = get_youtube_id(yt_url)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            raw_text = " ".join([t['text'] for t in transcript_list])
            st.success(f"Transcript loaded from Video ID: {video_id}")
        except Exception as e:
            st.error(f"Could not retrieve transcript: {e}")

# Action Button
if st.button("Generate Social Scripts"):
    if not api_key:
        st.error("Please provide a valid Gemini API Key in the sidebar.")
    elif not raw_text.strip():
        st.warning("Please enter or upload source content.")
    else:
        with st.spinner("Generating scripts..."):
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
                2. Main content/script formatted with timestamps, visual prompts, or slide markers.
                3. Clear Call to Action (CTA) and relevant hashtags.
                
                Format response cleanly with headers: [PLATFORM: <Name>]
                """

                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                )

                st.session_state['output_text'] = response.text

            except Exception as gen_err:
                st.error(f"Generation failed: {gen_err}")

# Output Section
if 'output_text' in st.session_state:
    output_text = st.session_state['output_text']
    
    st.subheader("Generated Scripts")
    st.markdown(output_text)

    # Audio Narration
    st.divider()
    st.subheader("Audio Preview")
    
    lang_codes = {"English": "en", "Spanish (Español)": "es", "Urdu (اردو)": "ur", "French (Français)": "fr", "German (Deutsch)": "de", "Hindi (हिंदी)": "hi"}
    tts_lang = lang_codes.get(target_language, "en")

    if st.button("Generate Audio Preview"):
        with st.spinner("Creating audio..."):
            try:
                tts = gTTS(text=output_text[:1000], lang=tts_lang, slow=False)
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                st.audio(audio_fp, format="audio/mp3")
            except Exception as tts_err:
                st.error(f"Audio error: {tts_err}")

    # Exports
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label=f"Download TXT ({target_language})",
            data=output_text,
            file_name=f"repurposed_content.txt",
            mime="text/plain"
        )

    with col2:
        pdf_data = generate_pdf_bytes(
            title=f"AI Content Repurposer Studio - {target_language}",
            content=output_text
        )
        st.download_button(
            label=f"Download PDF ({target_language})",
            data=pdf_data,
            file_name=f"repurposed_content.pdf",
            mime="application/pdf"
        )
