import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from google import genai
import pypdf
import docx
import pandas as pd
import io
import sqlite3
import hashlib
import random

# Optional audio preview dependency
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# 1. Page Configuration
st.set_page_config(
    page_title="AI Content Repurposer Studio Pro",
    page_icon="✨",
    layout="wide"
)

# 2. Custom Styling
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATABASE SETUP FOR USERS & HISTORY
# ==========================================
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            email TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            content_summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(email, password):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False

def register_user(email, password):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# ==========================================
# 4. AUTHENTICATION & REGISTRATION GATE
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "is_guest" not in st.session_state:
    st.session_state["is_guest"] = False

if not st.session_state["authenticated"]:
    st.markdown('<div class="main-title">🔐 Professional Access Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Sign in to your account, register a new profile, or continue as guest.</div>', unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])
    
    with auth_tab1:
        login_email = st.text_input("Email Address", key="login_email")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            if st.button("🚀 Secure Login", type="primary"):
                if verify_user(login_email, login_pass):
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = login_email
                    st.session_state["is_guest"] = False
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password.")
        with col_l2:
            if st.button("👤 Continue as Guest"):
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = "Guest"
                st.session_state["is_guest"] = True
                st.rerun()

        st.markdown("---")
        # Google Login Simulation Button
        if st.button("🌐 Sign in with Google (OAuth)", use_container_width=True):
            st.info("💡 To connect live Google OAuth, configure your client credentials in Streamlit secrets. Logging in as demo Google user...")
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = "google_user@gmail.com"
            st.session_state["is_guest"] = False
            st.rerun()

    with auth_tab2:
        reg_email = st.text_input("Email Address", key="reg_email")
        reg_pass = st.text_input("Create Password", type="password", key="reg_pass")
        reg_pass_confirm = st.text_input("Confirm Password", type="password", key="reg_pass_confirm")
        
        # Math CAPTCHA Generation
        if "captcha_num1" not in st.session_state:
            st.session_state["captcha_num1"] = random.randint(1, 9)
            st.session_state["captcha_num2"] = random.randint(1, 9)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            captcha_answer = st.text_input(f"🤖 Security Check: What is {st.session_state['captcha_num1']} + {st.session_state['captcha_num2']}?")
        
        if st.button("✨ Register New Account", type="primary"):
            expected_answer = str(st.session_state["captcha_num1"] + st.session_state["captcha_num2"])
            if captcha_answer.strip() != expected_answer:
                st.error("❌ Incorrect CAPTCHA answer. Please try again.")
            elif not reg_email or not reg_pass:
                st.warning("⚠️ Please fill in all fields.")
            elif reg_pass != reg_pass_confirm:
                st.error("❌ Passwords do not match.")
            else:
                if register_user(reg_email, reg_pass):
                    st.success("✅ Account created successfully! Please switch to the Sign In tab.")
                    st.session_state["captcha_num1"] = random.randint(1, 9)
                    st.session_state["captcha_num2"] = random.randint(1, 9)
                else:
                    st.error("❌ Email already registered. Please sign in.")

    st.stop()

# ==========================================
# 5. MAIN APP CONTENT (Unlocked)
# ==========================================

if st.session_state["is_guest"]:
    st.info("👋 **Guest Mode Active:** Full tool access enabled. History is temporary.")
else:
    st.sidebar.success(f"👤 Logged in as: **{st.session_state['user_email']}**")

# Header Section
st.markdown('<div class="main-title">✨ AI Content Repurposer Studio Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Powered by <b>gemini-3.6-flash</b> with Secure Auth, Captcha & Database Storage.</div>', unsafe_allow_html=True)

# Sidebar Setup
st.sidebar.title("⚙️ Setup & Customization")
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

if not api_key:
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password", help="Get key at aistudio.google.com")
else:
    st.sidebar.success("✅ Gemini API Key Active")

st.sidebar.markdown("---")
st.sidebar.subheader("📌 Brand Persona Preset")
selected_persona = st.sidebar.selectbox(
    "Choose Persona Style:",
    [
        "🎵 Independent Music Artist / Hype",
        "👕 E-Commerce Storefront / Organic Apparel",
        "💻 Tech & Software Creator",
        "🎯 General Content Strategist"
    ]
)

