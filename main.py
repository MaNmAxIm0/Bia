import os
import subprocess
import json
import logging
import shutil
from pathlib import Path
from tqdm import tqdm
from PIL import Image
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import config
from processors.image_processor import process_image
from processors.video_processor import process_video
from utils.rclone_handler import sync_rclone, delete_rclone

def setup_logging():
  log_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s")
  root_logger = logging.getLogger()
  if root_logger.hasHandlers():
    root_logger.handlers.clear()
  lisbon_tz = ZoneInfo("Europe/Lisbon")
  logging.Formatter.converter = lambda *args: datetime.now(lisbon_tz).timetuple()
  console_handler = logging.StreamHandler()
  console_handler.setFormatter(log_formatter)
  root_logger.addHandler(console_handler)
  file_handler = logging.FileHandler("workflow.log", encoding="utf-8")
  file_handler.setFormatter(log_formatter)
  root_logger.addHandler(file_handler)
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

def compress_pdf(input_path: Path, output_path: Path, quality: str = 'ebook'):
    """Compresses a PDF file using Ghostscript."""
    logging.info(f"Comprimindo PDF: {input_path.name} com qualidade '{quality}'...")
    gs_command = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]
    try:
        subprocess.run(gs_command, check=True, capture_output=True, text=True, timeout=900)
        logging.info(f"PDF comprimido com sucesso: {output_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"FALHA ao comprimir {input_path.name}: {e.stderr.strip()}")
        shutil.copy2(input_path, output_path)
        return False
    except Exception as e:
        logging.error(f"Erro inesperado ao comprimir {input_path.name}: {e}")
        shutil.copy2(input_path, output_path)
        return False

def main():
  setup_logging()
  logging.info("--- INÍCIO DO WORKFLOW DE SINCRONIZAÇÃO ---")
  for path in [config.LOCAL_ASSETS_DIR, config.PROCESSED_ASSETS_DIR, config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR]:
    path.mkdir(exist_ok=True)
  logging.info("A obter metadados dos ficheiros existentes no R2...")
  r2_files_metadata = {}
  try:
    r2_lsjson_cmd = ["rclone", "lsjson", config.R2_REMOTE_PATH, "--files-only", "--recursive"]
    result = subprocess.run(r2_lsjson_cmd, capture_output=True, text=True, check=True)
    r2_json_output = json.loads(result.stdout)
    for item in r2_json_output:
      r2_files_metadata[item["Path"]] = datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00"))
    logging.info(f"Metadados de {len(r2_files_metadata)} ficheiros do R2 obtidos.")
  except Exception as e:
    logging.error(f"Erro ao obter metadados do R2: {e}")
  logging.info("A obter metadados dos ficheiros existentes no Google Drive...")
  drive_files_metadata = {}
  try:
    drive_lsjson_cmd = ["rclone", "lsjson", config.DRIVE_REMOTE_PATH, "--files-only", "--recursive"]
    result = subprocess.run(drive_lsjson_cmd, capture_output=True, text=True, check=True)
    drive_json_output = json.loads(result.stdout)
    for item in drive_json_output:
        drive_files_metadata[item["Path"]] = datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00"))
    logging.info(f"Metadados de {len(drive_files_metadata)} ficheiros do Google Drive obtidos.")
  except Exception as e:
    logging.error(f"Erro ao obter metadados do Google Drive: {e}")
    return
  files_to_download = []
  for path, drive_mod_time in drive_files_metadata.items():
      if path not in r2_files_metadata or drive_mod_time > r2_files_metadata.get(path, datetime.fromtimestamp(0, tz=timezone.utc)):
          files_to_download.append(path)
  with open("download_list.txt", "w") as f:
      for item in files_to_download:
          f.write(f"{item}\n")
  if files_to_download:
      if not sync_rclone(config.DRIVE_REMOTE_PATH, str(config.LOCAL_ASSETS_DIR), "Sincronizar ficheiros necessários do Google Drive", "--files-from", "download_list.txt"):
        return
  else:
      logging.info("Nenhum ficheiro para descarregar.")
  google_drive_files = list(drive_files_metadata.keys())
  with open("r2_keep_list.txt", "w") as f:
    for item in google_drive_files:
      f.write(f"- {item}\n")
    f.write(f"- /{config.THUMBNAIL_DIR.name}/**\n")
    f.write("+ *\n")")} ⏎
  delete_rclone("r2_keep_list.txt", config.R2_REMOTE_PATH, "Remover ficheiros do R2 que não estão no Google Drive")
  if os.path.exists(config.JSON_OUTPUT_FILE):
      with open(config.JSON_OUTPUT_FILE, "r", encoding="utf-8") as f:
          final_data = json.load(f)
  else:
      final_data = {}
  manifest_entries = []
  failed_files = []
  for input_path in tqdm(list(config.LOCAL_ASSETS_DIR.rglob("*.*")), desc="Processando Ficheiros"):
    relative_path = input_path.relative_to(config.LOCAL_ASSETS_DIR)
    if input_path.suffix.lower() in config.PPTX_EXTENSIONS:
      output_path = (config.PROCESSED_ASSETS_DIR / relative_path).with_suffix(".pdf")
    else:
      output_path = config.PROCESSED_ASSETS_DIR / relative_path
    ext = input_path.suffix.lower()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    parent_folder = relative_path.parts[0] if len(relative_path.parts) > 1 else ""
    no_watermark_folders = ["Melhores", "Capas", "Apresentações", config.THUMBNAIL_DIR.name, ""]
    should_apply_watermark = parent_folder not in no_watermark_folders
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
      try:
        subprocess.run(convert_cmd, check=True, capture_output=True, text=True, encoding='utf-8', timeout=900)
        compress_pdf(output_path, output_path)
      except subprocess.CalledProcessError as e:
        logging.error(f"FALHA ao converter {input_path.name} para PDF: {e.stderr.strip()}")
        processed_successfully = False
        failed_files.append(str(relative_path))
      except Exception as e:
        logging.error(f"Erro inesperado ao converter {input_path.name} para PDF: {e}")
        processed_successfully = False
        failed_files.append(str(relative_path))
    elif ext in config.PDF_EXTENSIONS:
      compress_pdf(input_path, output_path)
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
      stem = output_path.stem
      titles = stem.split("_")
      title_pt, title_en, title_es = (titles[0] if titles else stem, titles[1] if len(titles) > 1 else titles[0], titles[2] if len(titles) > 2 else titles[0])
      entry = {"titles": {"pt": title_pt, "en": title_en, "es": title_es}, "orientation": get_media_orientation(output_path), "url": f"{config.R2_PUBLIC_URL}/{relative_path.as_posix()}"}
      if ext in config.VIDEO_EXTENSIONS:
        entry["thumbnail_url"] = f"{config.R2_PUBLIC_URL}/{config.THUMBNAIL_DIR.name}/{stem}_thumb.jpg"
      final_data[output_path.name] = entry
  google_drive_filenames = {Path(p).name for p in drive_files_metadata.keys()}
  final_data = {
      filename: data
      for filename, data in final_data.items()
      if filename in google_drive_filenames
  }
  with open(config.JSON_OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=2, ensure_ascii=False)
  with open(config.R2_FILE_MANIFEST, "w", encoding="utf-8") as f:
    f.write(f"Última sincronização: {datetime.now(ZoneInfo('Europe/Lisbon')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    if manifest_entries:
      f.write("Ficheiros processados nesta execução:")
      f.write("".join(manifest_entries))
    else:
      f.write("Nenhum ficheiro novo ou alterado foi processado.")
  with open(config.FAILED_FILES_LOG, "w", encoding="utf-8") as f:
    if failed_files:
      f.write("Ficheiros que falharam o processamento:")
      f.write("".join(failed_files))
    else:
      f.write("Nenhum ficheiro falhou o processamento.")
  sync_rclone(str(config.PROCESSED_ASSETS_DIR), config.R2_REMOTE_PATH, "Sincronizar para R2")
  logging.info("--- WORKFLOW CONCLUÍDO ---")

if __name__ == "__main__":
  main()