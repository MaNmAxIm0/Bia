# main.py

import logging
import json
from pathlib import Path
from tqdm import tqdm
import config
from processors import image_processor, video_processor
from utils import rclone_handler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

def main():
    """Orquestra todo o pipeline de processamento de média."""
    logging.info("--- INÍCIO DO PIPELINE DE PROCESSAMENTO DE MÉDIA ---")
    
    # 1. Setup e Download
    config.LOCAL_ASSETS_DIR.mkdir(exist_ok=True)
    config.PROCESSED_ASSETS_DIR.mkdir(exist_ok=True)
    rclone_handler.download_assets()

    # 2. Processamento de Média
    all_files = [p for p in config.LOCAL_ASSETS_DIR.rglob('*') if p.is_file()]
    if not all_files:
        logging.warning("Nenhum ficheiro encontrado para processar.")
        return

    failed_files = []
    processed_metadata = []

    with tqdm(total=len(all_files), desc="Processando ativos") as pbar:
        for file_path in all_files:
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
                    # Gera thumbnail para o vídeo processado
                    video_processor.generate_thumbnail(output_path, output_path.parent)
            else:
                shutil.copy2(file_path, output_path)
                success = True

            if success:
                # Adicionar metadados para o data.json
                # (Lógica de extração de dimensões omitida por simplicidade, mas seria aqui)
                processed_metadata.append({"path": str(relative_path)})
            else:
                failed_files.append(str(relative_path))
            
            pbar.update(1)

    # 3. Pós-Processamento e Upload
    logging.info("Gerando ficheiro de metadados data.json...")
    with open(config.JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed_metadata, f, indent=2)

    rclone_handler.upload_assets()
    rclone_handler.generate_r2_manifest()

    if failed_files:
        logging.error(f"{len(failed_files)} ficheiros falharam ao processar.")
        with open(config.FAILED_FILES_LOG, 'w') as f:
            f.write("\n".join(failed_files))
        # O workflow irá detetar a falha e mover para quarentena
        # exit(1) # Comentado para permitir que o workflow continue

    logging.info("--- FIM DO PIPELINE ---")

if __name__ == "__main__":
    import shutil
    main()
