# processors/video_processor.py

import logging
import subprocess
import shlex

def apply_watermark_to_video(video_path, output_path, config):
    """Aplica uma marca de água de texto a um vídeo usando FFmpeg."""
    try:
        # --- CORREÇÕES ---
        # A opacidade no FFmpeg é um valor entre 0.0 (transparente) e 1.0 (opaco)
        ffmpeg_alpha = config.WATERMARK_OPACITY / 255.0

        margin_expr_x = f"w*{config.MARGIN_RATIO}"
        margin_expr_y = f"h*{config.MARGIN_RATIO}"
        
        if config.POSITION_HORIZONTAL == 'center': pos_x = "(w-text_w)/2"
        elif config.POSITION_HORIZONTAL == 'left': pos_x = margin_expr_x
        else: pos_x = f"w-text_w-{margin_expr_x}" # 'right'

        if config.POSITION_VERTICAL == 'middle': pos_y = "(h-text_h)/2"
        elif config.POSITION_VERTICAL == 'top': pos_y = margin_expr_y
        else: pos_y = f"h-text_h-{margin_expr_y}" # 'bottom'

        # Converte a cor RGB para uma string hexadecimal que o FFmpeg entende
        font_color_hex = f"#{config.WATERMARK_COLOR_RGB[0]:02x}{config.WATERMARK_COLOR_RGB[1]:02x}{config.WATERMARK_COLOR_RGB[2]:02x}"

        # Comando FFmpeg completo e corrigido
        command = [
            "ffmpeg",
            "-i", video_path,
            "-vf", (
                f"drawtext="
                f"fontfile='{config.WATERMARK_FONT_PATH}':"
                f"text='{config.WATERMARK_TEXT}':"
                f"fontsize=h*{config.FONT_SIZE_RATIO}:"
                f"fontcolor={font_color_hex}@{ffmpeg_alpha}:"
                f"x={pos_x}:"
                f"y={pos_y}"
            ),
            "-codec:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-codec:a", "copy",
            "-y", # Sobrescreve o ficheiro de saída se já existir
            output_path
        ]
        
        logging.info(f"A executar FFmpeg: {' '.join(shlex.quote(c) for c in command)}")
        
        # Executa o comando
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        logging.info(f"Marca de água aplicada com sucesso a '{video_path}'")
        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg falhou ao processar o vídeo '{video_path}'.")
        logging.error(f"FFmpeg stderr: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Falha ao processar o vídeo '{video_path}'. Motivo: {e}")
        return False
