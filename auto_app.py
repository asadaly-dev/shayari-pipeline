import os
import time
import random
import zipfile
import io
import requests
import yt_dlp
import pandas as pd
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
        padding: 2rem 1.5rem;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(255, 75, 114, 0.1) 0%, rgba(121, 40, 202, 0.1) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        margin-bottom: 1.5rem;
        animation: fadeIn 0.7s ease-out;
    }
    .hero-icon {
        font-size: 3rem;
        display: inline-block;
        animation: float 3s ease-in-out infinite;
        margin-bottom: 0.3rem;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B72, #A855F7, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    .hero-subtitle {
        font-size: 0.98rem;
        opacity: 0.85;
        max-width: 580px;
        margin: 0 auto;
        line-height: 1.5;
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
        padding: 1.3rem;
        min-height: 180px;
        white-space: pre-wrap;
        animation: fadeIn 0.5s ease-out;
    }
    .urdu-font {
        direction: rtl;
        text-align: right;
        font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', 'Segoe UI', Tahoma, sans-serif;
        font-size: 1.3rem;
        line-height: 2.2;
    }
    .hindi-font {
        direction: ltr;
        text-align: left;
        font-family: 'Poppins', 'Segoe UI', sans-serif;
        font-size: 1.1rem;
        line-height: 1.8;
    }
</style>
""", unsafe_allow_html=True)

# --- Hero Header ---
st.markdown("""
<div class="hero-box">
    <div class="hero-icon">🎙️</div>
    <div class="hero-title">Shayari Video-to-Audio AI</div>
    <div class="hero-subtitle">
        Single link process karein ya Excel file upload karke bulk queue chalayein — Urdu/Hindi scripts aur ElevenLabs voiceover ek hi Master ZIP mein hasil karein!
    </div>
