# Ficheiro: scripts/process_videos.py

import subprocess, json, os, time
from datetime import datetime, timezone

# --- Configuração ---
RCLONE_REMOTE = "R2:bia-portfolio-assets"
CATEGORY = "Vídeos"
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat-SemiBold.ttf')
TEMP_DIR = "temp_files"
MANIFEST_FILE = "r2_file_manifest.txt"

def run_command(cmd, check=True):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=check, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        print(f"ERRO: {' '.join(cmd)}\n{e.stderr}")
        return None

def get_rclone_lsl_json(path):
    result = run_command(["rclone", "lsl", "--json", path, "--recursive"])
    return json.loads(result.stdout) if result and result.stdout else []

def get_last_manifest_time():
    try:
        with open(MANIFEST_FILE, 'r') as f:
            for line in f:
                if line.startswith("Gerado em:"):
                    date_str = " ".join(line.split()[2:5] + [line.split()[6]])
                    return datetime.strptime(date_str, "%b %d %H:%M:%S %Y").replace(tzinfo=timezone.utc)
    except:
        return datetime.fromtimestamp(0, tz=timezone.utc)

def apply_watermark_to_video(input_path, output_path):
    try:
        probe_result = run_command(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", input_path])
        dims = json.loads(probe_result.stdout)["streams"][0]
        width, height = int(dims.get("width", 0)), int(dims.get("height", 0))

        font_size = max(30, int(width * 0.055))
        margin = int(width * 0.025)
        escaped_text = WATERMARK_TEXT.replace("'", "\\'").replace(":", "\\:")
        vf_command = f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.8:x=w-text_w-{margin}:y=h-text_h-{margin}:shadowcolor=black@0.6:shadowx=2:shadowy=2"
        command = ["ffmpeg", "-i", input_path, "-vf", vf_command, "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "copy", "-y", output_path]
        run_command(command)
        return True
    except Exception as e:
        print(f"  ERRO ao aplicar marca de água ao vídeo: {e}")
        return False

def main():
    os.makedirs(TEMP_DIR, exist_ok=True)
    last_run_time = get_last_manifest_time()
    all_videos = [item for item in get_rclone_lsl_json(f"{RCLONE_REMOTE}/{CATEGORY}") if os.path.dirname(item["Path"]) == CATEGORY]

    videos_to_process = [
        item for item in all_videos
        if datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00")) > last_run_time
    ]
    
    print(f"Encontrados {len(videos_to_process)} vídeos novos ou modificados.")

    for item in videos_to_process:
        path = item["Path"]
        print(f"-> Processando: {path}")
        
        local_path = os.path.join(TEMP_DIR, os.path.basename(path))
        local_processed_path = os.path.join(TEMP_DIR, f"proc_{os.path.basename(path)}")

        run_command(["rclone", "copyto", f"{RCLONE_REMOTE}/{path}", local_path])
        
        if apply_watermark_to_video(local_path, local_processed_path):
            print(f"  -> Upload para: {path}")
            run_command(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE}/{path}"])
        
        os.remove(local_path)
        if os.path.exists(local_processed_path):
            os.remove(local_processed_path)

if __name__ == "__main__":
    main()