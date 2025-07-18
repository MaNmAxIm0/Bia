# utils/rclone_handler.py

import logging
import subprocess
import shlex
import config

def run_rclone_command(command: list, operation_name: str) -> bool:
    """Executa um comando rclone e trata os erros de forma genérica."""
    logging.info(f"Iniciando operação rclone: {operation_name}")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logging.info(f"Operação rclone '{operation_name}' concluída com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha na operação rclone '{operation_name}': {e.stderr}")
        return False

def download_assets():
    """Descarrega os ficheiros da origem para o diretório local."""
    command = ["rclone", "copy", config.DRIVE_REMOTE_PATH, str(config.LOCAL_ASSETS_DIR), "--progress"]
    if not run_rclone_command(command, "Download de ativos do Drive"):
        exit(1)

def upload_assets():
    """Faz o upload dos ficheiros processados para o R2."""
    command = [
        "rclone", "sync", str(config.PROCESSED_ASSETS_DIR), config.R2_REMOTE_PATH,
        "--exclude", "Thumbnails/**",
        "--exclude", "quarantine/**",
        "--exclude", "*.log",
        "-v"
    ]
    run_rclone_command(command, "Upload de ativos para o R2")

def generate_r2_manifest():
    """Gera o manifesto de ficheiros a partir do R2."""
    logging.info("Gerando manifesto de ficheiros do R2...")
    command = ["rclone", "lsf", "--format", "p", config.R2_REMOTE_PATH]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        with open(config.MANIFEST_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        logging.info(f"Manifesto '{config.MANIFEST_OUTPUT_FILE.name}' gerado com sucesso.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha ao gerar manifesto do R2: {e.stderr}")
