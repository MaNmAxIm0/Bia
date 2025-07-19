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
        files_data = json.loads(input_json_str)
        lisbon_tz = pytz.timezone('Europe/Lisbon')
        
        manifest_lines = []
        for item in files_data:
            if item.get('IsDir', False):
                continue
            
            mod_time_str = item.get('ModTime')
            path = item.get('Path')
            
            if mod_time_str and path:
                # --- CORREÇÃO: Truncar a data para microssegundos ---
                # O rclone pode devolver até 9 dígitos (nanossegundos).
                # O datetime do Python só aceita 6 (microssegundos).
                # Esta linha garante que a data é sempre compatível.
                if '.' in mod_time_str:
                    main_part, fractional_part = mod_time_str.split('.', 1)
                    # O 'Z' ou fuso horário vem depois da parte fracionária
                    if 'Z' in fractional_part:
                        fraction, timezone = fractional_part.split('Z', 1)
                        fraction = fraction[:6] # Limita a 6 dígitos
                        mod_time_str = f"{main_part}.{fraction}Z"
                    elif '+' in fractional_part:
                        fraction, timezone = fractional_part.split('+', 1)
                        fraction = fraction[:6]
                        mod_time_str = f"{main_part}.{fraction}+{timezone}"
                    elif '-' in fractional_part:
                        fraction, timezone = fractional_part.split('-', 1)
                        fraction = fraction[:6]
                        mod_time_str = f"{main_part}.{fraction}-{timezone}"

                # Converte a data UTC do rclone para um objeto datetime
                mod_time_utc = datetime.fromisoformat(mod_time_str.replace('Z', '+00:00'))
                
                # Converte para o fuso horário de Lisboa
                mod_time_lisbon = mod_time_utc.astimezone(lisbon_tz)
                
                # Formata a data e hora no formato desejado
                formatted_time = mod_time_lisbon.strftime('%Y-%m-%d %H:%M:%S')
                
                manifest_lines.append(f"{formatted_time} {path}")
        
        manifest_lines.sort(key=lambda line: line.split(' ', 1)[1])
        
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
    input_json = sys.stdin.read()
    output_file = "r2_file_manifest.txt"
    format_rclone_manifest(input_json, output_file)
