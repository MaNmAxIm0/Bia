import logging
import subprocess
import shlex
from pathlib import Path
import config
from .image_processor import process_image

def apply_video_watermark(video_path: Path, output_path: Path) -> bool:
  try:
    font_color_hex = f"#{config.WATERMARK_COLOR_RGB[0]:02x}{config.WATERMARK_COLOR_RGB[1]:02x}{config.WATERMARK_COLOR_RGB[2]:02x}"
    ffmpeg_alpha = config.WATERMARK_OPACITY / 255.0
    pos_x = f"w-text_w-(w*{config.MARGIN_RATIO})"
    pos_y = f"h-text_h-(h*{config.MARGIN_RATIO})"
    shadow_offset = f"h*{config.VID_WATERMARK_FONT_RATIO}*0.05"
    shadow_x = f"{pos_x}+{shadow_offset}"
    shadow_y = f"{pos_y}+{shadow_offset}"
    drawtext_filter = (
      f"drawtext="
      f"fontfile='{config.WATERMARK_FONT_PATH}':"
      f"text='{config.WATERMARK_TEXT}':"
      f"fontsize=h*{config.VID_WATERMARK_FONT_RATIO}:"
      f"fontcolor=black@{ffmpeg_alpha*0.8}:"
      f"x={shadow_x}:y={shadow_y},"
      f"drawtext="
      f"fontfile='{config.WATERMARK_FONT_PATH}':"
      f"text='{config.WATERMARK_TEXT}':"
      f"fontsize=h*{config.VID_WATERMARK_FONT_RATIO}:"
      f"fontcolor={font_color_hex}@{ffmpeg_alpha}:"
      f"x={pos_x}:y={pos_y}"
    )
    command = [
      "ffmpeg", "-i", str(video_path),
      "-vf", drawtext_filter,
      "-codec:v", "libx264", "-preset", "medium", "-crf", "23",
      "-codec:a", "copy", "-y", str(output_path)
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    return True
  except subprocess.CalledProcessError as e:
    logging.error(f"FFmpeg falhou ao aplicar marca de água ao vídeo '{video_path.name}': {e.stderr}")
    return False

def generate_thumbnail(video_path: Path) -> bool:
  logging.info(f"A gerar thumbnail para '{video_path.name}'...")
  try:
    relative_video_path = video_path.relative_to(config.PROCESSED_ASSETS_DIR)
    final_thumb_path = config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR / relative_video_path.with_name(f"{video_path.stem}_thumb.jpg")
    final_thumb_path.parent.mkdir(parents=True, exist_ok=True)
    temp_frame_path = Path.cwd() / f"{video_path.stem}_temp_frame.jpg"
    extract_cmd = [
      'ffmpeg', '-ss', config.THUMBNAIL_TIMESTAMP, '-i', str(video_path),
      '-vframes', '1', '-q:v', '2', '-y', str(temp_frame_path)
    ]
    subprocess.run(extract_cmd, check=True, capture_output=True, text=True)
    if not temp_frame_path.exists():
      raise FileNotFoundError("FFmpeg não criou o frame temporário.")
    logging.info(f"A aplicar marca de água ao thumbnail '{temp_frame_path.name}'...")
    if not process_image(temp_frame_path, final_thumb_path):
      raise Exception("O processador de imagem falhou ao criar o thumbnail final.")
    logging.info(f"Thumbnail '{final_thumb_path.name}' gerado com sucesso em '{final_thumb_path.parent}'.")
    return True
  except subprocess.CalledProcessError as e:
    logging.error(f"FFmpeg falhou ao extrair thumbnail de '{video_path.name}': {e.stderr}")
    return False
  except Exception as e:
    logging.error(f"Falha ao gerar thumbnail para '{video_path.name}': {e}")
    return False
  finally:
    if 'temp_frame_path' in locals() and temp_frame_path.exists():
      temp_frame_path.unlink()