import logging
import subprocess
from pathlib import Path
import config
from processors.image_processor import process_image

def run_command(command: list, operation_name: str) -> bool:
  logging.info(f"Iniciando: {operation_name}...")
  try:
    subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', timeout=900)
    logging.info(f"Sucesso: {operation_name} concluída.")
    return True
  except Exception as e:
    stderr = getattr(e, 'stderr', str(e))
    logging.error(f"FALHA em \'{operation_name}\': {stderr.strip()}")
    return False

def process_video(input_path: Path, output_path: Path, apply_watermark_flag: bool) -> bool:
  output_path.parent.mkdir(parents=True, exist_ok=True)
  filter_complex = "scale=min(1920\\,iw):-2"
  if apply_watermark_flag:
    font_path = str(config.WATERMARK_FONT_PATH).replace('\\', '/')
    watermark_text = config.WATERMARK_TEXT.replace("'", "'")
    watermark_filter = (
      f",drawtext=fontfile='{font_path}':text='{watermark_text}':"
      f"fontsize=min(w\,h)*{config.VID_WATERMARK_FONT_RATIO}:fontcolor=black@0.5:"
      f"x=(w-text_w-(min(w\,h)*{config.MARGIN_RATIO}))+2:y=(h-text_h-(min(w\,h)*{config.MARGIN_RATIO}))+2,"
      f"drawtext=fontfile='{font_path}':text='{watermark_text}':"
      f"fontsize=min(w\,h)*{config.VID_WATERMARK_FONT_RATIO}:fontcolor=white@0.8:"
      f"x=w-text_w-(min(w\,h)*{config.MARGIN_RATIO}):y=h-text_h-(min(w\,h)*{config.MARGIN_RATIO})"
    )
    filter_complex += watermark_filter
  video_cmd = [
    "ffmpeg", "-i", str(input_path),
    "-vf", filter_complex,
    "-c:v", "libx264", "-preset", "medium", "-crf", "32",
    "-c:a", "aac", "-b:a", "128k",
    "-y", str(output_path)
  ]
  if not run_command(video_cmd, f"Processar vídeo {input_path.name}"):
    return False
  try:
    thumb_path = config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR / f"{output_path.stem}_thumb.jpg"
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(input_path)]
    result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
    duration = float(result.stdout.strip())
    ts = max(0.1, duration * 0.15)
    if ts >= duration:
      ts = duration / 2
    thumb_cmd = [
      "ffmpeg", "-ss", str(ts), "-i", str(input_path),
      "-vframes", "1",
      "-q:v", "2",
      "-y",
      str(thumb_path)
    ]
    if not run_command(thumb_cmd, f"Gerar thumbnail para {output_path.name}"):
      logging.warning(f"Não foi possível gerar thumbnail para {output_path.name}, mas o vídeo foi processado.")
  except Exception as e:
    logging.error(f"FALHA CRÍTICA ao gerar thumbnail para {input_path.name}: {e}")
    return False
  return True