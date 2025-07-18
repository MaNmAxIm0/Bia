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
import subprocess
from PIL import Image
import os # <-- CORREÇÃO: Importação do módulo 'os'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

def get_asset_dimensions(file_path: Path) -> tuple:
    """Obtém as dimensões (largura, altura) de um ficheiro de imagem ou vídeo."""
    try:
        with Image.open(file_path) as img:
            return img.size
    except Exception:
        try:
            cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height', '-of', 'json', str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_data = json.loads(result.stdout)
            return video_data['streams'][0]['width'], video_data['streams'][0]['height']
        except Exception as e:
            logging.warning(f"Não foi possível obter as dimensões para {file_path.name}: {e}")
    return None, None

def generate_structured_json(processed_files: list):
    """Gera um ficheiro data.json estruturado por categoria, com títulos e orientação."""
    logging.info("Gerando ficheiro de metadados data.json com estrutura completa...")
    
    if "<" in config.R2_PUBLIC_URL or "xxxx" in config.R2_PUBLIC_URL:
        logging.error("A variável R2_PUBLIC_URL no config.py precisa de ser definida!")
        return

    final_data_structure = {}

    for file_info in processed_files:
        relative_path = Path(file_info["path"])
        local_path = config.PROCESSED_ASSETS_DIR / relative_path
        
        category = relative_path.parts[0].lower() if len(relative_path.parts) > 1 else "outros"
        
        if category not in final_data_structure:
            final_data_structure[category] = []

        file_name = relative_path.name
        title_parts = relative_path.stem.split('_')
        
        pt_title = title_parts[0] if len(title_parts) > 0 else ""
        en_title = title_parts[1] if len(title_parts) > 1 else pt_title
        es_title = title_parts[2] if len(title_parts) > 2 else pt_title
        
        titles = {"pt": pt_title, "en": en_title, "es": es_title}
        
        url_path = str(relative_path).replace(Path(relative_path)._flavour.sep, '/')
        full_url = f"{config.R2_PUBLIC_URL.rstrip('/')}/{url_path}"
        
        asset_data = {
            "name": file_name,
            "titles": titles,
            "url": full_url
        }
        
        # --- ATUALIZADO: Só obter dimensões para imagens e vídeos ---
        file_ext = relative_path.suffix.lower()
        is_media_file = file_ext in config.IMAGE_EXTENSIONS or file_ext in config.VIDEO_EXTENSIONS

        if is_media_file:
            width, height = get_asset_dimensions(local_path)
            if width and height:
                asset_data["orientation"] = "horizontal" if width >= height else "vertical"

        if file_ext in config.VIDEO_EXTENSIONS:
            thumb_name = f"{relative_path.stem}_thumb.jpg"
            thumb_url_path = (Path(url_path).parent / thumb_name).as_posix()
            asset_data["thumbnail_url"] = f"{config.R2_PUBLIC_URL.rstrip('/')}/{thumb_url_path}"
        
        final_data_structure[category].append(asset_data)

    with open(config.JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data_structure, f, ensure_ascii=False, indent=2)
    
    logging.info(f"'{config.JSON_OUTPUT_FILE.name}' gerado com sucesso com a estrutura final.")


def main():
    """Orquestra todo o pipeline de processamento de média."""
    logging.info("--- INÍCIO DO PIPELINE DE PROCESSAMENTO ---")
    
    config.LOCAL_ASSETS_DIR.mkdir(exist_ok=True)
    config.PROCESSED_ASSETS_DIR.mkdir(exist_ok=True)
    (config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR).mkdir(exist_ok=True)
    
    rclone_handler.download_all_assets()

    files_to_process = []
    for root, _, files in os.walk(config.LOCAL_ASSETS_DIR):
        for file in files:
            if not file.startswith('.'):
                files_to_process.append(Path(root) / file)

    if not files_to_process:
        logging.warning("Nenhum ficheiro encontrado para processar após o download.")
        return

    logging.info(f"Iniciando o processamento de {len(files_to_process)} ficheiros...")
    failed_files = []
    successfully_processed = []

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

            if success:
                successfully_processed.append({"path": str(relative_path)})
            else:
                failed_files.append(str(relative_path))
            
            pbar.update(1)

    # A função upload_assets agora usa 'sync' para espelhar as eliminações
    rclone_handler.upload_assets()
    rclone_handler.generate_r2_manifest_file()
    generate_structured_json(successfully_processed)

    if failed_files:
        logging.error(f"{len(failed_files)} ficheiros falharam ao processar.")
        with open(config.FAILED_FILES_LOG, 'w') as f:
            f.write("\n".join(failed_files))

    logging.info("--- FIM DO PIPELINE ---")

if __name__ == "__main__":
    main()
