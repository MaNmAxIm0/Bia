# run_processing.py

import os
import subprocess
import logging
from tqdm import tqdm
import shlex
from pathlib import Path
import shutil

import config
from processors.image_processor import apply_watermark_to_image
from processors.video_processor import apply_watermark_to_video

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_directories():
    """Cria os diretórios locais necessários."""
    logging.info(f"A garantir que os diretórios '{config.LOCAL_DOWNLOAD_DIR}' e '{config.LOCAL_PROCESSED_DIR}' existem.")
    os.makedirs(config.LOCAL_DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(config.LOCAL_PROCESSED_DIR, exist_ok=True)

def download_assets():
    """Descarrega os ficheiros do Google Drive para o diretório local."""
    logging.info(f"A iniciar o download de ficheiros de '{config.SOURCE_RCLONE_PATH}'...")
    try:
        # --- ESPAÇO VAZIO PREENCHIDO ---
        command = [
            "rclone", "copy", config.SOURCE_RCLONE_PATH, config.LOCAL_DOWNLOAD_DIR,
            "--progress"
        ]
        logging.info(f"A executar Rclone: {' '.join(shlex.quote(c) for c in command)}")
        subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info("Download concluído com sucesso.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha no download dos ficheiros com rclone. O script será terminado.")
        logging.error(f"Rclone stderr: {e.stderr}")
        exit(1)

def process_all_files():
    """Itera sobre os ficheiros, aplicando a marca de água apropriada."""
    logging.info("A iniciar o processamento de todos os ficheiros descarregados...")
    
    # --- ESPAÇO VAZIO PREENCHIDO ---
    source_dir = Path(config.LOCAL_DOWNLOAD_DIR)
    all_files = [p for p in source_dir.rglob('*') if p.is_file() and not p.name.startswith('.')]
    
    success_count = 0
    fail_count = 0

    with tqdm(total=len(all_files), desc="A processar ficheiros") as pbar:
        for file_path in all_files:
            relative_path = file_path.relative_to(config.LOCAL_DOWNLOAD_DIR)
            output_path = Path(config.LOCAL_PROCESSED_DIR) / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)

            extension = file_path.suffix.lower()

            if any(file_path.name.endswith(ext) for ext in config.EXCLUDE_PATTERNS):
                pbar.update(1)
                continue

            # ## CORREÇÃO CRÍTICA ##
            # A lógica anterior tinha um bug. Esta nova estrutura if/elif/else
            # garante que as imagens e vídeos são processados, e só os restantes
            # ficheiros (como PDFs) são copiados.
            if extension in config.IMAGE_EXTENSIONS:
                if apply_watermark_to_image(str(file_path), str(output_path), config):
                    success_count += 1
                else:
                    fail_count += 1
            elif extension in config.VIDEO_EXTENSIONS:
                if apply_watermark_to_video(str(file_path), str(output_path), config):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                # Se não for imagem nem vídeo, apenas copia o ficheiro
                logging.info(f"Ficheiro '{file_path.name}' não é imagem nem vídeo. A copiar diretamente.")
                try:
                    shutil.copy(file_path, output_path)
                    success_count += 1
                except Exception as e:
                    logging.error(f"Falha ao copiar '{file_path.name}'. Motivo: {e}")
                    fail_count += 1
            
            pbar.update(1)

    logging.info(f"Processamento concluído. Sucesso: {success_count}, Falhas: {fail_count}")
    if fail_count > 0:
        logging.warning("Alguns ficheiros não puderam ser processados. Verifique os logs de erro acima.")

if __name__ == "__main__":
    logging.info("--- INÍCIO DO PIPELINE DE PROCESSAMENTO ---")
    setup_directories()
    download_assets()
    process_all_files()
    logging.info("--- PIPELINE CONCLUÍDO ---")
