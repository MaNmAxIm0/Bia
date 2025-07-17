import subprocess
import json
import sys

# --- Variáveis de configuração (adicionei como exemplo) ---
# Defina o seu remote e o caminho no R2
R2_REMOTE_PATH = 'R2:bia-portfolio-assets' 
# Ficheiro onde o manifesto será guardado
MANIFEST_FILE = 'r2_manifest.json' # Alterado para r2_manifest.json para consistência
# Regras de exclusão para o rclone
EXCLUDE_RULES = [
    '--exclude', '.DS_Store',
    '--exclude', 'desktop.ini',
    '--exclude', 'Thumbs.db'
]
# --- Fim da configuração ---


def generate_manifest():
    """
    Executa o comando 'rclone lsjson' para obter uma lista detalhada dos
    ficheiros no R2 e guarda-a num ficheiro JSON, aplicando regras de exclusão.
    """
    print(f"--- Gerando manifesto de ficheiros de '{R2_REMOTE_PATH}' ---")

    # Define o comando base para o rclone
    base_command = ['rclone', 'lsjson', R2_REMOTE_PATH]

    # ## CORREÇÃO ##
    # A forma correta é concatenar a lista do comando base com a lista
    # de regras de exclusão. O operador '+' entre duas listas serve para juntá-las.
    command = base_command + EXCLUDE_RULES

    print(f"Comando a ser executado: {' '.join(command)}") # Opcional: para depuração

    try:
        # Executa o comando e captura a saída
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        
        # Analisa a saída JSON
        files = json.loads(result.stdout)
        
        # Guarda o manifesto no ficheiro
        with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
            json.dump(files, f, indent=2)
            
        print(f"\nManifesto gerado com sucesso com {len(files)} ficheiros.")
        print(f"Salvo em '{MANIFEST_FILE}'.")

    except FileNotFoundError:
        print("\nERRO: O comando 'rclone' não foi encontrado. Verifique se está instalado e no PATH do sistema.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nERRO ao executar o rclone: {e}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("\nERRO: Falha ao analisar a saída JSON do rclone. A saída pode estar vazia ou mal formatada.")
        print(f"Saída recebida do rclone: {result.stdout}")
        sys.exit(1)

if __name__ == "__main__":
    generate_manifest()

