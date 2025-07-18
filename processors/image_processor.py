# processors/image_processor.py

import logging
from PIL import Image, ImageDraw, ImageFont

def apply_watermark_to_image(image_path, output_path, config):
    """Aplica uma marca de água de texto a uma imagem."""
    try:
        with Image.open(image_path).convert('RGBA') as base_image:
            txt_layer = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
            
            font_size = int(base_image.height * config.FONT_SIZE_RATIO)
            try:
                font = ImageFont.truetype(config.WATERMARK_FONT_PATH, font_size)
            except IOError:
                logging.warning(f"Fonte '{config.WATERMARK_FONT_PATH}' não encontrada. A usar fonte padrão.")
                font = ImageFont.load_default()

            draw = ImageDraw.Draw(txt_layer)
            
            watermark_color_with_opacity = (*config.WATERMARK_COLOR_RGB, config.WATERMARK_OPACITY)
            
            text_bbox = draw.textbbox((0, 0), config.WATERMARK_TEXT, font=font)
            text_width = text_bbox[1] - text_bbox
            text_height = text_bbox[2] - text_bbox[3]
            
            margin_x = int(base_image.width * config.MARGIN_RATIO)
            margin_y = int(base_image.height * config.MARGIN_RATIO)

            if config.POSITION_HORIZONTAL == 'center': x = (base_image.width - text_width) / 2
            elif config.POSITION_HORIZONTAL == 'left': x = margin_x
            else: x = base_image.width - text_width - margin_x
            
            if config.POSITION_VERTICAL == 'middle': y = (base_image.height - text_height) / 2
            elif config.POSITION_VERTICAL == 'top': y = margin_y
            else: y = base_image.height - text_height - margin_y

            draw.text((x, y), config.WATERMARK_TEXT, font=font, fill=watermark_color_with_opacity)
            
            watermarked_image = Image.alpha_composite(base_image, txt_layer)
            
            watermarked_image.convert('RGB').save(output_path, 'JPEG', quality=95)
            logging.info(f"Marca de água aplicada com sucesso a '{image_path}'")
            return True

    except Exception as e:
        logging.error(f"Falha ao processar a imagem '{image_path}'. Motivo: {e}")
        return False