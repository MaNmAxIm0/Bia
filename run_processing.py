# run_processing.py

import os
import subprocess
import logging
import shlex
import shutil
from tqdm import tqdm
import sys

# Importa as configurações e os processadores
import config
from processors.video_processor import apply_watermark_to_video
# Descomente a linha abaixo quando o processador de imagem estiver pronto
# from processors.image_processor import apply_watermark_to_image

# Configura o logging para ser claro e informativo, enviando para a saída padrão
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def setup_directories():
    """Cria os diretórios locais necessários se não existirem."""
    logging.info(f"A garantir que os diretórios '{config.LOCAL_DOWNLOAD_DIR}' e '{config.LOCAL_PROCESSED_DIR}' existem.")
    os.makedirs(config.LOCAL_DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(config.LOCAL_PROCESSED_DIR, exist_ok=True)

def download_assets():
    """Descarrega os ficheiros da origem definida no config.py para o diretório local."""
    logging.info(f"A iniciar o download de ficheiros de '{config.SOURCE_RCLONE_PATH}'...")
    try:
        # Constrói o comando rclone a partir das configurações
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
        exit(1) # Termina o script se o download falhar

def process_all_files():
    """Itera sobre os ficheiros descarregados, aplicando a marca de água ou copiando-os."""
    logging.info("A iniciar o processamento de todos os ficheiros descarregados...")
    
    # Cria uma lista de todos os ficheiros no diretório de download, ignorando ficheiros ocultos
    file_list = [
        os.path.join(root, file)
        for root, _, files in os.walk(config.LOCAL_DOWNLOAD_DIR)
        for file in files if not file.startswith('.')
    ]

    if not file_list:
        logging.warning("Nenhum ficheiro encontrado para processar. Verifique se o download foi bem-sucedido e se a pasta de origem não está vazia.")
        return

    success_count = 0
    fail_count = 0

    with tqdm(total=len(file_list), desc="A processar ficheiros", unit="file") as pbar:
        for file_path in file_list:
            filename = os.path.basename(file_path)
            _, extension = os.path.splitext(filename.lower())
            
            # Define o caminho de saída mantendo a estrutura de pastas
            relative_path = os.path.relpath(file_path, config.LOCAL_DOWNLOAD_DIR)
            output_path = os.path.join(config.LOCAL_PROCESSED_DIR, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            processed = False
            
            # Verifica se o ficheiro deve ser ignorado com base nos padrões
            if hasattr(config, 'EXCLUDE_PATTERNS') and any(filename.endswith(ext) for ext in config.EXCLUDE_PATTERNS):
                pbar.update(1)
                continue

            # Processa imagens (se a função estiver disponível)
            # if extension in config.IMAGE_EXTENSIONS:
            #     if 'apply_watermark_to_image' in globals():
            #         if apply_watermark_to_image(file_path, output_path, config):
            #             success_count += 1
            #         else:
            #             fail_count += 1
            #         processed = True

            # Processa vídeos
            if extension in config.VIDEO_EXTENSIONS:
                if apply_watermark_to_video(file_path, output_path, config):
                    success_count += 1
                else:
                    fail_count += 1
                processed = True
            
            # Se não foi processado, copia o ficheiro diretamente
            if not processed:
                try:
                    shutil.copy2(file_path, output_path)
                    logging.info(f"Ficheiro '{filename}' com extensão não suportada. A copiar diretamente.")
                except Exception as e:
                    logging.error(f"Não foi possível copiar o ficheiro '{filename}': {e}")
                    fail_count += 1

            pbar.update(1)

    logging.info(f"Processamento concluído. Ficheiros com sucesso: {success_count}, Falhas: {fail_count}")
    if fail_count > 0:
        logging.warning("Alguns ficheiros não puderam ser processados. Verifique os logs de erro acima.")

if __name__ == "__main__":
    logging.info("--- INÍCIO DO PIPELINE DE PROCESSAMENTO ---")
    setup_directories()
    download_assets()
    process_all_files()
    logging.info("--- FIM DO PIPELINE DE PROCESSAMENTO ---")
    logging.info("O upload dos ficheiros processados será gerido pelo passo seguinte no workflow.")
