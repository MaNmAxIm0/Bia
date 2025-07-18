# processors/image_processor.py

import logging
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import os

def apply_watermark_to_image(image_path: str, output_path: str, config) -> bool:
    """
    Aplica uma marca de água de texto a uma imagem, com tratamento de erros robusto.
    Retorna True em caso de sucesso e False em caso de falha.
    """
    try:
        # --- AÇÃO IMEDIATA 3: Tratamento de Erros Granular ---
        # Abre a imagem dentro de um contexto 'with' para garantir que é fechada.
        with Image.open(image_path) as base_image:
            
            # Converte para RGBA para poder compor com uma camada com transparência.
            # Fazemos isto depois de abrir para garantir que o ficheiro é uma imagem válida primeiro.
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')

            # Cria uma camada transparente para desenhar o texto da marca de água.
            txt_layer = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
            
            # Define o tamanho da fonte com base na altura da imagem.
            font_size = int(base_image.height * config.FONT_SIZE_RATIO)
            try:
                font = ImageFont.truetype(config.WATERMARK_FONT_PATH, font_size)
            except IOError:
                logging.warning(f"Fonte '{config.WATERMARK_FONT_PATH}' não encontrada. A usar fonte padrão.")
                font = ImageFont.load_default()

            draw = ImageDraw.Draw(txt_layer)
            
            # Define a cor da marca de água com a opacidade configurada.
            watermark_color_with_opacity = (*config.WATERMARK_COLOR_RGB, config.WATERMARK_OPACITY)
            
            # --- AÇÃO IMEDIATA 4: Correção da Lógica de Posição (Previne o TypeError) ---
            # Desestrutura a bounding box para obter as coordenadas corretas.
            # textbbox retorna (left, top, right, bottom).
            left, top, right, bottom = draw.textbbox((0, 0), config.WATERMARK_TEXT, font=font)
            text_width = right - left
            text_height = bottom - top
            
            # Calcula as margens.
            margin_x = int(base_image.width * config.MARGIN_RATIO)
            margin_y = int(base_image.height * config.MARGIN_RATIO)

            # Calcula a posição (x, y) com base nas configurações.
            if config.POSITION_HORIZONTAL == 'center':
                x = (base_image.width - text_width) / 2
            elif config.POSITION_HORIZONTAL == 'left':
                x = margin_x
            else: # 'right'
                x = base_image.width - text_width - margin_x
            
            if config.POSITION_VERTICAL == 'middle':
                y = (base_image.height - text_height) / 2
            elif config.POSITION_VERTICAL == 'top':
                y = margin_y
            else: # 'bottom'
                y = base_image.height - text_height - margin_y

            # Desenha o texto na camada transparente.
            draw.text((x, y), config.WATERMARK_TEXT, font=font, fill=watermark_color_with_opacity)
            
            # Compõe a imagem original com a camada da marca de água.
            watermarked_image = Image.alpha_composite(base_image, txt_layer)
            
            # Converte a imagem final para RGB antes de a guardar como JPEG.
            # Usa a qualidade definida no config.py (ou um valor padrão).
            jpeg_quality = getattr(config, 'IMAGE_QUALITY', 90)
            watermarked_image.convert('RGB').save(output_path, 'JPEG', quality=jpeg_quality, optimize=True)
            
            # logging.info(f"Marca de água aplicada com sucesso a '{os.path.basename(image_path)}'")
            return True

    # --- AÇÃO IMEDIATA 3 (Continuação): Tratamento de Erros Específico ---
    except UnidentifiedImageError:
        logging.error(f"FALHA: Pillow não conseguiu identificar o formato de '{os.path.basename(image_path)}'. O ficheiro pode estar corrompido ou não ser uma imagem suportada.")
        return False
    except FileNotFoundError:
        logging.error(f"FALHA: O ficheiro não foi encontrado no caminho especificado: '{image_path}'")
        return False
    except Exception as e:
        # Captura todas as outras exceções para evitar que o script pare.
        logging.error(f"FALHA: Ocorreu um erro inesperado ao processar '{os.path.basename(image_path)}': {e}", exc_info=True)
        return False
