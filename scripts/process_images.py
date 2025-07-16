# Ficheiro: scripts/process_images.py

import subprocess, json, os, time
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- Configuração ---
RCLONE_REMOTE = "R2:bia-portfolio-assets"
CATEGORIES = ["Fotografias", "Designs"]
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat-SemiBold.ttf')
TEMP_DIR = "temp_files"
MANIFEST_FILE = "r2_file_manifest.txt"
MAX_IMAGE_WIDTH = 1920
JPEG_QUALITY = 85

def run_command(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
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

def apply_watermark_and_compress(input_path, output_path):
    # (Função idêntica à anterior, melhorada)
    try:
        with Image.open(input_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode == 'RGBA':
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            
            if img.width > MAX_IMAGE_WIDTH:
                h = int((MAX_IMAGE_WIDTH / img.width) * img.height)
                img = img.resize((MAX_IMAGE_WIDTH, h), Image.Resampling.LANCZOS)
            
            draw = ImageDraw.Draw(img)
            font_size = max(24, int(img.height * 0.05))
            font = ImageFont.truetype(FONT_PATH, font_size)
            
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(img.width * 0.025)
            position = (img.width - text_width - margin, img.height - text_height - margin)
            
            draw.text((position[0] + 2, position[1] + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text(position, WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220))
            
            img.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        return True
    except Exception as e:
        print(f"  ERRO ao aplicar marca de água: {e}")
        return False

def main():
    os.makedirs(TEMP_DIR, exist_ok=True)
    last_run_time = get_last_manifest_time()
    all_files = get_rclone_lsl_json(RCLONE_REMOTE)

    files_to_process = [
        item for item in all_files
        if os.path.dirname(item["Path"]) in CATEGORIES and
           datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00")) > last_run_time
    ]
    
    print(f"Encontradas {len(files_to_process)} imagens novas ou modificadas.")

    for item in files_to_process:
        path = item["Path"]
        print(f"-> Processando: {path}")
        
        local_path = os.path.join(TEMP_DIR, os.path.basename(path))
        run_command(["rclone", "copyto", f"{RCLONE_REMOTE}/{path}", local_path])
        
        processed_filename = f"{os.path.splitext(os.path.basename(path))[0]}.jpg"
        local_processed_path = os.path.join(TEMP_DIR, processed_filename)

        if apply_watermark_and_compress(local_path, local_processed_path):
            final_path = os.path.join(os.path.dirname(path), processed_filename)
            print(f"  -> Upload para: {final_path}")
            run_command(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE}/{final_path}"])

            if path.lower() != final_path.lower():
                print(f"  -> Apagando original obsoleto: {path}")
                run_command(["rclone", "deletefile", f"{RCLONE_REMOTE}/{path}"])
        
        os.remove(local_path)
        if os.path.exists(local_processed_path):
            os.remove(local_processed_path)

if __name__ == "__main__":
    main()