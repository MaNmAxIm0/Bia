import subprocess
import json
import os
import time
from PIL import Image, ImageDraw, ImageFont, ExifTags

# --- Configuração ---
RCLONE_REMOTE_NAME = "R2"
GDRIVE_REMOTE_NAME = "Drive"
BUCKET_NAME = "bia-portfolio-assets"
GDRIVE_SOURCE_PATH = "Portfólio Bia"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias",
    "Vídeos": "videos",
    "Designs": "designs",
    "Apresentações": "apresentacoes"
}
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__ ), 'Montserrat.ttf')
TEMP_DIR = "temp_files"

# Pastas no R2
WATERMARKED_DIR_IMG = "WatermarkedImages"
WATERMARKED_DIR_VID = "WatermarkedVideos"
THUMBNAILS_DIR = "Thumbnails"

EXIF_ORIENTATION_TAG = next((tag for tag, name in ExifTags.TAGS.items() if name == 'Orientation'), None)


# --- Funções Rclone Auxiliares ---

def rclone_lsf(remote_path):
    command = ["rclone", "lsf", remote_path, "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return [line for line in result.stdout.strip().split('\n') if line]
    except subprocess.CalledProcessError:
        return []

def rclone_delete_file(remote_path):
    print(f"  - Apagando ficheiro obsoleto no R2: {remote_path}")
    command = ["rclone", "deletefile", remote_path]
    subprocess.run(command, check=True, capture_output=True)

# --- Funções de Processamento ---

def add_watermark_to_image(input_path, output_path):
    try:
        with Image.open(input_path).convert("RGBA") as base:
            # Correção de orientação EXIF antes de aplicar a marca de água
            if EXIF_ORIENTATION_TAG and hasattr(base, '_getexif'):
                exif = base._getexif()
                if exif and EXIF_ORIENTATION_TAG in exif:
                    orientation = exif[EXIF_ORIENTATION_TAG]
                    if orientation == 3: base = base.rotate(180, expand=True)
                    elif orientation == 6: base = base.rotate(270, expand=True)
                    elif orientation == 8: base = base.rotate(90, expand=True)

            draw = ImageDraw.Draw(base)
            font_size = max(20, int(base.width * 0.05))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except IOError:
                print("    AVISO: Ficheiro de fonte não encontrado. A usar fonte padrão.")
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            textwidth, textheight = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(base.width * 0.015)
            x, y = base.width - textwidth - margin, base.height - textheight - margin
            
            # Sombra do texto
            draw.text((x + 2, y + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            # Texto principal
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 180))
            
            base.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"    ERRO ao aplicar marca de água na imagem '{input_path}': {e}")
        return False

def add_watermark_to_video(input_path, output_path, video_width):
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", "")
    font_size = max(24, int(video_width * 0.04))
    margin = int(video_width * 0.015)
    command = [
        "ffmpeg", "-i", input_path, 
        "-vf", f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.7:x=main_w-text_w-{margin}:y=main_h-text_h-{margin}:shadowcolor=black@0.5:shadowx=2:shadowy=2", 
        "-c:a", "copy", "-y", output_path
    ]
    try:
        # Usar -loglevel error para não poluir o log com detalhes do ffmpeg
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    ERRO FFmpeg ao aplicar marca de água: {e.stderr}")
        return False

def get_dimensions(local_path, file_type):
    width, height = 0, 0
    try:
        if file_type in ['fotografias', 'designs']:
            with Image.open(local_path) as img:
                width, height = img.size
                if EXIF_ORIENTATION_TAG and hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif and EXIF_ORIENTATION_TAG in exif and exif[EXIF_ORIENTATION_TAG] in [5, 6, 7, 8]:
                        width, height = height, width # Inverte para a orientação correta
        elif file_type == 'videos':
            command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,tags=rotate", "-of", "json", local_path]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            stream_info = json.loads(result.stdout)["streams"][0]
            width, height = int(stream_info.get("width", 0)), int(stream_info.get("height", 0))
            # Verifica se o vídeo está rodado (comum em vídeos de telemóvel)
            if "tags" in stream_info and "rotate" in stream_info["tags"] and stream_info["tags"]["rotate"] in ["90", "-90"]:
                width, height = height, width
    except Exception as e:
        print(f"    AVISO: Não foi possível obter dimensões para {local_path}. Erro: {e}")
    return width, height

