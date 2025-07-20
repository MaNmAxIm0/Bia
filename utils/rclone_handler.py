import logging
import subprocess
from pathlib import Path
import config

def run_rclone_command(command: list, operation_name: str) -> bool:
  logging.info(f"Iniciando operação rclone: {operation_name}")
  try:
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
    logging.info(f"Operação rclone '{operation_name}' concluída com sucesso.")
    logging.debug(f"Output do Rclone: {result.stdout}")
    return True
  except subprocess.CalledProcessError as e:
    logging.error(f"Falha na operação rclone '{operation_name}': {e.stderr}")
    return False

def download_all_assets():
  logging.info(f"Sincronizando ficheiros de '{config.DRIVE_REMOTE_PATH}' para '{config.LOCAL_ASSETS_DIR}'...")
  command = ["rclone", "sync", config.DRIVE_REMOTE_PATH, str(config.LOCAL_ASSETS_DIR), "--progress"]
  if not run_rclone_command(command, "Sincronização de ativos do Drive para local"):
    logging.critical("A sincronização inicial do Drive falhou. A abortar para evitar perda de dados.")
    exit(1)

def upload_assets():
  command = [
    "rclone", "sync", str(config.PROCESSED_ASSETS_DIR), config.R2_REMOTE_PATH,
    "--exclude", "quarantine/**",
    "--exclude", "*.log",
    "--track-renames",
    "-v"
  ]
  run_rclone_command(command, "Sincronização de ativos para o R2")

def generate_r2_manifest_file():
  logging.info("Gerando ficheiro de manifesto do R2...")
  command = ["rclone", "lsf", "-R", config.R2_REMOTE_PATH]
  try:
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
    with open(config.MANIFEST_OUTPUT_FILE, 'w', encoding='utf-8') as f:
      f.write(result.stdout)
    logging.info(f"Manifesto '{config.MANIFEST_OUTPUT_FILE.name}' gerado com sucesso.")
  except subprocess.CalledProcessError as e:
    logging.error(f"Falha ao gerar manifesto do R2: {e.stderr}")