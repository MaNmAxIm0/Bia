import os
import subprocess
import json
import logging
from PIL import Image, ImageOps, ImageDraw, ImageFont
from tqdm import tqdm
import shutil
from pathlib import Path

# --- CONFIGURAÇÃO ---
R2_PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
DRIVE_REMOTE_PATH = "Drive:Portfólio Bia"
R2_REMOTE_PATH = "R2:bia-portfolio-assets"
LOCAL_ASSETS_DIR = Path("local_assets" )
PROCESSED_ASSETS_DIR = Path("processed_assets")
THUMBNAILS_DIR = PROCESSED_ASSETS_DIR / "Thumbnails"
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = Path("fonts/Montserrat-Medium.ttf")

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi']

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

# --- FUNÇÕES AUXILIARES ---

def run_rclone_command(command: list, operation_name: str) -> bool:
    """Executa um comando rclone de forma segura e regista o resultado."""
    logging.info(f"Iniciando operação rclone: {operation_name}")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logging.info(f"Operação rclone '{operation_name}' concluída com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha na operação rclone '{operation_name}': {e.stderr.strip()}")
        return False

def get_media_dimensions(file_path: Path) -> tuple:
    """Obtém a largura e altura de uma imagem ou vídeo."""
    try:
        if file_path.suffix.lower() in IMAGE_EXTENSIONS:
            with Image.open(file_path) as img:
                return img.size
        elif file_path.suffix.lower() in VIDEO_EXTENSIONS:
            cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height', '-of', 'json', str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_data = json.loads(result.stdout)['streams'][0]
            return video_data['width'], video_data['height']
    except Exception as e:
        logging.warning(f"Não foi possível obter as dimensões para {file_path.name}: {e}")
    return None, None

# --- FUNÇÕES DE PROCESSAMENTO ---

def correct_image_orientation(img: Image.Image) -> Image.Image:
    """Verifica e corrige a orientação da imagem com base nos metadados EXIF."""
    try:
        return ImageOps.exif_transpose(img)
    except Exception as e:
        logging.warning(f"Não foi possível aplicar a transposição EXIF para uma imagem: {e}")
        return img

def apply_watermark_to_image(base_image: Image.Image) -> Image.Image:
    """Aplica uma marca de água de texto com sombra e tamanho dinâmico a uma imagem."""
    image_with_watermark = base_image.copy().convert("RGBA")
    draw = ImageDraw.Draw(image_with_watermark)
    font_size = int(image_with_watermark.width * 0.035)
    try:
        font = ImageFont.truetype(str(FONT_PATH), font_size)
    except IOError:
        logging.warning(f"Fonte '{FONT_PATH}' não encontrada. Usando fonte padrão.")
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    margin = int(image_with_watermark.width * 0.02)
    x = image_with_watermark.width - text_width - margin
    y = image_with_watermark.height - text_height - margin

    shadow_offset = int(font_size * 0.05)
    shadow_color = (0, 0, 0, 100)
    draw.text((x + shadow_offset, y + shadow_offset), WATERMARK_TEXT, font=font, fill=shadow_color)
    
    text_color = (255, 255, 255, 180)
    draw.text((x, y), WATERMARK_TEXT, font=font, fill=text_color)
    
    return image_with_watermark.convert("RGB")