def parse_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    elif len(parts) == 2: return {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else: return {'pt': name_without_ext, 'en': name_without_ext, 'es': name_without_ext}


# --- Lógica Principal com Feedback de Progresso ---

def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO DE MEDIA...")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

    # 1. Mapear ficheiros de origem
    print("\n--- [FASE 1 de 5] Mapeando ficheiros de origem no Google Drive ---")
    source_files = {}
    for category_name, category_key in CATEGORIES.items():
        if category_key == "apresentacoes": continue
        print(f"  A listar ficheiros em: {category_name}...")
        path = f"{GDRIVE_REMOTE_NAME}:{GDRIVE_SOURCE_PATH}/{category_name}"
        files = rclone_lsf(path)
        for f in files:
            source_files[f] = {'category_key': category_key, 'category_name': category_name}
    total_files_to_process = len(source_files)
    print(f"MAPEAMENTO CONCLUÍDO: Encontrados {total_files_to_process} ficheiros de imagem/vídeo no Google Drive.")

    # 2. Verificar ficheiros existentes no R2
    print("\n--- [FASE 2 de 5] Verificando ficheiros já processados no R2 ---")
    print("  A listar imagens com marca de água...")
    watermarked_images_r2 = set(rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_IMG}"))
    print(f"  Encontradas {len(watermarked_images_r2)} imagens processadas.")
    print("  A listar vídeos com marca de água...")
    watermarked_videos_r2 = set(rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_VID}"))
    print(f"  Encontrados {len(watermarked_videos_r2)} vídeos processados.")
    print("  A listar thumbnails...")
    thumbnails_r2 = set(rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{THUMBNAILS_DIR}"))
    print(f"  Encontradas {len(thumbnails_r2)} thumbnails.")

    # 3. Limpar ficheiros obsoletos
    print("\n--- [FASE 3 de 5] Limpando ficheiros obsoletos no R2 ---")
    expected_images = {f"{os.path.splitext(f)[0]}.png" for f, data in source_files.items() if data['category_key'] in ['fotografias', 'designs']}
    expected_videos = {f"{os.path.splitext(f)[0]}_wm{os.path.splitext(f)[1]}" for f, data in source_files.items() if data['category_key'] == 'videos'}
    expected_thumbnails = {f"{os.path.splitext(f)[0]}.jpg" for f, data in source_files.items() if data['category_key'] == 'videos'}

    for file_to_check in watermarked_images_r2 - expected_images:
        rclone_delete_file(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_IMG}/{file_to_check}")
    for file_to_check in watermarked_videos_r2 - expected_videos:
        rclone_delete_file(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_VID}/{file_to_check}")
    for file_to_check in thumbnails_r2 - expected_thumbnails:
        rclone_delete_file(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{THUMBNAILS_DIR}/{file_to_check}")
    print("Limpeza de ficheiros obsoletos concluída.")

    # 4. Processar ficheiros e gerar dados
    print("\n--- [FASE 4 de 5] Processando ficheiros e gerando data.json ---")
    output_data = {cat: [] for cat in CATEGORIES.values()}
    all_processed_files = watermarked_images_r2.union(watermarked_videos_r2)

    if total_files_to_process == 0:
        print("Nenhum ficheiro para processar.")
    else:
        for i, (filename, data) in enumerate(source_files.items()):
            # --- CÁLCULO E EXIBIÇÃO DA PERCENTAGEM ---
            progress = (i + 1) / total_files_to_process * 100
            print(f"[{progress:.1f}%] Processando ficheiro {i+1}/{total_files_to_process}: {filename}")
            
            category_key = data['category_key']
            category_name = data['category_name']
            base_name, ext = os.path.splitext(filename)
            
            file_data = {"name": filename, "titles": parse_filename(filename), "orientation": "unknown"}

            remote_watermarked_path = ""
            watermarked_filename_only = ""
            process_this_file = False
            
            if category_key in ["fotografias", "designs"]:
                watermarked_filename_only = f"{base_name}.png"
                remote_watermarked_path = f"{WATERMARKED_DIR_IMG}/{watermarked_filename_only}"
                if watermarked_filename_only not in all_processed_files:
                    process_this_file = True
                file_data["url"] = f"{PUBLIC_URL}/{remote_watermarked_path.replace(' ', '%20')}"
            elif category_key == "videos":
                watermarked_filename_only = f"{base_name}_wm{ext}"
                remote_watermarked_path = f"{WATERMARKED_DIR_VID}/{watermarked_filename_only}"
                if watermarked_filename_only not in all_processed_files:
                    process_this_file = True
                file_data["url"] = f"{PUBLIC_URL}/{remote_watermarked_path.replace(' ', '%20')}"
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{base_name}.jpg".replace(' ', '%20')

            local_original_path = os.path.join(TEMP_DIR, filename)

            if process_this_file:
                print(f"  -> Ficheiro novo. A descarregar e a aplicar marca de água...")
                subprocess.run(["rclone", "copyto", f"{GDRIVE_REMOTE_NAME}:{GDRIVE_SOURCE_PATH}/{category_name}/{filename}", local_original_path], check=True, capture_output=True)
                
                width, height = get_dimensions(local_original_path, category_key)
                file_data["orientation"] = "horizontal" if width >= height else "vertical"

                local_watermarked_path = os.path.join(TEMP_DIR, watermarked_filename_only)
                success = False
                if category_key in ["fotografias", "designs"]:
                    if add_watermark_to_image(local_original_path, local_watermarked_path):
                        success = True
                elif category_key == "videos":
                    if add_watermark_to_video(local_original_path, local_watermarked_path, width):
                        success = True
                
                if success:
                    print(f"  -> Marca de água aplicada. A enviar para o R2...")
                    subprocess.run(["rclone", "copyto", local_watermarked_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{remote_watermarked_path}"], check=True, capture_output=True)
                    print(f"  -> Envio concluído.")
                
                if os.path.exists(local_watermarked_path): os.remove(local_watermarked_path)
            else:
                # Se o ficheiro já existe, ainda precisamos das dimensões para o JSON
                print(f"  -> Ficheiro já processado. A obter dimensões...")
                subprocess.run(["rclone", "copyto", f"{GDRIVE_REMOTE_NAME}:{GDRIVE_SOURCE_PATH}/{category_name}/{filename}", local_original_path], check=True, capture_output=True)
                width, height = get_dimensions(local_original_path, category_key)
                file_data["orientation"] = "horizontal" if width >= height else "vertical"

            if os.path.exists(local_original_path): os.remove(local_original_path)
            
            output_data[category_key].append(file_data)
    
    # 5. Adicionar apresentações e finalizar
    print("\n--- [FASE 5 de 5] Adicionando apresentações e gerando ficheiro final ---")
    apresentacoes_path = f"{GDRIVE_REMOTE_NAME}:{GDRIVE_SOURCE_PATH}/Apresentações"
    print(f"  A listar ficheiros em: Apresentações...")
    apresentacoes_files = rclone_lsf(apresentacoes_path)
    for f in apresentacoes_files:
        output_data['apresentacoes'].append({
            "name": f,
            "titles": parse_filename(f),
            "url": f"{PUBLIC_URL}/Apresentações/{f.replace(' ', '%20')}",
            "orientation": "square" # Assumindo que apresentações são melhor representadas como quadrados
        })
    print(f"  Adicionadas {len(apresentacoes_files)} apresentações.")

    print("  A escrever o ficheiro data.json...")
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    end_time = time.time()
    print(f"\n>>> SCRIPT CONCLUÍDO COM SUCESSO em {end_time - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()
