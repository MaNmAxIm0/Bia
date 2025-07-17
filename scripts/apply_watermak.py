# Ficheiro: scripts/apply_watermark.py (VERSÃO CORRIGIDA)

import sys
import os
import subprocess
import json  # <--- CORREÇÃO: Módulo importado
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- Configuração ---
WATERMARK_TEXT = "© Beatriz Rodrigues"
MAX_IMAGE_WIDTH = 1920
JPEG_QUALITY = 85

def apply_image_watermark(input_path, output_path, font_path):
    """Aplica marca de água a um ficheiro de imagem."""
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
            font = ImageFont.truetype(font_path, font_size)
            
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            margin = int(img.width * 0.025)
            position = (img.width - text_width - margin, img.height - text_height - margin)
            
            draw.text((position[0] + 2, position[1] + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text(position, WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220))
            
            img.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
            return True
    except Exception as e:
        print(f"  ERRO DETALHADO ao aplicar marca de água na imagem '{os.path.basename(input_path)}': {e}", file=sys.stderr)
        return False

def apply_video_watermark(input_path, output_path, font_path):
    """Aplica marca de água a um ficheiro de vídeo."""
    try:
        # Obter dimensões do vídeo
        ffprobe_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", input_path]
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
        dims = json.loads(result.stdout)["streams"][0]
        width = int(dims.get("width", 0))

        if width == 0:
            print(f"  ERRO: Não foi possível obter dimensões do vídeo '{os.path.basename(input_path)}'.", file=sys.stderr)
            return False

        font_size = max(30, int(width * 0.055))
        margin = int(width * 0.025)
        escaped_text = WATERMARK_TEXT.replace("'", "'\\\\''")
        escaped_font_path = font_path.replace(":", "\\\\:")
        vf_command = f"drawtext=text='{escaped_text}':fontfile='{escaped_font_path}':fontsize={font_size}:fontcolor=white@0.8:x=w-text_w-{margin}:y=h-text_h-{margin}:shadowcolor=black@0.6:shadowx=2:shadowy=2"
        
        ffmpeg_cmd = ["ffmpeg", "-i", input_path, "-vf", vf_command, "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "copy", "-y", output_path]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        return True
    except Exception as e:
        print(f"  ERRO DETALHADO ao aplicar marca de água ao vídeo '{os.path.basename(input_path)}': {e}", file=sys.stderr)
        return False