# Ficheiro: /scripts/thumbnail_generator.py (VERSÃO CORRIGIDA E EFICIENTE)

import subprocess
import os
import sys

def run_command(cmd, check=True):
    """Função para executar comandos de terminal e verificar erros."""
    # O flush=True garante que os prints aparecem no log em tempo real.
    print(f"Executando: {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if check and result.returncode != 0:
        print(f"ERRO ao executar comando: {' '.join(cmd)}", file=sys.stderr)
        print(f"Stderr: {result.stderr}", file=sys.stderr)
        # Não termina o script inteiro, apenas retorna um erro para a chamada específica.
        return None
    return result.stdout.strip().split("\n")

def get_file_list(path):
    """Função para obter a lista de ficheiros de uma pasta no R2."""
    print(f"A listar ficheiros em: {path}")
    files = run_command(["rclone", "lsf", path, "--files-only"], check=False)
    if files is None:
        return set() # Retorna um conjunto vazio em caso de erro
    # Garante que linhas vazias não são incluídas
    return {line for line in files if line}

# --- Início da Lógica Principal ---
RCLONE_REMOTE = "R2:bia-portfolio-assets"
VIDEO_FOLDER = f"{RCLONE_REMOTE}/Vídeos"
THUMB_FOLDER = f"{RCLONE_REMOTE}/Thumbnails"
TEMP_DIR = "temp_download"

os.makedirs(TEMP_DIR, exist_ok=True)

# 1. Obter listas de ficheiros
videos = get_file_list(VIDEO_FOLDER)
thumbnails = get_file_list(THUMB_FOLDER)

# 2. Criar um conjunto de nomes base de thumbnails para uma pesquisa rápida
# Ex: transforma 'video1.jpg' em 'video1'
thumb_basenames = {os.path.splitext(t)[0] for t in thumbnails}
print(f"Encontradas {len(thumb_basenames)} thumbnails existentes.")

# 3. Filtrar a lista de vídeos para encontrar apenas os que precisam de thumbnail
videos_to_process = []
for v_filename in videos:
    # Ignora linhas vazias ou inválidas que possam ter vindo do rclone
    if not v_filename:
        continue
    
    video_basename = os.path.splitext(v_filename)[0]
    if video_basename not in thumb_basenames:
        videos_to_process.append(v_filename)

# 4. Processar apenas os vídeos necessários
if not videos_to_process:
    print("\nTODAS AS THUMBNAILS JÁ EXISTEM. Nenhuma ação necessária.")
    sys.exit(0)

print(f"\nENCONTRADOS {len(videos_to_process)} VÍDEOS NOVOS PARA PROCESSAR:")
for video in videos_to_process:
    print(f"- {video}")
print("-" * 20)


for video_filename in videos_to_process:
    try:
        local_video_path = os.path.join(TEMP_DIR, video_filename)
        thumb_name = f"{os.path.splitext(video_filename)[0]}.jpg"
        local_thumb_path = os.path.join(TEMP_DIR, thumb_name)

        # Baixar, gerar thumbnail e fazer upload
        run_command(["rclone", "copyto", f"{VIDEO_FOLDER}/{video_filename}", local_video_path])
        run_command(["ffmpeg", "-nostdin", "-i", local_video_path, "-ss", "00:00:01.00", "-vframes", "1", "-q:v", "2", local_thumb_path])
        run_command(["rclone", "copyto", local_thumb_path, f"{THUMB_FOLDER}/{thumb_name}"])

        # Limpeza
        os.remove(local_video_path)
        os.remove(local_thumb_path)
        print(f"-> Thumbnail para '{video_filename}' gerada com sucesso.\n")

    except Exception as e:
        print(f"ERRO CRÍTICO ao processar '{video_filename}': {e}", file=sys.stderr)

print("\nGeração de thumbnails concluída!")