</div>
""", unsafe_allow_html=True)

# --- Streamlit Secrets Configuration ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
ELEVEN_LABS_API_KEY = st.secrets.get("ELEVEN_LABS_API_KEY", "")
VOICE_ID = st.secrets.get("VOICE_ID", "nQ41Q0vYCIfV8DMjRAUs")

DOWNLOAD_FOLDER = "input_videos"
OUTPUT_URDU_FOLDER = "output_urdu_text"
OUTPUT_HINDI_FOLDER = "output_hindi_text"
OUTPUT_AUDIO_FOLDER = "output_audio"

for folder in [DOWNLOAD_FOLDER, OUTPUT_URDU_FOLDER, OUTPUT_HINDI_FOLDER, OUTPUT_AUDIO_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ==========================================
# 📥 UPGRADED DOWNLOADER FUNCTIONS (Anti-Bot & Fallback)
# ==========================================
def download_tiktok(video_url, prefix="single"):
    clean_url = video_url.split("?")[0].strip()
    
    # ---------------------------------------------------------
    # METHOD 1: yt-dlp using Browser Cookies (Bypasses IP Block)
    # ---------------------------------------------------------
    file_path = os.path.join(DOWNLOAD_FOLDER, f"{prefix}_tiktok_{abs(hash(clean_url))}.mp4")
    
    for browser in ["chrome", "edge", "firefox"]:
        ydl_opts = {
            "outtmpl": file_path,
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "cookiesfrombrowser": (browser,)
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([clean_url])
            if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
                return file_path, None
        except Exception:
            continue

    # ---------------------------------------------------------
    # METHOD 2: TikWM API Fallback (with mobile headers)
    # ---------------------------------------------------------
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Accept": "application/json"
        }
        res = requests.post(
            "https://www.tikwm.com/api/",
            data={"url": clean_url, "hd": 1},
            headers=headers,
            timeout=25
        )
        if res.status_code == 200 and res.text.strip().startswith("{"):
            data = res.json()
            if data.get("code") == 0 and data.get("data"):
                d = data["data"]
                dl_url = d.get("play") or d.get("wmplay") or d.get("music")
                if dl_url:
                    if dl_url.startswith("/"):
                        dl_url = "https://www.tikwm.com" + dl_url
                    vid_path = os.path.join(DOWNLOAD_FOLDER, f"{prefix}_tiktok_tikwm_{d.get('id', int(time.time()))}.mp4")
                    vid_res = requests.get(dl_url, headers=headers, timeout=60)
                    if vid_res.status_code == 200 and len(vid_res.content) > 1000:
                        with open(vid_path, "wb") as f:
                            f.write(vid_res.content)
                        return vid_path, None
    except Exception as e:
        return None, f"All methods failed. TikWM/yt-dlp error: {str(e)[:60]}"

    return None, "TikTok download failed (IP blocked or invalid link)"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.tikwm.com/'
    }
    tikwm_error = ""

    # Attempt 1: TikWM POST API
    try:
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={'url': video_url, 'hd': 1}, headers=headers, timeout=30)
        data = response.json()

        if data.get('code') == 0 and data.get('data'):
            video_dl_url = data['data'].get('play') or data['data'].get('wmplay')
            if video_dl_url:
                if video_dl_url.startswith("/"):
                    video_dl_url = "https://www.tikwm.com" + video_dl_url

                video_id = data['data'].get('id', int(time.time()))
                file_path = os.path.join(DOWNLOAD_FOLDER, f"{prefix}_tiktok_{video_id}.mp4")

                video_response = requests.get(video_dl_url, headers=headers, timeout=60)
                if video_response.status_code == 200 and len(video_response.content) > 1000:
                    with open(file_path, 'wb') as f:
                        f.write(video_response.content)
                    return file_path, None
                else:
                    tikwm_error = f"TikWM CDN HTTP {video_response.status_code}"
            else:
                tikwm_error = "TikWM: Video stream missing"
        else:
            tikwm_error = f"TikWM msg: {data.get('msg', 'Rate limit or IP block')}"
    except Exception as e:
        tikwm_error = f"TikWM Error: {str(e)[:50]}"

    # Attempt 2: yt-dlp Fallback with custom headers
    file_path = os.path.join(DOWNLOAD_FOLDER, f"{prefix}_tiktok_{abs(hash(video_url))}.mp4")
    ydl_opts = {
        'outtmpl': file_path,
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {'User-Agent': headers['User-Agent']}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
            return file_path, None
    except Exception as ydl_e:
        return None, f"{tikwm_error} | yt-dlp: {str(ydl_e)[:60]}"

    return None, tikwm_error or "TikTok IP block / Download failure"

def download_facebook(video_url, prefix="single"):
    file_path = os.path.join(DOWNLOAD_FOLDER, f"{prefix}_fb_{abs(hash(video_url))}.mp4")
    ydl_opts = {
        'outtmpl': file_path,
        'format': 'best',
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
            return file_path, None
        return None, "FB file empty or not created"
    except Exception as e:
        return None, f"FB Error: {str(e)[:80]}"

def download_video_router(url, prefix="item"):
    if "tiktok.com" in url or "vt.tiktok.com" in url:
        return download_tiktok(url, prefix)
    elif "facebook.com" in url or "fb.watch" in url:
        return download_facebook(url, prefix)
    return None, "Unsupported URL domain (Only TikTok & Facebook allowed)"

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
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        return True, "Success"
    else:
        return False, f"API Error {response.status_code}: {response.text[:60]}"

# --- Helper to Build Master ZIP from Batch Results ---
def build_batch_master_zip(results_list):
    zip_buffer = io.BytesIO()
    report_rows = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in results_list:
            report_rows.append({
                "S.No": item["sno"],
                "Platform": item["platform"],
                "Link": item["link"],
                "Status": item["status"],
                "Urdu Text": item.get("urdu_txt", ""),
                "Hindi Text": item.get("hindi_txt", ""),
                "Audio File": item.get("arc_audio_name", "")
            })
            if item["status"] == "✅ Completed":
                if os.path.exists(item["urdu_file_path"]):
                    zip_file.write(item["urdu_file_path"], arcname=item["arc_urdu_name"])
                if os.path.exists(item["hindi_file_path"]):
                    zip_file.write(item["hindi_file_path"], arcname=item["arc_hindi_name"])
                if os.path.exists(item["audio_filename"]):
                    zip_file.write(item["audio_filename"], arcname=item["arc_audio_name"])

        report_df = pd.DataFrame(report_rows)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            report_df.to_excel(writer, index=False, sheet_name="Batch_Report")
        excel_buffer.seek(0)
        zip_file.writestr("Batch_Summary_Report.xlsx", excel_buffer.read())

    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# ==========================================
# MAIN UI: DUAL MODE TABS
# ==========================================
mode_single, mode_bulk = st.tabs(["🔗 Single Video Link", "📊 Bulk Excel Queue (Auto-Pilot)"])

# ------------------------------------------
# TAB 1: SINGLE LINK PROCESSING
# ------------------------------------------
with mode_single:
    url_input = st.text_input(
        "🔗 Video Link",
        placeholder="https://www.tiktok.com/... ya https://www.facebook.com/...",
        label_visibility="collapsed"
    )

    if st.button("✨ Generate Single Poetry & Audio"):
        if not url_input.strip():
            st.warning("⚠️ Baraye meherbani pehle koi valid TikTok ya Facebook link enter karein!")
        elif not GROQ_API_KEY or not ELEVEN_LABS_API_KEY:
            st.error("⚠️ Streamlit secrets mein API keys configured nahi hain!")
        else:
            with st.status("🚀 AI Pipeline Chal Rahi Hai...", expanded=True) as status:
                st.write("📥 **Step 1/3:** Video download ki ja rahi hai...")
                media_path, dl_error = download_video_router(url_input, prefix="single")

                if not media_path or not os.path.exists(media_path):
                    status.update(label="❌ Video Download Failed!", state="error", expanded=False)
                    st.error(f"Video download nahi ho saki! Reason: `{dl_error}`")
                    st.stop()

                base_name = f"poetry_{int(time.time())}"

                st.write("🧠 **Step 2/3:** Groq Whisper AI audio transcribe aur Shayari format kar raha hai...")
                urdu_txt, hindi_txt, urdu_file_path, hindi_file_path = process_media_to_text(
                    media_path, base_name, GROQ_API_KEY
                )

                st.write("🎙️ **Step 3/3:** ElevenLabs se soulful voiceover generate ho raha hai...")
                audio_filename = os.path.join(OUTPUT_AUDIO_FOLDER, f"{base_name}.mp3")
                success, err_msg = generate_tts_elevenlabs(hindi_txt, audio_filename, ELEVEN_LABS_API_KEY, VOICE_ID)

                if os.path.exists(media_path):
                    os.remove(media_path)

                if success:
                    status.update(label="✅ Shayari aur Audio Kamiyabi se Tayyar Hain!", state="complete", expanded=False)
                    st.balloons()

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        zip_file.write(urdu_file_path, arcname=f"{base_name}_urdu.txt")
                        zip_file.write(audio_filename, arcname=f"{base_name}.mp3")
                    zip_buffer.seek(0)

                    st.session_state["single_result"] = {
                        "base_name": base_name,
                        "urdu_txt": urdu_txt,
                        "hindi_txt": hindi_txt,
                        "audio_filename": audio_filename,
                        "zip_bytes": zip_buffer.getvalue()
                    }
                else:
                    status.update(label=f"❌ Audio Generation Failed: {err_msg}", state="error", expanded=False)

    if "single_result" in st.session_state:
        res = st.session_state["single_result"]
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 🌙 Urdu Script")
            st.markdown(f'<div class="poetry-card urdu-font">{res["urdu_txt"]}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown("##### 🪔 Hindi Script")
            st.markdown(f'<div class="poetry-card hindi-font">{res["hindi_txt"]}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if os.path.exists(res["audio_filename"]):
            st.audio(res["audio_filename"])

        st.download_button(
            label="📥 Download Package (Urdu Text + MP3 ZIP)",
            data=res["zip_bytes"],
            file_name=f"{res['base_name']}_package.zip",
            mime="application/zip",
            key="dl_single"
        )

# ------------------------------------------
# TAB 2: BULK EXCEL QUEUE SYSTEM
# ------------------------------------------
with mode_bulk:
    st.markdown("##### 📂 Upload `cleaned_shayari_links.xlsx`")
    uploaded_excel = st.file_uploader(
        "Apni Excel file yahan drop karein",
        type=["xlsx"],
        label_visibility="collapsed"
    )

    if uploaded_excel:
        try:
            df_links = pd.read_excel(uploaded_excel)
        except Exception as e:
            st.error(f"Excel file read karne mein masla aaya: {e}")
            st.stop()

        link_col = None
        for candidate in ["Cleaned Link", "Link", "URL", "Original Link"]:
            if candidate in df_links.columns:
                link_col = candidate
                break
        if not link_col:
            link_col = df_links.columns[-1]

        if "S.No" not in df_links.columns:
            df_links.insert(0, "S.No", range(1, len(df_links) + 1))

        total_rows = len(df_links)
        st.info(f"📊 Excel file mein total **{total_rows} links** mile hain. (Link Column: `{link_col}`)")

        with st.expander("👀 Excel Links Preview Dekhein"):
            st.dataframe(df_links.head(20), use_container_width=True)

        st.markdown("##### 🎯 Select Batch Range (Safe Limit: 5–10 Links at a time on Cloud)")
        c1, c2 = st.columns(2)
        min_sno = int(df_links["S.No"].min())
        max_sno = int(df_links["S.No"].max())
        default_end = min(min_sno + 4, max_sno)

        with c1:
            start_sno = st.number_input("Start S.No", min_value=min_sno, max_value=max_sno, value=min_sno, step=1)
        with c2:
            end_sno = st.number_input("End S.No", min_value=min_sno, max_value=max_sno, value=default_end, step=1)

        if start_sno > end_sno:
            st.warning("⚠️ 'Start S.No' hamesha 'End S.No' se chota ya barabar hona chahiye!")
        else:
            batch_df = df_links[(df_links["S.No"] >= start_sno) & (df_links["S.No"] <= end_sno)]
            batch_count = len(batch_df)

            if st.button(f"🚀 Start Bulk Queue ({batch_count} Videos: S.No {start_sno} to {end_sno})"):
                if not GROQ_API_KEY or not ELEVEN_LABS_API_KEY:
                    st.error("⚠️ Streamlit secrets mein API keys configured nahi hain!")
                    st.stop()

                st.session_state["batch_results"] = []
                progress_bar = st.progress(0, text="⏳ Queue start ho rahi hai...")
                status_box = st.empty()
                live_counter = st.empty()

                completed_count = 0
                failed_count = 0

                for idx, (_, row) in enumerate(batch_df.iterrows(), start=1):
                    sno = int(row["S.No"])
                    url = str(row[link_col]).strip()
                    platform = str(row.get("Platform", "Video"))
                    padded_sno = f"{sno:03d}"

                    progress_pct = int(((idx - 1) / batch_count) * 100)
                    progress_bar.progress(progress_pct, text=f"🔄 Processing S.No #{sno} ({idx}/{batch_count})...")
                    status_box.info(f"📥 **S.No #{sno}:** Video download ho rahi hai (`{url}`)")

                    media_path, dl_error = download_video_router(url, prefix=f"batch_{padded_sno}")

                    if not media_path or not os.path.exists(media_path):
                        failed_count += 1
                        st.warning(f"⚠️ S.No #{sno} Failed — Reason: `{dl_error}`")
                        st.session_state["batch_results"].append({
                            "sno": sno,
                            "platform": platform,
                            "link": url,
                            "status": f"❌ Failed ({dl_error})"
                        })
                        st.session_state["batch_master_zip"] = build_batch_master_zip(st.session_state["batch_results"])
                        st.session_state["batch_range_label"] = f"{start_sno}_to_{end_sno}"
                        live_counter.markdown(f"**Live Stats:** ✅ Completed: `{completed_count}` | ❌ Failed: `{failed_count}`")
                        
                        # Anti-block random delay on failure too
                        if idx < batch_count:
                            time.sleep(random.uniform(4, 7))
                        continue

                    try:
                        status_box.info(f"🧠 **S.No #{sno}:** Whisper AI transcribe aur Shayari format kar raha hai...")
                        base_name = f"{padded_sno}_shayari"
                        urdu_txt, hindi_txt, urdu_fp, hindi_fp = process_media_to_text(
                            media_path, base_name, GROQ_API_KEY
                        )

                        status_box.info(f"🎙️ **S.No #{sno}:** ElevenLabs voiceover generate ho raha hai...")
                        audio_fp = os.path.join(OUTPUT_AUDIO_FOLDER, f"{base_name}.mp3")
                        tts_ok, tts_msg = generate_tts_elevenlabs(hindi_txt, audio_fp, ELEVEN_LABS_API_KEY, VOICE_ID)

                        if os.path.exists(media_path):
                            os.remove(media_path)

                        if tts_ok:
                            completed_count += 1
                            st.session_state["batch_results"].append({
                                "sno": sno,
                                "platform": platform,
                                "link": url,
                                "status": "✅ Completed",
                                "urdu_txt": urdu_txt,
                                "hindi_txt": hindi_txt,
                                "urdu_file_path": urdu_fp,
                                "hindi_file_path": hindi_fp,
                                "audio_filename": audio_fp,
                                "arc_urdu_name": f"{padded_sno}_urdu.txt",
                                "arc_hindi_name": f"{padded_sno}_hindi.txt",
                                "arc_audio_name": f"{padded_sno}_audio.mp3"
                            })
                        else:
                            failed_count += 1
                            st.warning(f"⚠️ S.No #{sno} Audio Failed — Reason: `{tts_msg}`")
                            st.session_state["batch_results"].append({
                                "sno": sno,
                                "platform": platform,
                                "link": url,
                                "status": f"❌ Failed ({tts_msg})"
                            })

                    except Exception as e:
                        if os.path.exists(media_path):
                            os.remove(media_path)
                        failed_count += 1
                        err_short = str(e)[:60]
                        st.warning(f"⚠️ S.No #{sno} Processing Error — `{err_short}`")
                        st.session_state["batch_results"].append({
                            "sno": sno,
                            "platform": platform,
                            "link": url,
                            "status": f"❌ Failed ({err_short})"
                        })

                    st.session_state["batch_master_zip"] = build_batch_master_zip(st.session_state["batch_results"])
                    st.session_state["batch_range_label"] = f"{start_sno}_to_{end_sno}"
                    live_counter.markdown(f"**Live Stats:** ✅ Completed: `{completed_count}` | ❌ Failed: `{failed_count}`")

                    # Smart Anti-Bot Delay (Randomized 5 to 9 seconds gap between requests for Cloud)
                    if idx < batch_count:
                        sleep_time = random.uniform(5.0, 9.0)
                        time.sleep(sleep_time)

                progress_bar.progress(100, text="✅ Bulk Queue Completed!")
                status_box.success(f"🎉 Batch Complete! {completed_count} kamiyab hue, {failed_count} fail hue.")
                if completed_count > 0:
                    st.balloons()

    if "batch_results" in st.session_state and len(st.session_state["batch_results"]) > 0:
        st.markdown("---")
        st.markdown("### 📦 Bulk Queue Output & Master Package")

        if "batch_master_zip" in st.session_state:
            range_lbl = st.session_state.get("batch_range_label", "batch")
            st.download_button(
                label="📥 Download MASTER ZIP (All Numbered Audios + Urdu Texts + Excel Report)",
                data=st.session_state["batch_master_zip"],
                file_name=f"Shayari_Batch_{range_lbl}.zip",
                mime="application/zip",
                key="dl_master_zip"
            )

        st.markdown("#### 📋 Individual Item Results")
        for item in st.session_state["batch_results"]:
            header_text = f"S.No #{item['sno']} ({item['platform']}) — {item['status']}"
            with st.expander(header_text):
                st.caption(f"🔗 Link: {item['link']}")
                if item["status"] == "✅ Completed":
                    c_u, c_h = st.columns(2)
                    with c_u:
                        st.markdown("**🌙 Urdu Script**")
                        st.markdown(f'<div class="poetry-card urdu-font">{item["urdu_txt"]}</div>', unsafe_allow_html=True)
                    with c_h:
                        st.markdown("**🪔 Hindi Script**")
                        st.markdown(f'<div class="poetry-card hindi-font">{item["hindi_txt"]}</div>', unsafe_allow_html=True)

                    if os.path.exists(item["audio_filename"]):
                        st.audio(item["audio_filename"])