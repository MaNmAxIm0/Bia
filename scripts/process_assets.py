import subprocess
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# --- Constantes de Configuração ---
DRIVE_DIR = Path("./portfolio_source") 
OUTPUT_DIR = Path("./processed_assets")
FAILED_DIR = Path("./failed_images") 
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_FILE = Path("./scripts/Montserrat-Medium.ttf") 

# Configurações da Marca de Água de Texto
WATERMARK_OPACITY = 0.5 # Ajuste conforme necessário (0.0 a 1.0)
FONT_SIZE_RATIO = 0.05

# --- Funções Auxiliares ---
def setup_directories():
    """Cria os diretórios de saída e falhas se não existirem."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)

def load_manifest():
    """
    Carrega o manifesto de ficheiros existentes no R2.
    Retorna um dicionário com o nome do ficheiro como chave e o hash como valor.
    """
    # CORRIGIDO: Usar o nome de ficheiro correto
    manifest_path = Path("./r2_file_manifest.txt") 
    manifest = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                # Assumindo que o r2_file_manifest.txt é um JSON válido
                data = json.load(f)
                for item in data:
                    # Usar o 'Key' que representa o caminho completo no R2
                    manifest[item['Key']] = item['Hash'] # Ou outro identificador único
            print(f"Manifesto carregado com {len(manifest)} entradas.")
        except json.JSONDecodeError:
            print(f"AVISO: O ficheiro de manifesto '{manifest_path}' não é um JSON válido. Será ignorado.")
        except Exception as e:
            print(f"AVISO: Erro ao carregar o manifesto '{manifest_path}': {e}. Será ignorado.")
    else:
        print(f"AVISO: Ficheiro de manifesto '{manifest_path}' não encontrado. A processar todos os ficheiros.")
    return manifest

def calculate_file_hash(file_path: Path):
    """Calcula um hash simples do ficheiro para comparação."""
    # Para simplificar, vamos usar o tamanho do ficheiro e a data de modificação
    # Para uma verificação mais robusta, pode usar hashlib.md5
    return f"{file_path.stat().st_size}-{file_path.stat().st_mtime_ns}"

def add_watermark(image_path: Path, output_path: Path):
    """Adiciona uma marca de água de texto a uma imagem."""
    try:
        img = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(img)

        img_width, img_height = img.size
        
        # Tenta carregar a fonte, se falhar, usa a fonte padrão
        try:
            font_size = int(img_height * FONT_SIZE_RATIO)
            font = ImageFont.truetype(str(FONT_FILE), font_size)
        except IOError:
            print(f"AVISO: Fonte '{FONT_FILE}' não encontrada. Usando fonte padrão.")
            font = ImageFont.load_default()
            font_size = int(img_height * FONT_SIZE_RATIO) # Ajusta o tamanho para a fonte padrão

        # Medir o tamanho do texto para posicionamento
        # getbbox() é mais robusto que getsize() para versões recentes do Pillow
        bbox = draw.textbbox((0,0), WATERMARK_TEXT, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Posição central inferior
        x = (img_width - text_width) / 2
        y = img_height - text_height - (img_height * 0.02) # Pequena margem inferior

        # Cor da marca de água (branco com opacidade)
        # O valor 255 * WATERMARK_OPACITY é o canal alfa (transparência)
        fill_color = (255, 255, 255, int(255 * WATERMARK_OPACITY))

        draw.text((x, y), WATERMARK_TEXT, font=font, fill=fill_color)

        # Salvar a imagem processada
        img.save(output_path)
        return True
    except Exception as e:
        print(f"Erro ao adicionar marca de água a {image_path}: {e}")
        return False

def process_single_file(file_path: Path, r2_manifest: dict):
    """Processa um único ficheiro: aplica marca de água e verifica se precisa de atualização."""
    relative_path = file_path.relative_to(DRIVE_DIR)
    output_path = OUTPUT_DIR / relative_path

    # CORRIGIDO: Criar o diretório pai antes de salvar o ficheiro
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Verifica se o ficheiro já existe no R2 e se é o mesmo
    r2_key = str(relative_path).replace('\\', '/') # Chave no R2 usa barras normais
    current_file_hash = calculate_file_hash(file_path)

    if r2_key in r2_manifest and r2_manifest[r2_key] == current_file_hash:
        # print(f"DEBUG: Ficheiro {r2_key} inalterado. Ignorando.")
        return {'status': 'skipped', 'path': file_path}

    # Processa apenas imagens por enquanto
    if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
        if add_watermark(file_path, output_path):
            return {'status': 'success', 'path': file_path}
        else:
            # Mover para a pasta de falhas se a marca de água falhar
            failed_path = FAILED_DIR / relative_path.name
            file_path.rename(failed_path) # Move o original para falhas
            return {'status': 'failed', 'path': file_path, 'error': 'Watermark failed'}
    else:
        # Para outros tipos de ficheiro, apenas copia
        try:
            # Certifica-se de que o diretório de destino existe para ficheiros não-imagem
            output_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['cp', str(file_path), str(output_path)], check=True)
            return {'status': 'success', 'path': file_path}
        except Exception as e:
            print(f"Erro ao copiar ficheiro {file_path}: {e}")
            failed_path = FAILED_DIR / relative_path.name
            file_path.rename(failed_path) # Move o original para falhas
            return {'status': 'failed', 'path': file_path, 'error': f'Copy failed: {e}'}

def main():
    """Função principal que orquestra o processamento."""
    setup_directories()
    
    # CORRIGIDO: Carregar o manifesto uma única vez no início
    r2_manifest = load_manifest()
    
    # Encontra todos os ficheiros no diretório de origem, incluindo subpastas
    files_to_process = [p for p in DRIVE_DIR.rglob('*') if p.is_file()]

    if not files_to_process:
        print("Nenhum ficheiro encontrado para processar.")
        return

    print(f"Encontrados {len(files_to_process)} ficheiros para processar.")
    
    success_log = []
    failure_log = []
    skipped_count = 0

    # Usar ThreadPoolExecutor para processamento paralelo
    with ThreadPoolExecutor() as executor:
        # Mapeia cada ficheiro para a função de processamento
        # Passa o r2_manifest para cada chamada de process_single_file
        futures = {executor.submit(process_single_file, file_path, r2_manifest): file_path for file_path in files_to_process}
        
        # Barra de progresso para acompanhar o processamento
        progress_bar = tqdm(as_completed(futures), total=len(files_to_process), desc="Processando Ativos", unit="file")

        for future in progress_bar:
            result = future.result()
            if result['status'] == 'success':
                success_log.append(str(result['path']))
            elif result['status'] == 'failed':
                failure_log.append(f"{result['path']} - {result['error']}")
            elif result['status'] == 'skipped':
                skipped_count += 1
            
            progress_bar.set_postfix(success=len(success_log), failed=len(failure_log), skipped=skipped_count)

    print(f"\nProcessamento concluído.")
    print(f"Total de ficheiros processados com sucesso: {len(success_log)}")
    print(f"Total de ficheiros ignorados (inalterados): {skipped_count}")
    print(f"Total de falhas: {len(failure_log)}")

    # CORRIGIDO: Salvar logs na raiz do projeto para serem apanhados pelo upload-artifact
    with open("./success.log", "w", encoding='utf-8') as f:
        f.write("\n".join(success_log))
    with open("./failure.log", "w", encoding='utf-8') as f:
        f.write("\n".join(failure_log))
    
    if failure_log:
        print(f"Verifique o ficheiro 'failure.log' para detalhes das falhas.")
    else:
        print("Nenhuma falha registada.")

if __name__ == "__main__":
    main()