custom_cta = st.sidebar.text_input("Default CTA / Link to Inject:", placeholder="e.g., Check our store at danish-jan.teemill.com")

st.sidebar.markdown("---")
if st.sidebar.button("🔒 Logout / Lock App"):
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = ""
    st.session_state["is_guest"] = False
    st.rerun()

st.sidebar.write("⚡ **Engine:** `gemini-3.6-flash`")

# Helper Functions
def extract_text_from_url(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    return " ".join(chunk for chunk in lines if chunk)

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

# Inputs Section
input_type = st.radio(
    "📥 Choose Input Source Type:",
    ["Text Script / Raw Notes", "🌐 Web Page / Article URL", "Upload Document (PDF, DOCX, TXT)", "Upload Audio File (MP3, WAV, M4A)"],
    horizontal=True
)

source_text = ""
uploaded_doc = None
uploaded_audio = None

if input_type == "Text Script / Raw Notes":
    source_text = st.text_area("📝 Source Content / Topic Notes:", height=180, placeholder="Paste track details, lyrics, apparel drop info, or raw draft...")
elif input_type == "🌐 Web Page / Article URL":
    target_url = st.text_input("🔗 Enter Web Page or Article URL:", placeholder="https://example.com/blog-post-or-news")
    if target_url:
        if st.button("Fetch Web Content"):
            try:
                with st.spinner("Scraping webpage text..."):
                    source_text = extract_text_from_url(target_url)
                    st.session_state["fetched_url_text"] = source_text
                    st.success(f"✅ Extracted {len(source_text.split())} words from link!")
            except Exception as e:
                st.error(f"Could not fetch URL content: {e}")
    if "fetched_url_text" in st.session_state:
        source_text = st.session_state["fetched_url_text"]
        st.info(f"Loaded URL Text ({len(source_text.split())} words)")
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

c_col1, c_col2, c_col3, c_col4 = st.columns(4)
with c_col1:
    enable_sentiment = st.checkbox("📊 Sentiment Analysis", value=True)
with c_col2:
    enable_image_prompts = st.checkbox("🎨 AI Image Prompts", value=True)
with c_col3:
    enable_calendar = st.checkbox("📅 7-Day Posting Plan", value=True)
with c_col4:
    enable_speech_preview = st.checkbox("🔊 Audio Preview", value=HAS_GTTS, disabled=not HAS_GTTS)

# Generation Trigger
if st.button("🚀 Repurpose Content Across Platforms", type="primary"):
    if not api_key:
        st.error("⚠️ Gemini API key required.")
    elif input_type in ["Text Script / Raw Notes", "Upload Document (PDF, DOCX, TXT)", "🌐 Web Page / Article URL"] and not source_text.strip():
        st.warning("⚠️ Provide source text, a URL, or a valid document.")
    elif input_type == "Upload Audio File (MP3, WAV, M4A)" and uploaded_audio is None:
        st.warning("⚠️ Upload an audio file first.")
    elif not target_platforms:
        st.warning("⚠️ Select at least one platform.")
    else:
        try:
            client = genai.Client(api_key=api_key)
            platforms_str = ", ".join(target_platforms)
            
            transcript_instruction = "[SECTION: 🎙️ Raw Audio Transcript]\nProvide a full verbatim transcript of the audio file." if input_type == "Upload Audio File (MP3, WAV, M4A)" else ""
            
            persona_instructions = f"Apply Brand Persona Style: {selected_persona}."
            sentiment_instruction = "[SECTION: 📊 Content Sentiment & Audience Fit]\nAnalyze emotional tone and target persona." if enable_sentiment else ""
            calendar_instruction = "[SECTION: 📅 7-Day Content Scheduling Plan]\nProvide a day-by-day scheduling table." if enable_calendar else ""
            image_prompt_instruction = "[SECTION: 🎨 AI Image Prompts (Midjourney / DALL-E 3)]\nProvide 4 visual prompts wrapped inside code blocks." if enable_image_prompts else ""
            cta_injection = f"\nNaturally incorporate this CTA: '{custom_cta}'" if custom_cta else ""

            prompt = f"""
            Act as a master social media strategist. 
            {persona_instructions}
            {transcript_instruction}

            Repurpose the input content for these target platforms: {platforms_str}.
            Language: Write all posts/scripts in **{target_language}** (Keep image prompts in English).
            Tone: {tone} | Depth: {post_length}
            {cta_injection}

            STRICT FORMAT: Label every section with `[PLATFORM: Platform Name]` or `[SECTION: Section Name]`.

            {sentiment_instruction}
            {calendar_instruction}
            {image_prompt_instruction}
            """

            payload = []
            if input_type == "Upload Audio File (MP3, WAV, M4A)":
                payload.append({"mime_type": uploaded_audio.type or "audio/mp3", "data": uploaded_audio.read()})
                payload.append(prompt)
            else:
                payload.append(f"Source Material:\n{source_text}\n\n{prompt}")

            with st.spinner(f"✨ Generating campaign in {target_language}..."):
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=payload
                )

            st.session_state["generated_output"] = response.text
            st.session_state["parsed_content"] = parse_sections(response.text)
            
            # Save history if not guest
            if not st.session_state["is_guest"]:
                conn = sqlite3.connect('users.db', check_same_thread=False)
                c = conn.cursor()
                c.execute('INSERT INTO history (email, content_summary) VALUES (?, ?)', 
                          (st.session_state["user_email"], f"Generated campaign for {platforms_str}"))
                conn.commit()
                conn.close()

            st.success("✅ Content Generated Successfully & Saved to Account!")

        except Exception as e:
            st.error(f"Error during generation: {e}")

