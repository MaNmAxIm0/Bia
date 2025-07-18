# run_processing.py

import os
import subprocess
import logging
from tqdm import tqdm
import shlex
from pathlib import Path
import shutil
import json
import sys

import config
# A importação do processador de imagem é mantida, assumindo que será corrigido.
from processors.image_processor import apply_watermark_to_image
from processors.video_processor import apply_watermark_to_video

# Configura o logging para ser claro e informativo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Ficheiro para registar os ficheiros que falharam
FAILED_FILES_LOG = "failed_files.log"

def setup_directories():
    """Cria os diretórios locais necessários."""
    Path(config.LOCAL_DOWNLOAD_DIR).mkdir(exist_ok=True)
    Path(config.LOCAL_PROCESSED_DIR).mkdir(exist_ok=True)
    # Limpa o log de falhas de execuções anteriores
    if os.path.exists(FAILED_FILES_LOG):
        os.remove(FAILED_FILES_LOG)

def download_assets():
    """Descarrega os ficheiros do Google Drive para o diretório local."""
    logging.info(f"A iniciar o download de ficheiros de '{config.SOURCE_RCLONE_PATH}'...")
    try:
        command = ["rclone", "copy", config.SOURCE_RCLONE_PATH, config.LOCAL_DOWNLOAD_DIR, "--progress"]
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logging.info("Download concluído com sucesso.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha no download dos ficheiros com rclone: {e.stderr}")
        exit(1)

def process_single_file(file_path: Path, manifest: dict):
    """Processa um único ficheiro, retornando o seu status."""
    relative_path = file_path.relative_to(config.LOCAL_DOWNLOAD_DIR)
    output_path = Path(config.LOCAL_PROCESSED_DIR) / relative_path
    
    # Compara com o manifesto para ver se precisa de ser processado
    local_size = file_path.stat().st_size
    remote_info = manifest.get(str(relative_path))
    if remote_info and local_size == remote_info.get('Size'):
        return "SKIPPED", None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    extension = file_path.suffix.lower()

    try:
        if extension in config.IMAGE_EXTENSIONS:
            if not apply_watermark_to_image(str(file_path), str(output_path), config):
                raise Exception("Processador de imagem retornou falha")
        elif extension in config.VIDEO_EXTENSIONS:
            if not apply_watermark_to_video(str(file_path), str(output_path), config):
                raise Exception("Processador de vídeo retornou falha")
        else:
            shutil.copy2(file_path, output_path)
        return "SUCCESS", None
    except Exception as e:
        # Retorna o erro para ser tratado pelo loop principal
        return "FAILURE", e

def process_all_files():
    """Itera sobre os ficheiros, processa-os e gere as falhas."""
    logging.info("A iniciar o processamento de ficheiros...")
    
    # Carrega o manifesto (assumindo que um script o gera)
    manifest = {} # Simplificado por agora
    source_dir = Path(config.LOCAL_DOWNLOAD_DIR)
    all_files = [p for p in source_dir.rglob('*') if p.is_file() and not p.name.startswith('.')]

    if not all_files:
        logging.warning("Nenhum ficheiro encontrado para processar.")
        return

    results = {"SUCCESS": 0, "SKIPPED": 0, "FAILURE": 0}
    failed_files_list = []

    with tqdm(total=len(all_files), desc="A processar ficheiros", unit="file") as pbar:
        for file_path in all_files:
            status, error = process_single_file(file_path, manifest)
            results[status] += 1
            
            if status == "FAILURE":
                relative_path = file_path.relative_to(config.LOCAL_DOWNLOAD_DIR)
                logging.error(f"Falha ao processar '{relative_path}': {error}")
                failed_files_list.append(str(relative_path))
            
            pbar.update(1)

    logging.info(f"Processamento concluído. Sucesso: {results['SUCCESS']}, Ignorados: {results['SKIPPED']}, Falhas: {results['FAILURE']}")

    if failed_files_list:
        logging.warning(f"{len(failed_files_list)} ficheiros falharam e serão marcados para quarentena.")
        with open(FAILED_FILES_LOG, 'w') as f:
            f.write("\n".join(failed_files_list))
        # O exit(1) foi removido para permitir que o workflow continue e execute o passo de quarentena
        # O passo de quarentena no .yml usará a condição if: failure() para ser acionado.

if __name__ == "__main__":
    setup_directories()
    download_assets()
    process_all_files()
