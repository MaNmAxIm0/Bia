# Ficheiro: scripts/process_files.py (VERSÃO FINAL COM CORREÇÃO DO COMANDO)

import subprocess
import json
import os
import time
import sys
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- Configuração ---
RCLONE_REMOTE = "R2:bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias", "Vídeos": "videos", "Designs": "designs",
    "Apresentações": "apresentacoes", "Melhores": "carousel", "Capas": "covers"
}
THUMBNAIL_DIR_R2 = "Thumbnails"
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat-SemiBold.ttf')
TEMP_DIR = "temp_files"
DATA_FILE = "data.json"
MANIFEST_FILE = "r2_file_manifest.txt"
MAX_IMAGE_WIDTH = 1920
JPEG_QUALITY = 85

# --- Funções Auxiliares ---
def run_command(cmd, check=True):
    try:
        # Executa o comando e retorna o resultado.
        return subprocess.run(cmd, capture_output=True, text=True, check=check, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        # Se o comando falhar, imprime o erro.
        print(f"ERRO ao executar: {' '.join(cmd)}\n{e.stderr}")
        return None

def get_rclone_json_list(path, flags=None):
    """Obtém uma lista de ficheiros do R2 em formato JSON."""
    if flags is None:
        flags = []
    # CORREÇÃO APLICADA AQUI: Utiliza o comando 'lsjson' que é o correto.
    cmd = ["rclone", "lsjson", path] + flags
    result = run_command(cmd)
    return json.loads(result.stdout) if result and result.stdout else []

def get_last_manifest_time():
    """Lê a data do último manifesto para saber o que processar."""
    try:
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("Gerado em:"):
                    parts = line.split()
                    date_str = " ".join(parts[2:5] + [parts[6]])
                    return datetime.strptime(date_str, "%b %d %H:%M:%S %Y").replace(tzinfo=timezone.utc)
    except Exception:
        print(f"AVISO: Manifesto não encontrado ou inválido. A processar todos os ficheiros.")
    return datetime.fromtimestamp(0, tz=timezone.utc)

def parse_filename_for_titles(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[2].replace('-', ' ')}
    return {'pt': name_without_ext.replace('-', ' '), 'en': name_without_ext.replace('-', ' '), 'es': name_without_ext.replace('-', ' ')}

def get_media_dimensions(local_path, is_video):
    try:
        if not is_video:
            with Image.open(local_path) as img:
                return ImageOps.exif_transpose(img).size
        else:
            result = run_command(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path])
            if result:
                dims = json.loads(result.stdout)["streams"][0]
                return int(dims.get("width", 0)), int(dims.get("height", 0))
    except Exception as e:
        print(f"  AVISO: Não foi possível obter dimensões para '{local_path}'. Erro: {e}", file=sys.stderr)
    return 0, 0

def generate_thumbnail(video_path, thumb_path):
    print(f"  -> A gerar thumbnail para: {os.path.basename(video_path)}")
    try:
        command = ["ffmpeg", "-i", video_path, "-ss", "00:00:01.000", "-vframes", "1", "-q:v", "2", "-y", thumb_path]
        run_command(command)
        return True
    except Exception as e:
        print(f"  ERRO ao gerar thumbnail: {e}", file=sys.stderr)
        return False

