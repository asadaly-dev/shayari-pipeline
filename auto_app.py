import os
import time
import zipfile
import io
import requests
import yt_dlp
from groq import Groq
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Shayari Video to Audio AI",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS & Animations ---
st.markdown("""
<style>
    /* Hide Streamlit default UI elements & Sidebar */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}

    /* Keyframe Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
        100% { transform: translateY(0px); }
    }
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 12px rgba(255, 75, 114, 0.35); }
        50% { box-shadow: 0 0 24px rgba(138, 43, 226, 0.65); }
        100% { box-shadow: 0 0 12px rgba(255, 75, 114, 0.35); }
    }

    /* Hero Banner Styling */
    .hero-box {
        text-align: center;
        padding: 2.2rem 1.5rem;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(255, 75, 114, 0.1) 0%, rgba(121, 40, 202, 0.1) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        margin-bottom: 2rem;
        animation: fadeIn 0.7s ease-out;
    }
    .hero-icon {
        font-size: 3.2rem;
        display: inline-block;
        animation: float 3s ease-in-out infinite;
        margin-bottom: 0.4rem;
    }
    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B72, #A855F7, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.85;
        max-width: 580px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* Input Field Styling */
    div[data-baseweb="input"] {
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #FF4B72 !important;
        box-shadow: 0 0 12px rgba(255, 75, 114, 0.3) !important;
    }

    /* Primary & Download Buttons */
    div.stButton > button, div.stDownloadButton > button {
        width: 100%;
        background: linear-gradient(90deg, #FF4B72 0%, #8A2BE2 100%);
        color: white !important;
        border: none;
        padding: 0.75rem 1.5rem;
        font-size: 1.05rem;
        font-weight: 600;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        animation: pulseGlow 3s infinite;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 8px 25px rgba(255, 75, 114, 0.55);
    }

    /* Poetry Output Cards */
    .poetry-card {
        background: rgba(128, 128, 128, 0.07);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        min-height: 220px;
        white-space: pre-wrap;
        animation: fadeIn 0.6s ease-out;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .poetry-card:hover {
        transform: translateY(-3px);
        border-color: #FF4B72;
    }
    .urdu-font {
        direction: rtl;
        text-align: right;
        font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', 'Segoe UI', Tahoma, sans-serif;
        font-size: 1.35rem;
        line-height: 2.3;
    }
    .hindi-font {
        direction: ltr;
        text-align: left;
        font-family: 'Poppins', 'Segoe UI', sans-serif;
        font-size: 1.15rem;
        line-height: 1.9;
    }
</style>
""", unsafe_allow_html=True)

# --- Hero Header ---
st.markdown("""
<div class="hero-box">
    <div class="hero-icon">🎙️</div>
    <div class="hero-title">Shayari Video-to-Audio AI</div>
    <div class="hero-subtitle">
        TikTok ya Facebook ka link paste karein — AI khud video download karegi, Urdu aur Hindi scripts format karegi, aur ElevenLabs voiceover ke sath instant ZIP package tayyar karegi!
    </div>
</div>
""", unsafe_allow_html=True)

# --- Background API Configurations (Hidden from UI) ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
ELEVEN_LABS_API_KEY = st.secrets.get("ELEVEN_LABS_API_KEY", "")
VOICE_ID = st.secrets.get("VOICE_ID", "nQ41Q0vYCIfV8DMjRAUs")

DOWNLOAD_FOLDER = "input_videos"
OUTPUT_URDU_FOLDER = "output_urdu_text"
OUTPUT_HINDI_FOLDER = "output_hindi_text"
OUTPUT_AUDIO_FOLDER = "output_audio"

