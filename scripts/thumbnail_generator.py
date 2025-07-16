import subprocess
import os
import sys

def run_command(cmd, check=True):
    """Função para executar comandos de terminal e verificar erros."""
    print(f"Executando: {' '.join(cmd)}", flush=True)
    # A codificação utf-8 é importante para nomes de ficheiros com acentos
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if check and result.returncode != 0:
        print(f"ERRO ao executar comando: {' '.join(cmd)}", file=sys.stderr)
        print(f"Stderr: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    # Retorna uma lista de linhas de output
    return result.stdout.strip().split("\n")

def get_file_list(path):
    """Função para obter a lista de ficheiros de uma pasta no R2."""
    print(f"A listar ficheiros em: {path}")
    # Usamos check=False para não falhar se a pasta estiver vazia
    return {line for line in run_command(["rclone", "lsf", path, "--files-only"], check=False) if line and not line.startswith("wm_")}

# --- Início da Lógica Principal ---
RCLONE_REMOTE = "R2:bia-portfolio-assets"
VIDEO_FOLDER = f"{RCLONE_REMOTE}/Vídeos"
THUMB_FOLDER = f"{RCLONE_REMOTE}/Thumbnails"
TEMP_DIR = "temp_download"

# Cria a pasta temporária se não existir
os.makedirs(TEMP_DIR, exist_ok=True)

# Obtém as listas de ficheiros
videos = get_file_list(VIDEO_FOLDER)
thumbnails = get_file_list(THUMB_FOLDER)
thumb_basenames = {os.path.splitext(t)[0] for t in thumbnails}

# Compara as listas para encontrar vídeos que precisam de thumbnail
videos_to_process = [v for v in videos if v and os.path.splitext(v)[0] not in thumb_basenames]

if not videos_to_process:
    print("Nenhuma thumbnail nova para gerar.")
    sys.exit(0)

print(f"\nThumbnails a serem geradas para: {videos_to_process}\n")

for video_filename in videos_to_process:
    if not video_filename:
        continue
    try:
        local_video_path = os.path.join(TEMP_DIR, video_filename)
        thumb_name = f"{os.path.splitext(video_filename)[0]}.jpg"
        local_thumb_path = os.path.join(TEMP_DIR, thumb_name)

        run_command(["rclone", "copyto", f"{VIDEO_FOLDER}/{video_filename}", local_video_path])
        run_command(["ffmpeg", "-nostdin", "-i", local_video_path, "-ss", "00:00:01.00", "-vframes", "1", "-q:v", "2", local_thumb_path])
        run_command(["rclone", "copyto", local_thumb_path, f"{THUMB_FOLDER}/{thumb_name}"])

        os.remove(local_video_path)
        os.remove(local_thumb_path)
        print(f"Thumbnail para '{video_filename}' gerada com sucesso.")

    except Exception as e:
        print(f"ERRO ao processar '{video_filename}': {e}", file=sys.stderr)

print("\nGeração de thumbnails concluída!")