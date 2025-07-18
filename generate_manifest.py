import subprocess
import sys
import json

# --- Constantes ---
R2_REMOTE_PATH = "R2:bia-portfolio-assets"
MANIFEST_FILE = "r2_manifest.json"

# --- CORREÇÃO --- A lista de regras de exclusão foi inicializada.
# Adicione aqui os padrões a serem ignorados pelo rclone.
# Cada regra será adicionada ao comando com a flag --exclude.
EXCLUDE_RULES = [
    "Thumbnails/**",  # Ignora a pasta Thumbnails e todo o seu conteúdo
    "*.log",          # Ignora ficheiros de log
]

def generate_manifest():
    """
    Executa o comando 'rclone lsjson' para obter uma lista detalhada dos
    ficheiros no R2 e guarda-a num ficheiro JSON.
    """
    print(f"--- Gerando manifesto de ficheiros de '{R2_REMOTE_PATH}' ---")

    # --- CORREÇÃO --- O comando foi construído corretamente como uma lista.
    # A construção dinâmica permite adicionar as regras de exclusão de forma segura.
    command = ["rclone", "lsjson", R2_REMOTE_PATH]
    
    # Adiciona as regras de exclusão ao comando
    for rule in EXCLUDE_RULES:
        command.extend(["--exclude", rule])

    try:
        # Executa o comando e captura a saída
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        
        # Analisa a saída JSON
        files = json.loads(result.stdout)
        
        # Guarda a lista de ficheiros no manifesto
        with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
            json.dump(files, f, indent=2)
            
        print(f"Manifesto gerado com sucesso com {len(files)} ficheiros.")

    except FileNotFoundError:
        print("ERRO: O comando 'rclone' não foi encontrado. Verifique se está instalado e no PATH do sistema.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        # Trata o caso específico de o bucket estar vazio ou não existir
        if "directory not found" in e.stderr.lower():
            print("AVISO: Bucket de destino parece estar vazio. A criar um manifesto vazio.")
            # --- CORREÇÃO --- Cria um manifesto com uma lista JSON vazia.
            with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
        else:
            print(f"ERRO ao executar o rclone: {e}\nStderr: {e.stderr}")
            sys.exit(1)
    except json.JSONDecodeError:
        print("ERRO: Falha ao analisar a saída JSON do rclone. A saída pode estar vazia ou malformada.")
        sys.exit(1)

if __name__ == "__main__":
    generate_manifest()
