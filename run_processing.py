# run_processing.py

import os
import subprocess
import logging
import shlex
import shutil  # Importado para copiar ficheiros
from pathlib import Path  # Importado para uma gestão de caminhos moderna
from tqdm import tqdm
import sys

# Importa as configurações e os processadores
import config
# from processors.image_processor import apply_watermark_to_image
from processors.video_processor import apply_watermark_to_video

# Configura o logging para ser claro e informativo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def setup_directories():
    """Cria os diretórios locais necessários se não existirem."""
    logging.info(f"A garantir que os diretórios '{config.LOCAL_DOWNLOAD_DIR}' e '{config.LOCAL_PROCESSED_DIR}' existem.")
    # Usa Path para criar os diretórios
    Path(config.LOCAL_DOWNLOAD_DIR).mkdir(exist_ok=True)
    Path(config.LOCAL_PROCESSED_DIR).mkdir(exist_ok=True)

def download_assets():
    """Descarrega os ficheiros da origem (Google Drive) para o diretório local."""
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
        logging.error("Falha no download dos ficheiros com rclone. O script será terminado.")
        logging.error(f"Rclone stderr: {e.stderr}")
        exit(1)

def process_all_files():
    """Itera sobre os ficheiros descarregados, aplicando a marca de água ou copiando-os."""
    logging.info("A iniciar o processamento de todos os ficheiros descarregados...")
    
    # --- CORREÇÃO --- A lista de ficheiros foi inicializada usando Path.rglob.
    # Este método é eficiente e retorna objetos Path diretamente.
    source_dir = Path(config.LOCAL_DOWNLOAD_DIR)
    all_files = [p for p in source_dir.rglob('*') if p.is_file() and not p.name.startswith('.')]

    if not all_files:
        logging.warning("Nenhum ficheiro encontrado para processar. Verifique se o download foi bem-sucedido.")
        return

    success_count = 0
    fail_count = 0

    with tqdm(total=len(all_files), desc="A processar ficheiros", unit="file") as pbar:
        for file_path in all_files:
            relative_path = file_path.relative_to(source_dir)
            output_path = Path(config.LOCAL_PROCESSED_DIR) / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)

            extension = file_path.suffix.lower()

            # Verifica se o ficheiro deve ser excluído
            if hasattr(config, 'EXCLUDE_PATTERNS') and any(file_path.name.endswith(ext) for ext in config.EXCLUDE_PATTERNS):
                pbar.update(1)
                continue

            # Processa imagens (se a função estiver disponível)
            # if extension in config.IMAGE_EXTENSIONS:
            #     if 'apply_watermark_to_image' in globals() and apply_watermark_to_image(str(file_path), str(output_path), config):
            #         success_count += 1
            #     else:
            #         fail_count += 1
            
            # Processa vídeos
            if extension in config.VIDEO_EXTENSIONS:
                if apply_watermark_to_video(str(file_path), str(output_path), config):
                    success_count += 1
                else:
                    fail_count += 1
            
            # Se não for um tipo de ficheiro processável, apenas o copia
            else:
                try:
                    shutil.copy2(file_path, output_path)
                    # O log para cópia pode ser verboso, então pode ser comentado se preferir
                    # logging.info(f"Ficheiro '{file_path.name}' não processável. A copiar diretamente.")
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
    logging.info("--- FIM DO PIPELINE DE PROCESSAMENTO ---")
