import json
import sys
from datetime import datetime
import pytz

def format_rclone_manifest(input_json_str: str, output_file_path: str):
    """
    Lê o output JSON do 'rclone lsjson', formata-o para 'ModTime Path'
    e guarda-o num ficheiro de texto.
    """
    try:
        # Lê a string JSON de entrada
        files_data = json.loads(input_json_str)
        
        # Define o fuso horário de Lisboa para a conversão
        lisbon_tz = pytz.timezone('Europe/Lisbon')
        
        manifest_lines = []
        for item in files_data:
            # Ignora as entradas que são diretórios
            if item.get('IsDir', False):
                continue
            
            # Extrai a data de modificação e o caminho
            mod_time_str = item.get('ModTime')
            path = item.get('Path')
            
            if mod_time_str and path:
                # Converte a data UTC do rclone para um objeto datetime
                mod_time_utc = datetime.fromisoformat(mod_time_str.replace('Z', '+00:00'))
                # Converte para o fuso horário de Lisboa
                mod_time_lisbon = mod_time_utc.astimezone(lisbon_tz)
                # Formata a data e hora no formato desejado
                formatted_time = mod_time_lisbon.strftime('%Y-%m-%d %H:%M:%S')
                
                manifest_lines.append(f"{formatted_time} {path}")
        
        # Ordena as linhas alfabeticamente pelo caminho do ficheiro
        manifest_lines.sort(key=lambda line: line.split(' ', 1)[1])
        
        # Escreve o resultado no ficheiro de saída
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(manifest_lines))
            
        print(f"Manifesto '{output_file_path}' formatado e guardado com sucesso com {len(manifest_lines)} ficheiros.")

    except json.JSONDecodeError:
        print("Erro: A entrada não é um JSON válido.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    # Lê o JSON a partir da entrada padrão (stdin)
    input_json = sys.stdin.read()
    output_file = "r2_file_manifest.txt"
    format_rclone_manifest(input_json, output_file)