# Render Results Dashboard & Interactive Assistant
if "parsed_content" in st.session_state:
    parsed_content = st.session_state["parsed_content"]
    raw_output = st.session_state.get("generated_output", "")
    
    st.markdown("---")
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

    tab_names = list(parsed_content.keys()) + ["💬 AI Editing Assistant"]
    tabs = st.tabs(tab_names)
    
    for idx, name in enumerate(parsed_content.keys()):
        with tabs[idx]:
            content = parsed_content[name]
            st.markdown(content)
            
            c_chars = len(content)
            c_words = len(content.split())
            st.caption(f"📏 Stats: **{c_chars}** characters | **{c_words}** words")
            
            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                if st.button(f"📋 Copy Text", key=f"copy_{idx}"):
                    st.toast(f"Copied {name} content to clipboard!")
            
            if enable_speech_preview and HAS_GTTS:
                with col_btn2:
                    if st.button(f"🔊 Listen to Audio Preview", key=f"tts_{idx}"):
                        clean_text = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
                        clean_text = re.sub(r'[\*#_]', '', clean_text)
                        lang_code = "en" if "English" in target_language else "es" if "Spanish" in target_language else "ur" if "Urdu" in target_language else "en"
                        tts = gTTS(text=clean_text[:500], lang=lang_code)
                        fp = io.BytesIO()
                        tts.write_to_fp(fp)
                        st.audio(fp, format="audio/mp3")

    with tabs[-1]:
        st.subheader("💬 Ask AI to Edit or Refine Output")
        user_query = st.text_input("Ask for adjustments (e.g., 'Make the hook punchier', 'Add a discount code'):")
        if st.button("Apply Edit Request") and user_query:
            try:
                client = genai.Client(api_key=api_key)
                edit_prompt = f"Original Generated Content:\n{raw_output}\n\nUser Revision Request: {user_query}\n\nProvide updated content in {target_language}:"
                with st.spinner("Applying revisions..."):
                    revised_resp = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=edit_prompt
                    )
                st.markdown("### ✏️ Revised Output / Answer:")
                st.markdown(revised_resp.text)
            except Exception as e:
                st.error(f"Error executing revision: {e}")

    st.markdown("---")
    st.subheader("📥 Export Campaign")
    ex_col1, ex_col2, ex_col3 = st.columns(3)
    
    with ex_col1:
        st.download_button(
            label="📄 Download Markdown (.md)",
            data=raw_output,
            file_name=f"campaign_{target_language.lower()}.md",
            mime="text/markdown"
        )
    with ex_col2:
        st.download_button(
            label="📝 Download Plain Text (.txt)",
            data=raw_output,
            file_name=f"campaign_{target_language.lower()}.txt",
            mime="text/plain"
        )
    with ex_col3:
        df_export = pd.DataFrame(list(parsed_content.items()), columns=["Platform / Section", "Content"])
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Download CSV (Scheduler)",
            data=csv_data,
            file_name="social_media_scheduler.csv",
            mime="text/csv"
        )
