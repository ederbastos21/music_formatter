#create_video.py
import os
import random
from moviepy import AudioFileClip, ImageClip
from logger import ColoredLogger

logger = ColoredLogger("VIDEO")

def create_video(config):
    logger.module_start()
    IMAGES_DIR = config["IMAGES_DIR"]
    AUDIO_MIX_FILE = config["AUDIO_MIX_FILE"]
    VIDEO_OUTPUT_FILE = config["VIDEO_OUTPUT_FILE"]

    if not os.path.exists(IMAGES_DIR):
        logger.error(f"Missing template directory: {IMAGES_DIR}")
        raise FileNotFoundError(f"Directory not found: {IMAGES_DIR}")
    
    if not os.path.exists(AUDIO_MIX_FILE):
        logger.error(f"Missing audio file: {AUDIO_MIX_FILE}")
        raise FileNotFoundError(f"File not found: {AUDIO_MIX_FILE}")
    
    image_files = [f for f in os.listdir(IMAGES_DIR)
                   if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    
    if not image_files:
        logger.error("No images available in templates")
        raise RuntimeError("No template images available")
    
    try:
        # Select and store image path for thumbnail creation
        image_path = os.path.join(IMAGES_DIR, random.choice(image_files))
        config["SELECTED_IMAGE"] = image_path
        logger.info(f"Selected image: {os.path.basename(image_path)}")
        
        # Create video
        audio_clip = AudioFileClip(AUDIO_MIX_FILE)
        image_clip = ImageClip(image_path).with_duration(audio_clip.duration).with_fps(24)
        video = image_clip.with_audio(audio_clip)
        
        logger.info("Rendering video...")
        video.write_videofile(VIDEO_OUTPUT_FILE, codec="libx264", audio_codec="aac")
        logger.success(f"Video created: {VIDEO_OUTPUT_FILE}")
        
        # Cleanup audio file if deletion is enabled
        if config.get("DELETE_AUDIO_MIX", True) and os.path.exists(AUDIO_MIX_FILE):
            os.remove(AUDIO_MIX_FILE)
            logger.info("Removed temporary audio file")
            
    except Exception as e:
        logger.error(f"Video creation failed: {str(e)}")
        raise
