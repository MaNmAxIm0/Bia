# main.py

import logging
import json
from pathlib import Path
from tqdm import tqdm
import config
from processors import image_processor, video_processor
from utils import rclone_handler
import shutil
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

def main():
    """Orquestra todo o pipeline de processamento de média."""
    logging.info("--- INÍCIO DO PIPELINE DE PROCESSAMENTO INCREMENTAL ---")
    
    config.LOCAL_ASSETS_DIR.mkdir(exist_ok=True)
    config.PROCESSED_ASSETS_DIR.mkdir(exist_ok=True)
    
    # 1. Obter o estado atual do R2
    r2_manifest = rclone_handler.get_r2_manifest_as_dict()
    
    # 2. Descarregar apenas os ficheiros novos ou modificados
    rclone_handler.download_changed_assets(r2_manifest)

    # 3. Processar apenas os ficheiros que foram descarregados
    files_to_process = [p for p in config.LOCAL_ASSETS_DIR.rglob('*') if p.is_file()]
    if not files_to_process:
        logging.info("Nenhum ficheiro para processar nesta execução.")
        logging.info("--- FIM DO PIPELINE ---")
        return

    logging.info(f"Iniciando o processamento de {len(files_to_process)} ficheiros...")
    failed_files = []

    with tqdm(total=len(files_to_process), desc="Processando ativos") as pbar:
        for file_path in files_to_process:
            pbar.set_description(f"Processando {file_path.name}")
            relative_path = file_path.relative_to(config.LOCAL_ASSETS_DIR)
            output_path = config.PROCESSED_ASSETS_DIR / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            extension = file_path.suffix.lower()
            success = False

            if extension in config.IMAGE_EXTENSIONS:
                success = image_processor.process_image(file_path, output_path)
            elif extension in config.VIDEO_EXTENSIONS:
                success = video_processor.apply_video_watermark(file_path, output_path)
                if success:
                    video_processor.generate_thumbnail(output_path)
            else:
                shutil.copy2(file_path, output_path)
                success = True

            if not success:
                failed_files.append(str(relative_path))
            
            pbar.update(1)

    # 4. Upload e geração de manifestos finais
    rclone_handler.upload_assets()
    rclone_handler.generate_r2_manifest_file()
    
    # A geração do data.json pode ser mais complexa, por agora fica como placeholder
    logging.info("Gerando ficheiro de metadados data.json (placeholder)...")
    with open(config.JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({"status": "processamento concluído"}, f, indent=2)

    if failed_files:
        logging.error(f"{len(failed_files)} ficheiros falharam ao processar.")
        with open(config.FAILED_FILES_LOG, 'w') as f:
            f.write("\n".join(failed_files))

    logging.info("--- FIM DO PIPELINE ---")

if __name__ == "__main__":
    main()
