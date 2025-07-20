import logging
from PIL import Image, ImageDraw, ImageFont, ExifTags, UnidentifiedImageError
from pathlib import Path
import config

def correct_image_orientation(img: Image.Image) -> Image.Image:
  try:
    exif = img.getexif()
    orientation_tag = 274
    if orientation_tag in exif:
      orientation = exif[orientation_tag]
    if orientation == 3:
      img = img.rotate(180, expand=True)
    elif orientation == 6:
      img = img.rotate(270, expand=True)
    elif orientation == 8:
      img = img.rotate(90, expand=True)
  except (AttributeError, KeyError, IndexError):
    pass
  return img

def apply_watermark(image: Image.Image) -> Image.Image:
  if image.mode != 'RGBA':
    image = image.convert('RGBA')

  txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
  draw = ImageDraw.Draw(txt_layer)
  font_size = int(image.width * config.IMG_WATERMARK_FONT_RATIO)
  try:
    font = ImageFont.truetype(config.WATERMARK_FONT_PATH, font_size)
  except IOError:
    logging.warning(f"Fonte {config.WATERMARK_FONT_PATH} não encontrada. Usando fonte padrão.")
    font = ImageFont.load_default()
  left, top, right, bottom = draw.textbbox((0, 0), config.WATERMARK_TEXT, font=font)
  text_width = right - left
  text_height = bottom - top
  margin = int(image.width * config.MARGIN_RATIO)
  x = image.width - text_width - margin
  y = image.height - text_height - margin
  shadow_offset = int(font_size * 0.05)
  shadow_x = x + shadow_offset
  shadow_y = y + shadow_offset
  shadow_color = (0, 0, 0, int(config.WATERMARK_OPACITY * 0.8))
  draw.text((shadow_x, shadow_y), config.WATERMARK_TEXT, font=font, fill=shadow_color)
  fill_color = (*config.WATERMARK_COLOR_RGB, config.WATERMARK_OPACITY)
  draw.text((x, y), config.WATERMARK_TEXT, font=font, fill=fill_color)
  return Image.alpha_composite(image, txt_layer)

def process_image(file_path: Path, output_path: Path) -> bool:
  try:
    with Image.open(file_path) as img:
      corrected_img = correct_image_orientation(img)
      watermarked_img = apply_watermark(corrected_img)
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