for folder in [DOWNLOAD_FOLDER, OUTPUT_URDU_FOLDER, OUTPUT_HINDI_FOLDER, OUTPUT_AUDIO_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# --- Downloader Functions ---
def download_tiktok(video_url):
    api_url = f"https://www.tikwm.com/api/?url={video_url}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        if data.get('code') == 0:
            video_dl_url = data['data']['play']
            video_id = data['data']['id']
            file_path = os.path.join(DOWNLOAD_FOLDER, f"tiktok_{video_id}.mp4")
            video_response = requests.get(video_dl_url)
            with open(file_path, 'wb') as f:
                f.write(video_response.content)
            return file_path
    except Exception as e:
        st.error(f"TikTok download error: {e}")
    return None

def download_facebook(video_url):
    file_path = os.path.join(DOWNLOAD_FOLDER, f"fb_{abs(hash(video_url))}.mp4")
    ydl_opts = {
        'outtmpl': file_path,
        'format': 'best',
        'quiet': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return file_path
    except Exception as e:
        st.error(f"Facebook download error: {e}")
    return None

# --- Text Extraction & Formatting ---
def process_media_to_text(media_path, base_name, groq_key):
    client_groq = Groq(api_key=groq_key)
    with open(media_path, "rb") as file:
        transcription = client_groq.audio.transcriptions.create(
            file=(os.path.basename(media_path), file.read()),
            model="whisper-large-v3",
            response_format="text"
        )
    raw_text = transcription

    prompt = f"""
    You are an expert Urdu/Hindi poet and text formatter. Analyze the transcribed text provided below extracted from a shayari video. 
    Carefully filter out any background noise, music cues, or non-poetry words. Focus ONLY on the spoken shayari.
    Consider the delivery style (andaz-e-bayan) and emotional tone, and apply appropriate punctuation. 
    CRITICAL INSTRUCTION: If any misra (line) or phrase is repeated in the video, you MUST retain the exact same repetition in the formatted text. Do not skip or remove repetitions, as they are crucial for the poetry's emotional impact.

    Raw Transcribed Text:
    {raw_text}

    Provide two separate versions of the poetry:
    URDU_TEXT: The original poetry in authentic Urdu script (Persian-Arabic), formatted as proper poetry (line by line / misra format) with correct punctuation and styling, keeping all repetitions intact.
    HINDI_TEXT: The same poetry in Devanagari (Hindi) script, with identical formatting, line structure, and exact repetitions.
    
    Respond strictly in the following format:
    ---URDU_START---
    [Formatted poetry in Urdu script with repetitions]
    ---URDU_END---

    ---HINDI_START---
    [Formatted poetry in Hindi script with repetitions]
    ---HINDI_END---
    """

    response = client_groq.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    result_content = response.choices[0].message.content

    urdu_text, hindi_text = raw_text, raw_text
    if "---URDU_START---" in result_content and "---URDU_END---" in result_content:
        urdu_text = result_content.split("---URDU_START---")[1].split("---URDU_END---")[0].strip()
    if "---HINDI_START---" in result_content and "---HINDI_END---" in result_content:
        hindi_text = result_content.split("---HINDI_START---")[1].split("---HINDI_END---")[0].strip()

    # Save files locally
    urdu_file_path = os.path.join(OUTPUT_URDU_FOLDER, f"{base_name}_urdu.txt")
    with open(urdu_file_path, 'w', encoding='utf-8') as f:
        f.write(urdu_text)

    hindi_file_path = os.path.join(OUTPUT_HINDI_FOLDER, f"{base_name}_hindi.txt")
    with open(hindi_file_path, 'w', encoding='utf-8') as f:
        f.write(hindi_text)

    return urdu_text, hindi_text, urdu_file_path, hindi_file_path

# --- ElevenLabs TTS Generation ---
def generate_tts_elevenlabs(text, output_filename, api_key, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    payload = {
        "text": text,
        "model_id": "eleven_v4_turbo",
        "voice_settings": {
            "stability": 0.40,
            "similarity_boost": 0.70
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        return True
    else:
        st.error(f"ElevenLabs API Error: {response.status_code} - {response.text}")
        return False

# --- Main Input Flow ---
url_input = st.text_input(
    "🔗 Video Link",
    placeholder="https://www.tiktok.com/... ya https://www.facebook.com/...",
    label_visibility="collapsed"
)

if st.button("✨ Generate Poetry & Audio Package"):
    if not url_input.strip():
        st.warning("⚠️ Baraye meherbani pehle koi valid TikTok ya Facebook link enter karein!")
    elif not GROQ_API_KEY or not ELEVEN_LABS_API_KEY:
        st.error("⚠️ System configuration mein API keys missing hain. (`st.secrets` check karein)")
    else:
        with st.status("🚀 AI Pipeline Chal Rahi Hai...", expanded=True) as status:
            st.write("📥 **Step 1/3:** Video download ki ja rahi hai...")
            media_path = None
            if "tiktok.com" in url_input or "vt.tiktok.com" in url_input:
                media_path = download_tiktok(url_input)
            elif "facebook.com" in url_input or "fb.watch" in url_input:
                media_path = download_facebook(url_input)
            else:
                status.update(label="❌ Invalid Link!", state="error", expanded=False)
                st.error("Baraye meherbani sirf TikTok ya Facebook ka valid link dein!")
                st.stop()

            if not media_path or not os.path.exists(media_path):
                status.update(label="❌ Video Download Failed!", state="error", expanded=False)
                st.stop()

            base_name = f"poetry_{int(time.time())}"

            st.write("🧠 **Step 2/3:** Groq Whisper AI audio transcribe kar raha hai aur Shayari format ho rahi hai...")
            urdu_txt, hindi_txt, urdu_file_path, hindi_file_path = process_media_to_text(
                media_path, base_name, GROQ_API_KEY
            )

            st.write("🎙️ **Step 3/3:** ElevenLabs se soulful voiceover generate ho raha hai...")
            audio_filename = os.path.join(OUTPUT_AUDIO_FOLDER, f"{base_name}.mp3")
            success = generate_tts_elevenlabs(hindi_txt, audio_filename, ELEVEN_LABS_API_KEY, VOICE_ID)

            # Cleanup downloaded video
            if os.path.exists(media_path):
                os.remove(media_path)

            if success:
                status.update(label="✅ Shayari aur Audio Kamiyabi se Tayyar Hain!", state="complete", expanded=False)
                st.balloons()

                # Create in-memory ZIP package
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.write(urdu_file_path, arcname=f"{base_name}_urdu.txt")
                    zip_file.write(audio_filename, arcname=f"{base_name}.mp3")
                zip_buffer.seek(0)

                # Store results in session_state so they persist across button clicks
                st.session_state["pipeline_result"] = {
                    "base_name": base_name,
                    "urdu_txt": urdu_txt,
                    "hindi_txt": hindi_txt,
                    "audio_filename": audio_filename,
                    "zip_bytes": zip_buffer.getvalue()
                }
            else:
                status.update(label="❌ Audio Generation Failed!", state="error", expanded=False)

# --- Display Results ---
if "pipeline_result" in st.session_state:
    res = st.session_state["pipeline_result"]

    st.markdown("<br>", unsafe_allow_html=True)
    tab_side, tab_urdu, tab_hindi = st.tabs(["✨ Side-by-Side View", "📜 Urdu Script (Copy)", "📜 Hindi Script (Copy)"])

    with tab_side:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 🌙 Urdu Script")
            st.markdown(f'<div class="poetry-card urdu-font">{res["urdu_txt"]}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown("##### 🪔 Hindi Script")
            st.markdown(f'<div class="poetry-card hindi-font">{res["hindi_txt"]}</div>', unsafe_allow_html=True)

    with tab_urdu:
        st.text_area("Urdu Poetry", res["urdu_txt"], height=220, label_visibility="collapsed")

    with tab_hindi:
        st.text_area("Hindi Poetry", res["hindi_txt"], height=220, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🎧 Generated Voiceover Preview")
    if os.path.exists(res["audio_filename"]):
        st.audio(res["audio_filename"])

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📥 Download Complete Package (Urdu Text + MP3 ZIP)",
        data=res["zip_bytes"],
        file_name=f"{res['base_name']}_package.zip",
        mime="application/zip"
    )