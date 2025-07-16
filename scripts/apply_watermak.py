# Ficheiro: scripts/apply_watermark.py

import sys
import os
import subprocess
import json # <--- LINHA ADICIONADA
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- Configuração ---
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat-SemiBold.ttf')
TEMP_DIR = "temp_files"
MAX_IMAGE_WIDTH = 1920
JPEG_QUALITY = 85

def get_media_dimensions(local_path, is_video):
    width, height = 0, 0
    try:
        if not is_video:
            with Image.open(local_path) as img:
                img_corrected = ImageOps.exif_transpose(img)
                width, height = img_corrected.size
        else:
            command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path]
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            dims = json.loads(result.stdout)["streams"][0]
            width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
    except Exception as e:
        print(f"  AVISO: Não foi possível obter dimensões para '{local_path}'. Erro: {e}", file=sys.stderr)
    return width, height

def main(input_path):
    filename = os.path.basename(input_path)
    is_video = filename.lower().endswith(('.mp4', '.mov'))
    
    print(f"  A aplicar marca de água em: {filename}")
    
    width, height = get_media_dimensions(input_path, is_video)
    if width == 0:
        sys.exit(1) # Sai com erro se não conseguir ler as dimensões

    if not is_video:
        output_path = os.path.join(TEMP_DIR, f"{os.path.splitext(filename)[0]}.jpg")
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
        except Exception as e:
            print(f"  ERRO DETALHADO ao aplicar marca de água na imagem: {e}", file=sys.stderr)
            sys.exit(1)
    else: # é vídeo
        output_path = os.path.join(TEMP_DIR, f"processed_{filename}")
        try:
            font_size = max(30, int(width * 0.055))
            margin = int(width * 0.025)
            escaped_text = WATERMARK_TEXT.replace("'", "\\'").replace(":", "\\:")
            vf_command = f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.8:x=w-text_w-{margin}:y=h-text_h-{margin}:shadowcolor=black@0.6:shadowx=2:shadowy=2"
            command = ["ffmpeg", "-i", input_path, "-vf", vf_command, "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "copy", "-y", output_path]
            subprocess.run(command, check=True)
        except Exception as e:
            print(f"  ERRO DETALHADO ao aplicar marca de água ao vídeo: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Erro: Nenhum ficheiro especificado.", file=sys.stderr)
        sys.exit(1)