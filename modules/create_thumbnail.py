import os
import random
from PIL import Image, ImageDraw, ImageFont
from logger import ColoredLogger

logger = ColoredLogger("THUMBNAIL")


def load_model_config(config):
    """
    Load the model-specific text configuration file.
    Expects a file named {model}_config.txt inside the templates/{model} folder.
    Lines starting with '#' or '-' are ignored.
    Each nonempty line must be of the format:
    
        KEY=VALUE

    Numeric values are automatically converted.
    """
    model = os.path.basename(config["TEMPLATES_DIR"])
    config_path = os.path.join(config["TEMPLATES_DIR"], f"{model}_config.txt")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Model config file not found: {config_path}")
    text_config = {}
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Convert to int or float if possible; otherwise, leave as string.
                try:
                    text_config[key] = int(value)
                except ValueError:
                    try:
                        text_config[key] = float(value)
                    except ValueError:
                        text_config[key] = value
    return text_config


def get_text_size(text, font, letter_spacing):
    """Return the (width, height) of the text using the given font and letter spacing."""
    if letter_spacing is None:
        letter_spacing = 0
    if letter_spacing == 0:
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height
    else:
        total_width = 0
        max_height = 0
        for char in text:
            bbox = font.getbbox(char)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            total_width += w
            max_height = max(max_height, h)
        if len(text) > 1:
            total_width += letter_spacing * (len(text) - 1)
        return total_width, max_height


def _draw_text_with_spacing(draw, position, text, font, fill, letter_spacing):
    """Draws text letter-by-letter applying letter spacing."""
    x, y = position
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        bbox = font.getbbox(char)
        w = bbox[2] - bbox[0]
        x += w + letter_spacing


def draw_text_with_border_and_spacing(draw, position, text, font, fill, border_color, border_width, letter_spacing):
    """Draw text with a border and custom letter spacing."""
    x, y = position
    if border_width > 0:
        for dx in range(-border_width, border_width + 1):
            for dy in range(-border_width, border_width + 1):
                if dx == 0 and dy == 0:
                    continue
                _draw_text_with_spacing(draw, (x + dx, y + dy), text, font, border_color, letter_spacing)
    _draw_text_with_spacing(draw, (x, y), text, font, fill, letter_spacing)


def draw_multiline_text_with_border_and_spacing(draw, lines, start_position, font, fill,
                                                border_color, border_width, letter_spacing,
                                                line_spacing, box_width=None):
    """
    Draws multiple lines of text. If box_width is provided, each line is centered horizontally
    within that box.
    """
    x0, y0 = start_position
    for line in lines:
        text_width, text_height = get_text_size(line, font, letter_spacing)
        if box_width is not None:
            x = x0 + (box_width - text_width) // 2
        else:
            x = x0
        draw_text_with_border_and_spacing(draw, (x, y0), line, font, fill, border_color, border_width, letter_spacing)
        y0 += text_height + line_spacing


