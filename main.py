import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import subprocess
import time
import shutil
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from spleeter_utils import separate_music

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app_debug.log',
    filemode='w'
)
logger = logging.getLogger()

# =============================================================================
# PATH SANITIZATION AND SECURITY
# =============================================================================
def sanitize_path(path):
    """Remove invalid characters from paths"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        path = path.replace(char, '')
    return os.path.normpath(path)

# =============================================================================
# WINDOWS ADMIN CHECK
# =============================================================================
if sys.platform == 'win32':
    import ctypes
    # Check if we're running as admin
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        try:
            # Re-run as admin
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)
        except:
            logger.warning("Failed to run as admin")

# Workaround for TensorFlow file locking issue
if sys.platform == 'win32':
    try:
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.SetDllDirectoryW(None)
        logger.debug("Applied TensorFlow file locking workaround")
    except Exception as e:
        logger.error(f"TensorFlow workaround failed: {str(e)}")

# =============================================================================
# CRITICAL PATH SETUP FOR PYINSTALLER COMPATIBILITY
# =============================================================================
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = sys._MEIPASS  # PyInstaller temp folder
    
    # Add TensorFlow to DLL search path (Windows only)
    if sys.platform.startswith('win'):
        tensorflow_path = os.path.join(RESOURCE_DIR, 'tensorflow')
        if os.path.exists(tensorflow_path):
            os.environ['PATH'] = tensorflow_path + os.pathsep + os.environ['PATH']
            logger.debug(f"Added TensorFlow to PATH: {tensorflow_path}")
else:
    # Running as normal Python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR

# Set environment variables BEFORE importing anything else
os.environ['SPLEETER_MODEL_PATH'] = os.path.join(RESOURCE_DIR, 'pretrained_models')
os.environ['PATH'] = os.path.join(RESOURCE_DIR, 'ffmpeg') + os.pathsep + os.environ['PATH']
logger.debug(f"SPLEETER_MODEL_PATH set to: {os.environ['SPLEETER_MODEL_PATH']}")
logger.debug(f"FFmpeg added to PATH: {os.path.join(RESOURCE_DIR, 'ffmpeg')}")

# Verify FFmpeg
try:
    result = subprocess.check_output(
        ['ffmpeg', '-version'],
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    ffmpeg_version = result.decode().split('\n')[0]
    logger.info(f"FFmpeg found: {ffmpeg_version}")
except Exception as e:
    logger.critical(f"FFmpeg ERROR: {str(e)}")
    messagebox.showerror("FFmpeg Missing", "FFmpeg not found! Application cannot function.")
    sys.exit(1)

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================
INPUT_DIR = sanitize_path(os.path.join(BASE_DIR, "input"))
OUTPUT_DIR = sanitize_path(os.path.join(BASE_DIR, "output"))
TEMP_DIR = sanitize_path(os.path.join(INPUT_DIR, "temp_download"))

# Create directories if missing
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
logger.debug(f"Input directory: {INPUT_DIR}")
logger.debug(f"Output directory: {OUTPUT_DIR}")
logger.debug(f"Temp directory: {TEMP_DIR}")

selected_file = None

# =============================================================================
# YOUTUBE DOWNLOAD FUNCTIONS
# =============================================================================
def extract_video_id(url):
    """Extract YouTube video ID from various URL formats"""
    if "youtube.com" in url or "youtu.be" in url:
        if "v=" in url:
            return url.split("v=")[-1].split("&")[0]
        elif "youtu.be" in url:
            return url.split("/")[-1].split("?")[0]
    return None

def download_yt_mp3(url, status_callback):
    global selected_file
    video_id = extract_video_id(url)
    if not video_id:
        status_callback("❌ Invalid YouTube URL.")
        logger.warning(f"Invalid YouTube URL: {url}")
        return

    status_callback("🔁 Starting conversion process...")
    logger.info(f"Starting YouTube download: {url}")

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size=1280,720")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": TEMP_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    # Use y2mate service
    url_y2mate = "https://y2mate.as/en-qOwq/"

    for attempt in range(3):
        status_callback(f"⚙️ Attempt {attempt+1}/3...")
        logger.info(f"Download attempt {attempt+1}/3")
        try:
            # Initialize WebDriver
            driver = webdriver.Chrome(options=chrome_options)
            logger.debug("Chrome WebDriver initialized")
            driver.get(url_y2mate)

            # Enter video URL
            input_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="v"]'))
            )
            input_box.send_keys(url)
            time.sleep(1)
            logger.debug("URL entered")

            # Click Convert button
            convert_btn = driver.find_element(By.XPATH, '/html/body/form/div[2]/button[2]')
            convert_btn.click()
            logger.debug("Convert button clicked")

            # Wait for Download button
            try:
                download_btn = WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[2]/button[1]'))
                )
                logger.debug("Download button found")
            except:
                status_callback("❌ Download button not found. Retrying...")
                logger.warning("Download button not found")
                driver.quit()
                continue

            # Click Download
            download_btn.click()
            status_callback("📥 Download started...")
            logger.debug("Download button clicked")

            # Wait for download to complete
            downloaded_file = None
            timeout = 300  # 5 minutes
            poll_interval = 2
            elapsed = 0
            
            while elapsed < timeout:
                time.sleep(poll_interval)
                elapsed += poll_interval
                
                # Check for completed downloads
                files = [f for f in os.listdir(TEMP_DIR) 
                         if f.endswith(".mp3")]
                
                # Check for in-progress downloads
                temp_files = [f for f in os.listdir(TEMP_DIR) 
                             if f.endswith(".crdownload") or f.endswith(".part")]
                
                if files:
                    downloaded_file = files[0]
                    logger.debug(f"Download complete: {downloaded_file}")
                    break
                
                if not temp_files:
                    # No active downloads
                    time.sleep(2)
                    files = [f for f in os.listdir(TEMP_DIR) if f.endswith(".mp3")]
                    if files:
                        downloaded_file = files[0]
                        logger.debug(f"Download complete (no temp files): {downloaded_file}")
                        break

            if not downloaded_file:
                status_callback("❌ Download failed or timed out.")
                logger.error("Download failed or timed out")
                driver.quit()
                continue

            # Move to main input directory
            src_path = os.path.join(TEMP_DIR, downloaded_file)
            final_path = os.path.join(INPUT_DIR, downloaded_file)
            shutil.move(src_path, final_path)
            logger.info(f"File moved to: {final_path}")

            selected_file = final_path
            status_callback("✅ MP3 downloaded and ready.")
            driver.quit()
            return

        except Exception as e:
            import traceback
            error_msg = f"❌ Error: {str(e)}\n{traceback.format_exc()}"
            logger.error(f"Download error: {error_msg}")
            status_callback(error_msg[:200])  # Show first 200 chars
            if 'driver' in locals():
                try:
                    driver.quit()
                except:
                    pass
            continue

    status_callback("❌ All 3 attempts failed. Please try again later.")
    logger.error("All download attempts failed")

# =============================================================================
# GUI APPLICATION
# =============================================================================
def run_gui():
    root = tk.Tk()
    root.title("AI Music Splitter")
    root.geometry("440x520")
    root.resizable(False, False)
    
    # Set application icon
    try:
        icon_path = os.path.join(RESOURCE_DIR, 'app_icon.ico')
        root.iconbitmap(icon_path)
        logger.debug("Application icon set")
    except Exception as e:
        logger.warning(f"Could not set icon: {str(e)}")

    # GUI Elements
    header = tk.Label(root, text="AI Music Splitter", font=("Arial", 16, "bold"), fg="#2c3e50")
    header.pack(pady=10)

    # Section 1: Local File Selection
    local_frame = tk.LabelFrame(root, text=" 🎵 Local Audio File ", padx=10, pady=10)
    local_frame.pack(fill="x", padx=15, pady=5)
    
    file_label = tk.Label(local_frame, text="No file selected", fg="gray", wraplength=350)
    file_label.pack(pady=2)
    
    browse_btn = tk.Button(local_frame, text="Browse Local Audio", 
                          command=lambda: select_local_file(file_label, status_label),
                          bg="#3498db", fg="white", width=20)
    browse_btn.pack(pady=5)

    # Section 2: YouTube Download
    yt_frame = tk.LabelFrame(root, text=" ▶️ YouTube Download ", padx=10, pady=10)
    yt_frame.pack(fill="x", padx=15, pady=10)
    
    tk.Label(yt_frame, text="Enter YouTube URL:").pack(anchor="w")
    yt_entry = tk.Entry(yt_frame, width=45)
    yt_entry.pack(fill="x", pady=2)
    
    yt_btn = tk.Button(yt_frame, text="Download MP3", 
                      command=lambda: start_yt_download(yt_entry, status_label),
                      bg="#e74c3c", fg="white", width=20)
    yt_btn.pack(pady=5)

    # Stem Selection
    stem_frame = tk.LabelFrame(root, text=" 🎚️ Stem Selection ", padx=10, pady=10)
    stem_frame.pack(fill="x", padx=15, pady=10)
    
    stem_var = tk.StringVar(value="2")
    tk.Radiobutton(stem_frame, text="2 Stems (Vocals + Accompaniment)", 
                  variable=stem_var, value="2").pack(anchor="w", padx=5)
    tk.Radiobutton(stem_frame, text="4 Stems (Vocals + Drums + Bass + Other)", 
                  variable=stem_var, value="4").pack(anchor="w", padx=5)
    tk.Radiobutton(stem_frame, text="5 Stems (Vocals + Drums + Bass + Piano + Other)", 
                  variable=stem_var, value="5").pack(anchor="w", padx=5)

    # Separate Button
    separate_btn = tk.Button(root, text="Separate Audio", 
                           command=lambda: start_separation(stem_var, status_label), 
                           bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                           height=2, width=20)
    separate_btn.pack(pady=15)

    # Status Bar
    status_frame = tk.Frame(root, bd=1, relief=tk.SUNKEN)
    status_frame.pack(fill="x", padx=10, pady=5, side=tk.BOTTOM)
    status_label = tk.Label(status_frame, text="Ready", fg="#2c3e50", anchor=tk.W)
    status_label.pack(fill="x", padx=5, pady=2)

    # =========================================================================
    # GUI HELPER FUNCTIONS
    # =========================================================================
    def select_local_file(file_label, status_label):
        global selected_file
        file = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=[("Audio files", "*.mp3 *.wav *.flac *.ogg *.m4a")]
        )
        if file:
            try:
                # Copy to input directory
                filename = os.path.basename(file)
                dest = os.path.join(INPUT_DIR, filename)
                shutil.copy(file, dest)
                selected_file = dest
                file_label.config(text=filename)
                status_label.config(text="✅ Local file selected.")
                logger.info(f"Local file selected: {filename}")
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                status_label.config(text=error_msg)
                logger.error(f"File copy error: {str(e)}")

    def start_separation(stem_var, status_label):
        if not selected_file:
            messagebox.showerror("No file", "Please select or download an audio file.")
            return
        
        # Validate file exists
        if not os.path.exists(selected_file):
            error_msg = "❌ Selected file not found!"
            status_label.config(text=error_msg)
            logger.error(error_msg)
            return
            
        # Validate file size
        file_size = os.path.getsize(selected_file) / (1024 * 1024)  # in MB
        if file_size < 0.1:
            error_msg = "❌ File is too small (corrupted?)"
            status_label.config(text=error_msg)
            logger.warning(error_msg)
            return
            
        # Validate audio duration
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(selected_file)
            if len(audio) < 1000:  # Less than 1 second
                error_msg = "❌ Audio too short (download failed?)"
                status_label.config(text=error_msg)
                logger.warning(error_msg)
                return
        except Exception as e:
            logger.warning(f"Audio duration check skipped: {str(e)}")
            
        threading.Thread(target=threaded_separation, args=(stem_var, status_label)).start()

    def threaded_separation(stem_var, status_label):
        try:
            selected_stems = int(stem_var.get())
            status_text = "🎧 Starting audio separation..."
            status_label.config(text=status_text)
            logger.info(status_text)
            
            # Create unique output directory per separation
            timestamp = int(time.time())
            separation_output = sanitize_path(os.path.join(OUTPUT_DIR, f"output_{timestamp}"))
            os.makedirs(separation_output, exist_ok=True)
            logger.info(f"Created output directory: {separation_output}")
            
            # Debug info
            logger.debug(f"Separating: {selected_file}")
            logger.debug(f"Output dir: {separation_output}")
            logger.debug(f"Stems: {selected_stems}")
            
            # Run separation
            separate_music(selected_file, separation_output, stems=selected_stems)
            
            status_text = "✅ Separation completed successfully!"
            status_label.config(text=status_text)
            logger.info(status_text)
            messagebox.showinfo("Success", f"Output saved to:\n{separation_output}")
        except Exception as e:
            # Extract first line of error
            error_lines = str(e).split('\n')
            error_summary = error_lines[0] if error_lines else "Unknown error"
            
            status_text = f"❌ {error_summary}"
            status_label.config(text=status_text)
            logger.error(f"Separation failed: {str(e)}")
            messagebox.showerror("Separation Failed", error_summary)
            
            # Write full error to log
            with open("separation_errors.log", "a") as f:
                f.write(f"[{time.ctime()}] Error: {str(e)}\n\n")

    def start_yt_download(yt_entry, status_label):
        yt_url = yt_entry.get().strip()
        if not yt_url:
            messagebox.showerror("Missing URL", "Please enter a YouTube URL.")
            return
        threading.Thread(target=download_yt_mp3, args=(yt_url, lambda msg: status_label.config(text=msg))).start()

    root.mainloop()

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    logger.info("===== APPLICATION STARTED =====")
    logger.info(f"Resource directory: {RESOURCE_DIR}")
    logger.info(f"Base directory: {BASE_DIR}")
    
    # Add resource paths to system path
    sys.path.append(RESOURCE_DIR)
    
    # Start the application
    try:
        run_gui()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        messagebox.showerror("Fatal Error", f"Application crashed: {str(e)}")
    finally:
        logger.info("===== APPLICATION EXITED =====")