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
# As funções de processamento são importadas, mas não foram fornecidas.
# Assumindo que existem em 'processors/'.
from processors.image_processor import apply_watermark_to_image
from processors.video_processor import apply_watermark_to_video

# Configura o logging para ser claro e informativo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def setup_directories():
    """Cria os diretórios locais necessários."""
    logging.info(f"A garantir que os diretórios '{config.LOCAL_DOWNLOAD_DIR}' e '{config.LOCAL_PROCESSED_DIR}' existem.")
    Path(config.LOCAL_DOWNLOAD_DIR).mkdir(exist_ok=True)
    Path(config.LOCAL_PROCESSED_DIR).mkdir(exist_ok=True)

def download_assets():
    """Descarrega os ficheiros do Google Drive para o diretório local."""
    logging.info(f"A iniciar o download de ficheiros de '{config.SOURCE_RCLONE_PATH}'...")
    try:
        # --- CORREÇÃO --- O comando rclone foi preenchido corretamente.
        command = [
            "rclone", "copy", config.SOURCE_RCLONE_PATH, config.LOCAL_DOWNLOAD_DIR,
            "--progress"
        ]
        logging.info(f"A executar Rclone: {' '.join(shlex.quote(c) for c in command)}")
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logging.info("Download concluído com sucesso.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha no download dos ficheiros com rclone. O script será terminado.")
        logging.error(f"Rclone stderr: {e.stderr}")
        exit(1)

def load_manifest():
    """Carrega o manifesto de ficheiros existentes no R2."""
    manifest_path = Path("r2_manifest.json")
    if not manifest_path.exists():
        logging.warning("Ficheiro de manifesto não encontrado. A processar todos os ficheiros.")
        return {}
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
            # Cria um dicionário onde a chave é o caminho do ficheiro e o valor são os seus metadados
            return {item['Path']: item for item in manifest_data}
    except (json.JSONDecodeError, TypeError):
        logging.warning(f"O ficheiro de manifesto '{manifest_path.name}' não é um JSON válido. Será ignorado.")
        return {}

def process_single_file(file_path: Path, r2_manifest: dict):
    """Processa um único ficheiro se for novo ou modificado."""
    relative_path = file_path.relative_to(config.LOCAL_DOWNLOAD_DIR)
    output_path = Path(config.LOCAL_PROCESSED_DIR) / relative_path
    
    local_size = file_path.stat().st_size
    remote_file_info = r2_manifest.get(str(relative_path))

    # Compara o tamanho do ficheiro local com o do manifesto para ver se mudou
    if remote_file_info and local_size == remote_file_info.get('Size'):
        return (str(relative_path), "SKIPPED", None)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    extension = file_path.suffix.lower()

    try:
        if hasattr(config, 'EXCLUDE_PATTERNS') and any(file_path.name.endswith(ext) for ext in config.EXCLUDE_PATTERNS):
            return (str(relative_path), "IGNORED_PATTERN", None)

        if extension in config.IMAGE_EXTENSIONS:
            if apply_watermark_to_image(str(file_path), str(output_path), config):
                return (str(relative_path), "SUCCESS", None)
            else:
                raise Exception("Falha no processador de imagem")
        elif extension in config.VIDEO_EXTENSIONS:
            if apply_watermark_to_video(str(file_path), str(output_path), config):
                return (str(relative_path), "SUCCESS", None)
            else:
                raise Exception("Falha no processador de vídeo")
        else:
            shutil.copy2(file_path, output_path) # Usar copy2 para preservar metadados
            return (str(relative_path), "COPIED_UNSUPPORTED", None)
    except Exception as e:
        return (str(relative_path), "FAILURE", str(e))

def process_all_files():
    """Itera sobre os ficheiros, aplicando a marca de água apropriada."""
    logging.info("A iniciar o processamento de ficheiros com base no manifesto...")
    
    r2_manifest = load_manifest()
    
    # --- CORREÇÃO --- A lista de ficheiros foi inicializada corretamente.
    source_dir = Path(config.LOCAL_DOWNLOAD_DIR)
    all_files = [p for p in source_dir.rglob('*') if p.is_file() and not p.name.startswith('.')]
    
    if not all_files:
        logging.warning("Nenhum ficheiro encontrado para processar.")
        return

    success_count = 0
    fail_count = 0
    skipped_count = 0

    with tqdm(total=len(all_files), desc="A processar ficheiros", unit="file") as pbar:
        for file_path in all_files:
            relative_path, status, error_msg = process_single_file(file_path, r2_manifest)
            
            if status == "SUCCESS" or status == "COPIED_UNSUPPORTED":
                success_count += 1
            elif status == "SKIPPED":
                skipped_count += 1
            else: # FAILURE ou IGNORED_PATTERN
                fail_count += 1
                if status == "FAILURE":
                    logging.error(f"Falha ao processar '{relative_path}': {error_msg or 'Erro desconhecido'}")
            
            pbar.update(1)

    logging.info(f"Processamento concluído. Sucesso: {success_count}, Ignorados (sem alterações): {skipped_count}, Falhas: {fail_count}")
    if fail_count > 0:
        logging.error("Ocorreram falhas durante o processamento. O workflow irá falhar.")
        exit(1)

if __name__ == "__main__":
    logging.info("--- INÍCIO DO PIPELINE DE PROCESSAMENTO ---")
    setup_directories()
    download_assets()
    process_all_files()
    logging.info("--- PIPELINE CONCLUÍDO ---")
