
import logging
import subprocess
from pathlib import Path

def sync_rclone(source: str, destination: str, operation_name: str, *args) -> bool:
  command = ["rclone", "copy"]
  if source: command.append(source)
  if destination: command.append(destination)
  command.extend(args)
  command.extend(["--progress", "-v", "--checksum"])
  logging.info(f"Iniciando operação rclone: {operation_name}")
  try:
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", timeout=900)
    logging.info(f"Operação rclone \'{operation_name}\' concluída com sucesso.")
    if result.stdout:
        logging.info(f"Detalhes da operação:\n{result.stdout}")
    return True
  except subprocess.CalledProcessError as e:
    logging.error(f"Falha na operação rclone \'{operation_name}\' (código de saída {e.returncode}): {e.stderr}")
    return False
  except Exception as e:
    logging.error(f"Erro inesperado na operação rclone \'{operation_name}\' (copy): {e}")
    return False

def delete_rclone(source: str, destination: str, operation_name: str, *args) -> bool:
  command = ["rclone", "delete"]
  if destination: command.append(destination)
  command.extend(args)
  command.extend(["--progress", "-v", "--filter-from", source])
  logging.info(f"Iniciando operação rclone: {operation_name}")
  try:
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", timeout=900)
    logging.info(f"Operação rclone \'{operation_name}\' concluída com sucesso.")
    if result.stdout:
        logging.info(f"Detalhes da operação:\n{result.stdout}")
    return True
  except subprocess.CalledProcessError as e:
    logging.error(f"Falha na operação rclone \'{operation_name}\' (código de saída {e.returncode}): {e.stderr}")
    return False
  except Exception as e:
    logging.error(f"Erro inesperado na operação rclone \'{operation_name}\' (delete): {e}")
    return False