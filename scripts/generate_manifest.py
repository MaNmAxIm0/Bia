import subprocess
import sys
import json

# --- Constantes ---
R2_REMOTE_PATH = "R2:bia-portfolio-assets"
MANIFEST_FILE = "r2_manifest.json"
# Regras para excluir a pasta de thumbnails e ficheiros de sistema do manifesto
EXCLUDE_RULES = ['--exclude', '/Thumbnails/**', '--exclude', 'desktop.ini']

def generate_manifest():
    """
    Executa o comando 'rclone lsjson' para obter uma lista detalhada dos
    ficheiros no R2 e guarda-a num ficheiro JSON.
    """
    print(f"--- Gerando manifesto de ficheiros de '{R2_REMOTE_PATH}' ---")

    # ## CORREÇÃO FINAL ##
    # A linha anterior 'command = + EXCLUDE_RULES' estava sintaticamente incorreta.
    # A forma correta é construir a lista de comandos base e depois concatenar
    # a lista de regras de exclusão usando o operador '+'.
    command = + EXCLUDE_RULES

    try:
        # Executa o comando e captura a saída
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Analisa a saída JSON
        files = json.loads(result.stdout)
        
        # Guarda o manifesto no ficheiro
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(files, f, indent=2)
            
        print(f"Manifesto gerado com sucesso com {len(files)} ficheiros.")
        print(f"Salvo em '{MANIFEST_FILE}'.")

    except FileNotFoundError:
        print("ERRO: O comando 'rclone' não foi encontrado. Verifique se está instalado e no PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao executar o rclone: {e}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("ERRO: Falha ao analisar a saída JSON do rclone.")
        sys.exit(1)

if __name__ == "__main__":
    generate_manifest()