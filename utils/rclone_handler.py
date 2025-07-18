# utils/rclone_handler.py

import logging
import subprocess
import shlex
import config
import json
from pathlib import Path

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

def get_r2_manifest_as_dict() -> dict:
    """Obtém o manifesto do R2 e retorna-o como um dicionário."""
    logging.info("Obtendo manifesto atual do R2...")
    command = ["rclone", "lsjson", config.R2_REMOTE_PATH, "--exclude", "Thumbnails/**"]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        files = json.loads(result.stdout)
        return {item['Path']: item for item in files}
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.warning(f"Não foi possível obter o manifesto do R2 (pode estar vazio). Erro: {e}")
        return {}

def download_changed_assets(r2_manifest: dict):
    """Compara o Google Drive com o manifesto do R2 e descarrega apenas os ficheiros novos ou modificados."""
    logging.info("Comparando Drive com o manifesto R2 para encontrar alterações...")
    drive_command = ["rclone", "lsjson", config.DRIVE_REMOTE_PATH]
    try:
        result = subprocess.run(drive_command, check=True, capture_output=True, text=True, encoding='utf-8')
        drive_files = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Falha ao listar ficheiros do Google Drive: {e}")
        exit(1)

    files_to_download = []
    for drive_file in drive_files:
        path = drive_file['Path']
        r2_file = r2_manifest.get(path)
        if not r2_file or r2_file['Size'] != drive_file['Size']:
            files_to_download.append(path)

    if not files_to_download:
        logging.info("Nenhum ficheiro novo ou modificado encontrado. Nada para descarregar.")
        return

    logging.info(f"Encontrados {len(files_to_download)} ficheiros para descarregar.")
    
    files_from_list_path = "files_to_download.txt"
    with open(files_from_list_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(files_to_download))

    download_command = [
        "rclone", "copy", config.DRIVE_REMOTE_PATH, str(config.LOCAL_ASSETS_DIR),
        "--files-from", files_from_list_path, "--progress"
    ]
    if not run_rclone_command(download_command, "Download de ficheiros alterados"):
        exit(1)
    
    Path(files_from_list_path).unlink()

def upload_assets():
    """Faz o upload dos ficheiros processados para o R2."""
    command = [
        "rclone", "sync", str(config.PROCESSED_ASSETS_DIR), config.R2_REMOTE_PATH,
        "--exclude", "quarantine/**",
        "--exclude", "*.log",
        "-v"
    ]
    run_rclone_command(command, "Upload de ativos para o R2")

def generate_r2_manifest_file():
    """Gera o ficheiro de manifesto r2_file_manifest.txt a partir do R2."""
    logging.info("Gerando ficheiro de manifesto do R2...")
    # --- CORREÇÃO: Adicionada a flag -R para busca recursiva ---
    command = ["rclone", "lsf", "-R", "--format", "p", config.R2_REMOTE_PATH]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        with open(config.MANIFEST_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        logging.info(f"Manifesto '{config.MANIFEST_OUTPUT_FILE.name}' gerado com sucesso.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha ao gerar manifesto do R2: {e.stderr}")
