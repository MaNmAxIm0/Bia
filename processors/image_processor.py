# processors/image_processor.py

import logging
from PIL import Image, ImageDraw, ImageFont, ExifTags, UnidentifiedImageError
from pathlib import Path
import config

def correct_image_orientation(img: Image.Image) -> Image.Image:
    """Lê a tag de orientação EXIF de uma imagem e aplica a rotação necessária."""
    try:
        exif = img.getexif()
        orientation_tag = 274  # Tag para Orientação

        if orientation_tag in exif:
            orientation = exif[orientation_tag]
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # A imagem não tem dados EXIF ou a tag de orientação
        pass
    return img

def apply_watermark(image: Image.Image) -> Image.Image:
    """Aplica uma marca de água com sombra para melhor legibilidade."""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)
    
    # Calcular tamanho da fonte com base na LARGURA da imagem
    font_size = int(image.width * config.IMG_WATERMARK_FONT_RATIO)
    try:
        font = ImageFont.truetype(config.WATERMARK_FONT_PATH, font_size)
    except IOError:
        logging.warning(f"Fonte {config.WATERMARK_FONT_PATH} não encontrada. Usando fonte padrão.")
        font = ImageFont.load_default()

    # Obter o tamanho do texto para posicionamento preciso
    left, top, right, bottom = draw.textbbox((0, 0), config.WATERMARK_TEXT, font=font)
    text_width = right - left
    text_height = bottom - top
    
    # Calcular posição (canto inferior direito com margem)
    margin = int(image.width * config.MARGIN_RATIO)
    x = image.width - text_width - margin
    y = image.height - text_height - margin
    
    # --- ATUALIZADO: Adicionar sombra ---
    # 1. Definir a posição e cor da sombra
    shadow_offset = int(font_size * 0.05) # Deslocamento de 5% do tamanho da fonte
    shadow_x = x + shadow_offset
    shadow_y = y + shadow_offset
    # Sombra preta com uma opacidade ligeiramente inferior à do texto principal
    shadow_color = (0, 0, 0, int(config.WATERMARK_OPACITY * 0.8)) 

    # 2. Desenhar a sombra
    draw.text((shadow_x, shadow_y), config.WATERMARK_TEXT, font=font, fill=shadow_color)

    # 3. Desenhar o texto principal por cima da sombra
    fill_color = (*config.WATERMARK_COLOR_RGB, config.WATERMARK_OPACITY)
    draw.text((x, y), config.WATERMARK_TEXT, font=font, fill=fill_color)
    
    return Image.alpha_composite(image, txt_layer)

def process_image(file_path: Path, output_path: Path) -> bool:
    """Orquestra o processamento completo de uma imagem."""
    try:
        with Image.open(file_path) as img:
            # 1. Corrigir orientação
            corrected_img = correct_image_orientation(img)
            
            # 2. Aplicar marca de água
            watermarked_img = apply_watermark(corrected_img)
            
            # 3. Salvar como JPEG
            final_img = watermarked_img.convert('RGB')
            final_img.save(
                output_path,
                'JPEG',
                quality=config.IMAGE_QUALITY,
                optimize=True,
                progressive=True
            )
        return True
    except UnidentifiedImageError:
        logging.error(f"FALHA DE FORMATO: Pillow não conseguiu identificar '{file_path.name}'.")
        return False
    except Exception as e:
        logging.error(f"FALHA INESPERADA ao processar imagem '{file_path.name}': {e}", exc_info=True)
        return False
