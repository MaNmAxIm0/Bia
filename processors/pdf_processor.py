import subprocess
import shutil

def process_pdf(input_path, output_path):
  shutil.copy2(input_path, output_path)