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
    page_title="Shayari Video to Audio Pipeline",
    page_icon="🎙️",
    layout="centered"
)

st.title("🚀 Shayari Video-to-Audio AI Pipeline")
st.markdown("TikTok ya Facebook ka link dein, automation video download karegi, Urdu/Hindi text format karegi, aur ElevenLabs se audio generate karke aik hi click par ZIP download provide karegi!")

# --- Sidebar Configurations ---
st.sidebar.header("🔑 API Configurations")
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
        st.error(f"TikTok error: {e}")
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
    You are an expert Urdu/Hindi poet and text formatter. Analyze the transcribed text provided below. This text has been extracted from a shayari (poetry) video. Carefully consider the delivery style (andaz-e-bayan) and emotional tone, then apply appropriate punctuation. IMPORTANT: If any misra (line) is repeated in the video, retain the exact same repetition in the formatted text. Raw Transcribed Text:

    {raw_text}

    Provide two separate versions of the poetry:
    URDU_TEXT: The original poetry in authentic Urdu script (Persian-Arabic), formatted as proper poetry (line by line / misra format) with correct punctuation and styling.
    HINDI_TEXT: The same poetry in Devanagari (Hindi) script, with identical formatting, line structure, and repetitions.
    Respond strictly in the following format:
    ---URDU_START---
    [Formatted poetry in Urdu script]
    ---URDU_END---

    ---HINDI_START---
    [Formatted poetry in Hindi script]
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

# --- Streamlit UI Main Flow ---
url_input = st.text_input("🔗 TikTok ya Facebook video ka link yahan paste karein:")

if st.button("🚀 Process Pipeline"):
    if not url_input.strip():
        st.warning("Baraye meherbani pehle koi valid link enter karein!")
    elif not GROQ_API_KEY or not ELEVEN_LABS_API_KEY:
        st.error("Baraye meherbani sidebar mein apni API keys enter karein!")
    else:
        media_path = None
        with st.spinner("📥 Video download ki ja rahi hai..."):
            if "tiktok.com" in url_input or "vt.tiktok.com" in url_input:
                media_path = download_tiktok(url_input)
            elif "facebook.com" in url_input or "fb.watch" in url_input:
                media_path = download_facebook(url_input)
            else:
                st.error("Baraye meherbani koi valid TikTok ya Facebook link dein!")

        if media_path and os.path.exists(media_path):
            base_name = f"poetry_{int(time.time())}"
            
            with st.spinner("🤖 Groq Whisper AI transcribe kar raha hai aur LLM formatting kar raha hai..."):
                urdu_txt, hindi_txt, urdu_file_path, hindi_file_path = process_media_to_text(media_path, base_name, GROQ_API_KEY)

            audio_filename = os.path.join(OUTPUT_AUDIO_FOLDER, f"{base_name}.mp3")
            with st.spinner("🎙️ ElevenLabs se Hindi text par audio generate ho rahi hai..."):
                success = generate_tts_elevenlabs(hindi_txt, audio_filename, ELEVEN_LABS_API_KEY, VOICE_ID)

            # Cleanup video file
            if os.path.exists(media_path):
                os.remove(media_path)

            if success:
                st.success("✨ Sabhi files kamiyabi se generate ho gayi hain!")

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📜 Urdu Script")
                    st.text_area("Urdu Text", urdu_txt, height=200)
                with col2:
                    st.subheader("📜 Hindi Script")
                    st.text_area("Hindi Text", hindi_txt, height=200)

                st.markdown("---")
                st.subheader("🎧 Generated Audio & Single Download Package")
                st.audio(audio_filename)

                # Create an in-memory zip file containing Urdu text and MP3 audio
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.write(urdu_file_path, arcname=f"{base_name}_urdu.txt")
                    zip_file.write(audio_filename, arcname=f"{base_name}.mp3")
                zip_buffer.seek(0)

                st.download_button(
                    label="📥 Download Urdu Text & Audio (ZIP)",
                    data=zip_buffer,
                    file_name=f"{base_name}_package.zip",
                    mime="application/zip"
                )