def process_thumbnail(config):
    logger.module_start()
    try:
        run_individually = config.get("RUN_INDIVIDUALLY", True)
        IMAGES_DIR = config.get("IMAGES_DIR")
        if run_individually:
            image_files = [f for f in os.listdir(IMAGES_DIR)
                           if f.lower().endswith(("png", "jpg", "jpeg"))]
            if not image_files:
                logger.error("No images found in directory")
                raise FileNotFoundError("No images available")
            image_path = os.path.join(IMAGES_DIR, random.choice(image_files))
            config["SELECTED_IMAGE"] = image_path
        image_path = config.get("SELECTED_IMAGE")
        if not image_path or not os.path.exists(image_path):
            logger.error("No image available for thumbnail")
            raise FileNotFoundError("Missing source image")
        
        # Read all non-commented lines from the thumbnail text file.
        text_file = config["THUMBNAIL_TEXT_FILE"]
        if not os.path.exists(text_file):
            logger.error(f"Thumbnail text file missing: {text_file}")
            raise FileNotFoundError(f"Missing text file: {text_file}")
        with open(text_file, "r", encoding="utf-8") as f:
            title_lines = [line.strip() for line in f if line.strip() and not line.startswith("-")]
        if not title_lines:
            logger.error("No thumbnail texts available")
            raise ValueError("Empty thumbnail text file")
        
        # Duration text is built from video length.
        video_length = config["VIDEO_LENGTH_MINUTES"]
        duration_text = f"{video_length} Minutes"
        
        # Load the model-specific text config parameters.
        text_config = load_model_config(config)
        
        # === TITLE (Multiline) Configurations ===
        title_font_size         = text_config.get("TITLE_FONT_SIZE", 100)
        title_font_path         = text_config.get("TITLE_FONT_PATH", "arialbd.ttf")
        title_color             = text_config.get("TITLE_COLOR", "white")
        title_border_color      = text_config.get("TITLE_BORDER_COLOR", "black")
        title_border_width      = text_config.get("TITLE_BORDER_WIDTH", 4)
        title_x                 = text_config.get("TITLE_X_POSITION", 30)
        title_y                 = text_config.get("TITLE_Y_POSITION", 30)
        title_box_width         = text_config.get("TITLE_BOX_WIDTH", None)  # Use full width if not provided.
        title_line_spacing      = text_config.get("TITLE_LINE_SPACING", 10)
        title_letter_spacing    = text_config.get("TITLE_LETTER_SPACING", 0)
        
        # === DURATION (Single Line) Configurations ===
        duration_font_size      = text_config.get("DURATION_FONT_SIZE", 90)
        duration_font_path      = text_config.get("DURATION_FONT_PATH", "arialbd.ttf")
        duration_color          = text_config.get("DURATION_COLOR", "white")
        duration_border_color   = text_config.get("DURATION_BORDER_COLOR", "black")
        duration_border_width   = text_config.get("DURATION_BORDER_WIDTH", 2)
        duration_x              = text_config.get("DURATION_X_POSITION", 30)
        duration_y              = text_config.get("DURATION_Y_POSITION", None)  # If not set, calculate from bottom.
        duration_box_width      = text_config.get("DURATION_BOX_WIDTH", None)
        duration_line_spacing   = text_config.get("DURATION_LINE_SPACING", 5)
        duration_letter_spacing = text_config.get("DURATION_LETTER_SPACING", 0)
        
        logger.info(f"Processing image: {os.path.basename(image_path)}")
        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # Load title font.
            try:
                title_font = ImageFont.truetype(title_font_path, title_font_size)
            except Exception as e:
                logger.warning(f"Failed to load title font from {title_font_path}, using default. Error: {e}")
                title_font = ImageFont.load_default()
            # Load duration font.
            try:
                duration_font = ImageFont.truetype(duration_font_path, duration_font_size)
            except Exception as e:
                logger.warning(f"Failed to load duration font from {duration_font_path}, using default. Error: {e}")
                duration_font = ImageFont.load_default()
            
            # If no box width is provided for the title text, use image width minus horizontal margin.
            if title_box_width is None:
                title_box_width = width - title_x * 2
            # Draw the title text block at the top-left (with centering within the box).
            draw_multiline_text_with_border_and_spacing(
                draw,
                title_lines,
                (title_x, title_y),
                title_font,
                title_color,
                title_border_color,
                title_border_width,
                title_letter_spacing,
                title_line_spacing,
                box_width=title_box_width
            )
            
            # Determine y position for duration text: if not set, place it a few pixels above the bottom.
            if duration_y is None:
                d_text_width, d_text_height = get_text_size(duration_text, duration_font, duration_letter_spacing)
                duration_y = height - d_text_height - 30  # 30 pixels from the bottom.
            if duration_box_width is None:
                duration_box_width = width - duration_x * 2
            # Draw the duration text (single line) at the bottom-left.
            draw_multiline_text_with_border_and_spacing(
                draw,
                [duration_text],
                (duration_x, duration_y),
                duration_font,
                duration_color,
                duration_border_color,
                duration_border_width,
                duration_letter_spacing,
                duration_line_spacing,
                box_width=duration_box_width
            )
            
            # Save the output thumbnail.
            img.save(config["THUMBNAIL_OUTPUT"], quality=95)
            logger.success(f"Thumbnail saved: {config['THUMBNAIL_OUTPUT']}")
            
    except Exception as e:
        logger.error(f"Thumbnail creation failed: {str(e)}")
        raise


if __name__ == "__main__":
    # For testing purposes, define a minimal config.
    test_config = {
        "RUN_INDIVIDUALLY": True,
        "IMAGES_DIR": "templates/VPM/VPM_images",
        "THUMBNAIL_TEXT_FILE": "templates/VPM/VPM_thumbnail_text.txt",
        "THUMBNAIL_OUTPUT": "output/thumbnail.jpg",
        "VIDEO_LENGTH_MINUTES": 60,
        "TEMPLATES_DIR": "templates/VPM"
    }
    process_thumbnail(test_config)
