# run_processing.py

import os
import subprocess
import logging
from tqdm import tqdm
import shlex
import shutil # Adicionado para a cópia de ficheiros não processados

import config
# from processors.image_processor import apply_watermark_to_image
from processors.video_processor import apply_watermark_to_video

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_directories():
    """Cria os diretórios locais necessários."""
    os.makedirs(config.LOCAL_DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(config.LOCAL_PROCESSED_DIR, exist_ok=True)

def download_assets():
    """Descarrega os ficheiros do R2, aplicando as exclusões definidas no config.py."""
    logging.info(f"A descarregar ficheiros de '{config.SOURCE_RCLONE_PATH}'...")
    try:
        # --- CORREÇÃO --- Constrói o comando dinamicamente a partir do config.py
        command = [
            "rclone", "copy", config.SOURCE_RCLONE_PATH, config.LOCAL_DOWNLOAD_DIR,
            "--progress"
        ]
        
        # Adiciona todas as regras de exclusão do ficheiro de configuração
        for pattern in config.RCLONE_EXCLUDE_PATTERNS:
            command.extend(["--exclude", pattern])

        logging.info(f"A executar Rclone: {' '.join(shlex.quote(c) for c in command)}")
        subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info("Download concluído com sucesso.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha no download dos ficheiros com rclone. Stderr: {e.stderr}")
        exit(1)

def upload_processed_assets():
    """Carrega os ficheiros processados para o R2."""
    logging.info(f"A carregar ficheiros para '{config.DEST_RCLONE_PATH}'...")
    try:
        command = [
            "rclone", "copy", config.LOCAL_PROCESSED_DIR, config.DEST_RCLONE_PATH,
            "--progress"
        ]
        logging.info(f"A executar Rclone: {' '.join(shlex.quote(c) for c in command)}")
        subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info("Upload concluído com sucesso.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha no upload dos ficheiros com rclone. Stderr: {e.stderr}")
        exit(1)

def process_all_files():
    """Itera sobre os ficheiros, aplicando a marca de água apropriada."""
    logging.info("A iniciar o processamento de ficheiros...")
    
    file_list = []
    for root, _, files in os.walk(config.LOCAL_DOWNLOAD_DIR):
        for file in files:
            if not file.startswith('.'):
                file_list.append(os.path.join(root, file))

    success_count = 0
    fail_count = 0

    with tqdm(total=len(file_list), desc="A processar ficheiros") as pbar:
        for file_path in file_list:
            filename = os.path.basename(file_path)
            _, extension = os.path.splitext(filename.lower())
            
            relative_path = os.path.relpath(file_path, config.LOCAL_DOWNLOAD_DIR)
            output_path = os.path.join(config.LOCAL_PROCESSED_DIR, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            processed = False
            if any(filename == pattern for pattern in config.LOCAL_EXCLUDE_FILENAMES):
                pbar.update(1)
                continue

            # if extension in config.IMAGE_EXTENSIONS:
            #     if apply_watermark_to_image(file_path, output_path, config): success_count += 1
            #     else: fail_count += 1
            #     processed = True

            if extension in config.VIDEO_EXTENSIONS:
                if apply_watermark_to_video(file_path, output_path, config): success_count += 1
                else: fail_count += 1
                processed = True
            
            if not processed:
                shutil.copy2(file_path, output_path)
                logging.info(f"Ficheiro '{filename}' com extensão não suportada. A copiar diretamente.")

            pbar.update(1)

    logging.info(f"Processamento concluído. Sucesso: {success_count}, Falhas: {fail_count}")
    if fail_count > 0:
        logging.warning("Alguns ficheiros não puderam ser processados. Verifique os logs de erro acima.")

if __name__ == "__main__":
    setup_directories()
    download_assets()
    process_all_files()
    # upload_processed_assets()
    logging.info("Pipeline concluído.")
