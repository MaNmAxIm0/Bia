import os
import subprocess
import json
import logging
import shutil
from pathlib import Path
from tqdm import tqdm
from PIL import Image
from datetime import datetime
from zoneinfo import ZoneInfo
import config
from processors.image_processor import process_image
from processors.video_processor import process_video
from processors.pdf_processor import process_pdf
from utils.rclone_handler import sync_rclone

def setup_logging():
  log_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s")
  root_logger = logging.getLogger()
  if root_logger.hasHandlers(): root_logger.handlers.clear()
  lisbon_tz = ZoneInfo("Europe/Lisbon")
  logging.Formatter.converter = lambda *args: datetime.now(lisbon_tz).timetuple()
  handler = logging.StreamHandler()
  handler.setFormatter(log_formatter)
  root_logger.addHandler(handler)
  root_logger.setLevel(logging.INFO)

def get_media_orientation(file_path: Path) -> str:
  ext = file_path.suffix.lower()
  try:
    if ext in config.IMAGE_EXTENSIONS:
      with Image.open(file_path) as img:
        return "vertical" if img.height > img.width else "horizontal"
    elif ext in config.VIDEO_EXTENSIONS:
      cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(file_path)]
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      width, height = map(int, result.stdout.strip().split("x"))
      return "vertical" if height > width else "horizontal"
  except Exception:
    return "horizontal"
  return "horizontal"

def main():
  setup_logging()
  logging.info("--- INÍCIO DO WORKFLOW DE SINCRONIZAÇÃO ---")
  for path in [config.LOCAL_ASSETS_DIR, config.PROCESSED_ASSETS_DIR, config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR]:
    path.mkdir(exist_ok=True)
  if not sync_rclone(config.DRIVE_REMOTE_PATH, str(config.LOCAL_ASSETS_DIR), "Sincronizar Google Drive"):
    return
  if not sync_rclone(config.R2_REMOTE_PATH, str(config.PROCESSED_ASSETS_DIR), "Sincronizar R2 para local", "--use-server-modtime"):
    return
  drive_stems = {p.stem for p in config.LOCAL_ASSETS_DIR.rglob("*.*")}
  for proc_file in list(config.PROCESSED_ASSETS_DIR.rglob("*.*")):
    if config.THUMBNAIL_DIR.name in proc_file.parts:
      if proc_file.stem.replace("_thumb", "") not in drive_stems:
        proc_file.unlink()
    elif proc_file.stem not in drive_stems:
      proc_file.unlink()
  manifest_entries = []
  failed_files = []
  for input_path in tqdm(list(config.LOCAL_ASSETS_DIR.rglob("*.*")),
                          desc="Processando Ficheiros"):
    relative_path = input_path.relative_to(config.LOCAL_ASSETS_DIR)
    if input_path.suffix.lower() in config.PPTX_EXTENSIONS:
      output_path = (config.PROCESSED_ASSETS_DIR / relative_path).with_suffix(".pdf")
    else:
      output_path = config.PROCESSED_ASSETS_DIR / relative_path
    ext = input_path.suffix.lower()
    if output_path.exists() and input_path.stat().st_mtime <= output_path.stat().st_mtime:
      continue
    output_path.parent.mkdir(parents=True, exist_ok=True)
    parent_folder = relative_path.parts[0] if len(relative_path.parts) > 1 else ""
    should_apply_watermark = parent_folder not in ["Melhores", "Capas", "Apresentações", config.THUMBNAIL_DIR.name]
    processed_successfully = True
    if ext in [".gdoc", ".gsheet", ".gslides"]:
      shutil.copy2(input_path, output_path)
    elif ext in config.PPTX_EXTENSIONS:
      logging.info(f"Convertendo {input_path.name} para PDF...")
      convert_cmd = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_path.parent),
        str(input_path)
      ]
      if sync_rclone(None, None, f"Converter {input_path.name}", *convert_cmd):
        logging.info(f"PDF gerado: A comprimir {output_path.name}...")
        compress_pdf_path = output_path.with_name(f"{output_path.stem}_compressed.pdf")
        process_pdf(output_path, compress_pdf_path)
        shutil.move(compress_pdf_path, output_path)
      else:
        processed_successfully = False
        failed_files.append(str(relative_path))
    elif ext in config.PDF_EXTENSIONS:
      process_pdf(input_path, output_path)
    elif ext in config.IMAGE_EXTENSIONS:
      process_image(input_path, output_path, apply_watermark_flag=should_apply_watermark)
    elif ext in config.VIDEO_EXTENSIONS:
      if not process_video(input_path, output_path, apply_watermark_flag=should_apply_watermark):
        processed_successfully = False
        failed_files.append(str(relative_path))
    else:
      continue
    if processed_successfully:
      manifest_entries.append(f"{relative_path.as_posix()} - {datetime.now().isoformat()}")
  final_data = {}
  for source_path in list(config.LOCAL_ASSETS_DIR.rglob("*.*")):
    relative_path = source_path.relative_to(config.LOCAL_ASSETS_DIR)
    ext = source_path.suffix.lower()
    if ext in [".gdoc", ".gsheet", ".gslides"]:
      try:
        with open(source_path, "r", encoding="utf-8") as f: url = json.load(f)["url"]
        if "presentation" in url: url = url.replace("/edit", "/embed?start=false&loop=false&delayms=3000")
        final_data[source_path.stem] = {"titles": {"pt": source_path.stem, "en": source_path.stem, "es": source_path.stem}, "orientation": "horizontal", "url": url, "is_external": True}
      except Exception: continue
    else:
      output_path = config.PROCESSED_ASSETS_DIR / relative_path
      if output_path.exists():
        stem = output_path.stem
        titles = stem.split("_"); title_pt, title_en, title_es = (titles[0] if titles else stem, titles[1] if len(titles) > 1 else titles[0], titles[2] if len(titles) > 2 else titles[0])
        entry = {"titles": {"pt": title_pt, "en": title_en, "es": title_es}, "orientation": get_media_orientation(output_path), "url": f"{config.R2_PUBLIC_URL}/{relative_path.as_posix()}"}
        if ext in config.VIDEO_EXTENSIONS:
          entry["thumbnail_url"] = f"{config.R2_PUBLIC_URL}/{config.THUMBNAIL_DIR.name}/{stem}_thumb.jpg"
        final_data[output_path.name] = entry
  with open(config.JSON_OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=2, ensure_ascii=False)
  with open(config.R2_FILE_MANIFEST, "w", encoding="utf-8") as f:
    f.write(f"Última sincronização: {datetime.now(ZoneInfo('Europe/Lisbon')).strftime('%Y-%m-%d %H:%M:%S %Z')}

")
    if manifest_entries:
      f.write("Ficheiros processados nesta execução:
")
      f.write("
".join(manifest_entries))
    else:
      f.write("Nenhum ficheiro novo ou alterado foi processado.
")
  with open(config.FAILED_FILES_LOG, "w", encoding="utf-8") as f:
    if failed_files:
      f.write("Ficheiros que falharam o processamento:
")
      f.write("
".join(failed_files))
    else:
      f.write("Nenhum ficheiro falhou o processamento.
")
  sync_rclone(str(config.PROCESSED_ASSETS_DIR), config.R2_REMOTE_PATH, "Sincronizar para R2")
  logging.info("--- WORKFLOW CONCLUÍDO ---")

if __name__ == "__main__":
  main()
