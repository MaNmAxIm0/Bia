import logging
import subprocess
from pathlib import Path

def sync_rclone(source: str, destination: str, operation_name: str, *args) -> bool:
  command = ["rclone", "sync"]
  if source: command.append(source)
  if destination: command.append(destination)
  command.extend(args)
  command.extend(["--progress", "-v"])
  logging.info(f"Iniciando operação rclone: {operation_name}")
  try:
    subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", timeout=900)
    logging.info(f"Operação rclone \'{operation_name}\' concluída com sucesso.")
    return True
  except subprocess.CalledProcessError as e:
    logging.error(f"Falha na operação rclone \'{operation_name}\': {e.stderr}")
    return False
  except Exception as e:
    logging.error(f"Erro inesperado na operação rclone \'{operation_name}\': {e}")
    return False