def process_video(input_path: Path, output_path: Path) -> bool:
    """Aplica marca de água e gera uma thumbnail para um vídeo."""
    font_path_ffmpeg = str(FONT_PATH).replace("\\", "/").replace(":", "\\\\:")
    watermark_cmd = [
        "ffmpeg", "-i", str(input_path),
        "-vf", (
            f"drawtext=fontfile='{font_path_ffmpeg}':text='{WATERMARK_TEXT}':fontsize=h*0.03:fontcolor=black@0.5:x=(w-text_w-w*0.02)+2:y=(h-text_h-h*0.02)+2,"
            f"drawtext=fontfile='{font_path_ffmpeg}':text='{WATERMARK_TEXT}':fontsize=h*0.03:fontcolor=white@0.8:x=w-text_w-w*0.02:y=h-text_h-h*0.02"
        ),
        "-codec:v", "libx264", "-preset", "medium", "-crf", "23", "-codec:a", "copy", "-y", str(output_path)
    ]
    try:
        subprocess.run(watermark_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg falhou ao aplicar marca de água ao vídeo '{input_path.name}': {e.stderr.strip()}")
        return False

    thumbnail_path = THUMBNAILS_DIR / f"{input_path.stem}_thumb.jpg"
    thumbnail_cmd = ["ffmpeg", "-i", str(output_path), "-ss", "00:00:01.000", "-vframes", "1", "-q:v", "2", "-y", str(thumbnail_path)]
    try:
        subprocess.run(thumbnail_cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg falhou ao gerar thumbnail para '{input_path.name}': {e.stderr.strip()}")
        return True

# --- GERAÇÃO DE METADATOS ---

def generate_data_json(output_file: str):
    """Gera um ficheiro data.json que cataloga todos os ativos por categoria e orientação."""
    logging.info("Gerando ficheiro de metadados data.json com estrutura completa...")
    if "xxxx" in R2_PUBLIC_URL:
        logging.warning("A variável R2_PUBLIC_URL não foi definida! Os URLs no data.json estarão incorretos.")

    asset_catalog = {}
    
    all_processed_files = list(PROCESSED_ASSETS_DIR.rglob("*.*"))

    for file_path_local in all_processed_files:
        if file_path_local.parent.name == "Thumbnails" or not file_path_local.is_file():
            continue

        relative_path = file_path_local.relative_to(PROCESSED_ASSETS_DIR)
        category = relative_path.parts[0] if len(relative_path.parts) > 1 else "geral"
        
        if category not in asset_catalog:
            asset_catalog[category] = {"horizontal": [], "vertical": []}

        url_path = relative_path.as_posix()
        asset_info = {
            "path": url_path,
            "url": f"{R2_PUBLIC_URL.rstrip('/')}/{url_path}"
        }

        width, height = get_media_dimensions(file_path_local)
        orientation = "horizontal"
        if width is not None and height is not None and height > width:
            orientation = "vertical"
        
        if file_path_local.suffix.lower() in VIDEO_EXTENSIONS:
            thumbnail_filename = f"{file_path_local.stem}_thumb.jpg"
            asset_info["thumbnail_url"] = f"{R2_PUBLIC_URL.rstrip('/')}/Thumbnails/{thumbnail_filename}"

        asset_catalog[category][orientation].append(asset_info)

    final_data_structure = {"pt": asset_catalog}
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data_structure, f, indent=4, ensure_ascii=False)
    
    logging.info(f"'{output_file}' gerado com sucesso com a estrutura final.")

# --- FLUXO DE TRABALHO PRINCIPAL ---

def main():
    logging.info("--- INÍCIO DO PIPELINE DE PROCESSAMENTO ---")

    if LOCAL_ASSETS_DIR.exists(): shutil.rmtree(LOCAL_ASSETS_DIR)
    if PROCESSED_ASSETS_DIR.exists(): shutil.rmtree(PROCESSED_ASSETS_DIR)
    PROCESSED_ASSETS_DIR.mkdir(exist_ok=True)
    THUMBNAILS_DIR.mkdir(exist_ok=True)

    download_cmd = ["rclone", "copy", DRIVE_REMOTE_PATH, str(LOCAL_ASSETS_DIR), "--progress"]
    if not run_rclone_command(download_cmd, "Download de ativos do Drive"):
        logging.error("Pipeline interrompido devido a falha no download.")
        return

    all_local_files = [p for p in LOCAL_ASSETS_DIR.rglob("*") if p.is_file() and not p.name.startswith('.')]
    logging.info(f"Encontrados {len(all_local_files)} ficheiros para processar.")
    failure_count = 0

    with tqdm(total=len(all_local_files), desc="Processando ficheiros") as pbar:
        for input_path in all_local_files:
            relative_path = input_path.relative_to(LOCAL_ASSETS_DIR)
            output_path = PROCESSED_ASSETS_DIR / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_ext = input_path.suffix.lower()
            processed_successfully = False

            try:
                if file_ext in IMAGE_EXTENSIONS:
                    with Image.open(input_path) as img:
                        img = correct_image_orientation(img)
                        img = apply_watermark_to_image(img)
                        img.save(output_path, "JPEG", quality=90, optimize=True, progressive=True)
                        processed_successfully = True
                elif file_ext in VIDEO_EXTENSIONS:
                    if process_video(input_path, output_path):
                        processed_successfully = True
                else:
                    shutil.copy2(input_path, output_path)
                    processed_successfully = True
            except Exception as e:
                logging.error(f"Erro inesperado ao processar {input_path.name}: {e}")

            if not processed_successfully:
                failure_count += 1
            pbar.update(1)

    generate_data_json("data.json")

    if failure_count > 0:
        logging.warning(f"{failure_count} ficheiros falharam ao processar.")
    
    logging.info("--- FIM DO PIPELINE ---")

if __name__ == "__main__":
    main()
