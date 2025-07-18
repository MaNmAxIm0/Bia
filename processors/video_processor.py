# processors/video_processor.py

import logging
import subprocess
import shlex
from pathlib import Path
import config
# A importação do process_image é crucial para a reutilização de código
from .image_processor import process_image

def apply_video_watermark(video_path: Path, output_path: Path) -> bool:
    """Aplica uma marca de água de texto a um vídeo usando FFmpeg."""
    try:
        font_color_hex = f"#{config.WATERMARK_COLOR_RGB[0]:02x}{config.WATERMARK_COLOR_RGB[1]:02x}{config.WATERMARK_COLOR_RGB[2]:02x}"
        ffmpeg_alpha = config.WATERMARK_OPACITY / 255.0
        
        pos_x = f"w-text_w-(w*{config.MARGIN_RATIO})"
        pos_y = f"h-text_h-(h*{config.MARGIN_RATIO})"
        
        command = [
            "ffmpeg", "-i", str(video_path),
            "-vf", (
                f"drawtext="
                f"fontfile='{config.WATERMARK_FONT_PATH}':"
                f"text='{config.WATERMARK_TEXT}':"
                f"fontsize=h*{config.VID_WATERMARK_FONT_RATIO}:"
                f"fontcolor={font_color_hex}@{ffmpeg_alpha}:"
                f"x={pos_x}:y={pos_y}"
            ),
            "-codec:v", "libx264", "-preset", "medium", "-crf", "23",
            "-codec:a", "copy", "-y", str(output_path)
        ]
        
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg falhou ao aplicar marca de água ao vídeo '{video_path.name}': {e.stderr}")
        return False

def generate_thumbnail(video_path: Path) -> bool:
    """
    Gera um thumbnail com marca de água para um vídeo.
    O thumbnail será guardado na mesma pasta que o vídeo processado.
    """
    # --- CORREÇÃO: Lógica de caminhos robusta ---
    # O thumbnail deve ser guardado no mesmo diretório que o vídeo de saída.
    output_dir = video_path.parent
    temp_frame_path = output_dir / f"{video_path.stem}_temp_frame.jpg"
    final_thumb_path = output_dir / f"{video_path.stem}_thumb.jpg"
    
    logging.info(f"A gerar thumbnail para '{video_path.name}'...")

    try:
        # 1. Extrair um frame de alta qualidade com FFmpeg
        extract_cmd = [
            'ffmpeg', '-ss', config.THUMBNAIL_TIMESTAMP, '-i', str(video_path),
            '-vframes', '1', '-q:v', '2', '-y', str(temp_frame_path)
        ]
        subprocess.run(extract_cmd, check=True, capture_output=True, text=True)

        if not temp_frame_path.exists():
            raise FileNotFoundError("FFmpeg não criou o frame temporário.")

        # 2. Processar o frame extraído usando o mesmo pipeline das imagens
        logging.info(f"A aplicar marca de água ao thumbnail '{temp_frame_path.name}'...")
        if not process_image(temp_frame_path, final_thumb_path):
            # Propaga o erro se o processamento da imagem falhar
            raise Exception("O processador de imagem falhou ao criar o thumbnail final.")
            
        logging.info(f"Thumbnail '{final_thumb_path.name}' gerado com sucesso.")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg falhou ao extrair thumbnail de '{video_path.name}': {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Falha ao gerar thumbnail para '{video_path.name}': {e}")
        return False
    finally:
        # Garante que o ficheiro temporário é sempre limpo
        if temp_frame_path.exists():
            temp_frame_path.unlink()