def apply_watermark(input_path, output_path, is_video):
    width, height = get_media_dimensions(input_path, is_video)
    if width == 0:
        return False
    try:
        if not is_video:
            with Image.open(input_path) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode == 'RGBA':
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                if img.width > MAX_IMAGE_WIDTH:
                    h = int((MAX_IMAGE_WIDTH / img.width) * img.height)
                    img = img.resize((MAX_IMAGE_WIDTH, h), Image.Resampling.LANCZOS)
                draw = ImageDraw.Draw(img)
                font_size = max(24, int(img.height * 0.05))
                font = ImageFont.truetype(FONT_PATH, font_size)
                bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
                text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                margin = int(img.width * 0.025)
                position = (img.width - text_width - margin, img.height - text_height - margin)
                draw.text((position[0] + 2, position[1] + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
                draw.text(position, WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220))
                img.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        else: # é vídeo
            font_size = max(30, int(width * 0.055))
            margin = int(width * 0.025)
            escaped_text = WATERMARK_TEXT.replace("'", "'\\\\''")
            escaped_font_path = FONT_PATH.replace(":", "\\\\:")
            vf_command = f"drawtext=text='{escaped_text}':fontfile='{escaped_font_path}':fontsize={font_size}:fontcolor=white@0.8:x=w-text_w-{margin}:y=h-text_h-{margin}:shadowcolor=black@0.6:shadowx=2:shadowy=2"
            command = ["ffmpeg", "-i", input_path, "-vf", vf_command, "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "copy", "-y", output_path]
            run_command(command)
        return True
    except Exception as e:
        print(f"  ERRO DETALHADO ao aplicar marca de água: {e}", file=sys.stderr)
        return False

# --- Lógica Principal ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO E GERAÇÃO DE DADOS...")
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("\n--- [FASE 1] Verificando ficheiros novos ou modificados ---")
    all_files_data = get_rclone_json_list(RCLONE_REMOTE, ["--recursive"])
    
    # Se a primeira listagem falhar (por exemplo, o bucket estar vazio), não podemos continuar.
    if not all_files_data:
        print("AVISO: Nenhum ficheiro encontrado no bucket R2. A sair do script.")
        # Cria ficheiros vazios para não dar erro no commit
        with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump({key: [] for key in CATEGORIES.values()}, f)
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f: f.write("Manifesto vazio.")
        sys.exit(0)

    existing_thumbnails = {os.path.splitext(f["Name"])[0] for f in get_rclone_json_list(f"{RCLONE_REMOTE}/{THUMBNAIL_DIR_R2}")}
    last_run_time = get_last_manifest_time()

    for item in all_files_data:
        try:
            path = item["Path"]
            filename = os.path.basename(path)
            basename, _ = os.path.splitext(filename)
            category_folder = os.path.dirname(path)

            if category_folder not in CATEGORIES or CATEGORIES[category_folder] == "covers": continue
            
            mod_time = datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00"))
            if mod_time < last_run_time: continue

            print(f"-> Processando ficheiro modificado: {path}")
            
            local_path = os.path.join(TEMP_DIR, filename)
            run_command(["rclone", "copyto", f"{RCLONE_REMOTE}/{path}", local_path])
            
            is_video = CATEGORIES.get(category_folder) == "videos"

            # Gera thumbnail se for um vídeo e não existir
            if is_video and basename not in existing_thumbnails:
                local_thumb_path = os.path.join(TEMP_DIR, f"{basename}.jpg")
                if generate_thumbnail(local_path, local_thumb_path):
                    run_command(["rclone", "copyto", local_thumb_path, f"{RCLONE_REMOTE}/{THUMBNAIL_DIR_R2}/{basename}.jpg"])
                    os.remove(local_thumb_path)
            
            # Aplica marca de água
            print(f"  -> A aplicar marca de água...")
            local_processed_path = os.path.join(TEMP_DIR, f"wm_{filename}")
            if apply_watermark(local_path, local_processed_path, is_video):
                print(f"  -> A enviar ficheiro com marca de água para: {path}")
                run_command(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE}/{path}"])
            
            # Limpa ficheiros temporários
            if os.path.exists(local_path): os.remove(local_path)
            if os.path.exists(local_processed_path): os.remove(local_processed_path)

        except Exception as e:
             print(f"  -> ERRO CRÍTICO ao processar {item.get('Path', 'item desconhecido')}: {e}")
            
    print("\n--- [FASE 2] Gerando o ficheiro data.json e o manifesto final ---")
    final_r2_files = get_rclone_json_list(RCLONE_REMOTE, ["--recursive"])
    new_data = {v: [] for v in CATEGORIES.values()}
    
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        f.write(f"Manifesto de Ficheiros do Bucket '{os.path.basename(RCLONE_REMOTE)}'\n")
        f.write(f"Gerado em: {datetime.now().strftime('%a %b %d %H:%M:%S WEST %Y')}\n")
        f.write("----------------------------------------------------\n")
        
        for item in sorted(final_r2_files, key=lambda x: x["ModTime"], reverse=True):
            path, mod_time_str, size = item["Path"], item["ModTime"], item["Size"]
            mod_time = datetime.fromisoformat(mod_time_str.replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{mod_time}\t{size:>10}\t{path}\n")

            category_folder = os.path.dirname(path)
            if category_folder in CATEGORIES:
                category_key = CATEGORIES[category_folder]
                file_data = {"name": os.path.basename(path), "titles": parse_filename_for_titles(item["Name"]), "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}"}
                if category_key == 'videos':
                    thumb_name = os.path.splitext(item["Name"])[0]
                    file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAIL_DIR_R2}/{thumb_name.replace(' ', '%20')}.jpg"
                new_data[category_key].append(file_data)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print("Ficheiro data.json e manifesto gerados com sucesso.")
    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()
