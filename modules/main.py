#main.py
import cut_songs
import assemble_songs
import create_video
import create_thumbnail
from pydub import AudioSegment
import os
import sys
from logger import ColoredLogger

logger = ColoredLogger("MAIN")

def get_resource_report(config):
    model = config['TEMPLATES_DIR'].split('/')[-1]
    report = f"\n📊 Resource Report for {model} Model:\n"
    
    # Song names
    song_names = []
    if os.path.exists(config["SONG_NAMES_FILE"]):
        with open(config["SONG_NAMES_FILE"], 'r', encoding='utf-8') as f:
            song_names = [line.strip() for line in f if not line.startswith('-')]
    report += f"1. Available Song Names: {len(song_names)}\n"
    
    # Title names
    title_names = []
    if os.path.exists(config["TITLE_TEMPLATE_FILE"]):
        with open(config["TITLE_TEMPLATE_FILE"], 'r', encoding='utf-8') as f:
            title_names = [line.strip() for line in f if not line.startswith('-')]
    report += f"2. Available Title Names: {len(title_names)}\n"
    
    # Processed songs
    processed_songs = []
    total_duration = 0
    processed_dir = config["PROCESSED_DIR"]
    if os.path.exists(processed_dir):
        for fname in os.listdir(processed_dir):
            if fname.endswith('.mp3'):
                file_path = os.path.join(processed_dir, fname)
                try:
                    audio = AudioSegment.from_file(file_path)
                    processed_songs.append(fname)
                    total_duration += len(audio)
                except Exception as e:
                    logger.error(f"Reading {file_path}: {str(e)}")
    mins, secs = divmod(total_duration//1000, 60)
    report += (f"3. Processed Songs Available: {len(processed_songs)} tracks "
               f"({mins:02}:{secs:02})\n")
    
    # Images
    available_images = 0
    images_dir = config["IMAGES_DIR"]
    if os.path.exists(images_dir):
        available_images = len([f for f in os.listdir(images_dir) 
                              if f.lower().endswith(('png', 'jpg', 'jpeg'))])
    report += f"4. Available Images: {available_images}\n"
    
    return report

def preflight_check(config):
    errors = []
    model = config['TEMPLATES_DIR'].split('/')[-1]
    required_duration = config["VIDEO_LENGTH_MINUTES"] * 60 * 1000

    # Check song names
    song_names_available = 0
    if os.path.exists(config["SONG_NAMES_FILE"]):
        with open(config["SONG_NAMES_FILE"], 'r', encoding='utf-8') as f:
            song_names_available = sum(1 for line in f if not line.startswith('-'))
    
    # Check unprocessed songs
    unprocessed_files = []
    if os.path.exists(config["UNPROCESSED_DIR"]):
        unprocessed_files = [f for f in os.listdir(config["UNPROCESSED_DIR"]) 
                           if f.lower().endswith('.mp3')]
    
    # Check processed duration
    processed_duration = 0
    if os.path.exists(config["PROCESSED_DIR"]):
        for fname in os.listdir(config["PROCESSED_DIR"]):
            if fname.endswith('.mp3'):
                try:
                    audio = AudioSegment.from_file(os.path.join(config["PROCESSED_DIR"], fname))
                    processed_duration += len(audio)
                except Exception as e:
                    errors.append(f"Invalid audio file: {fname} ({str(e)})")

    # Check title names
    title_names_available = 0
    if os.path.exists(config["TITLE_TEMPLATE_FILE"]):
        with open(config["TITLE_TEMPLATE_FILE"], 'r', encoding='utf-8') as f:
            title_names_available = sum(1 for line in f if not line.startswith('-'))

    # Check images
    available_images = 0
    if os.path.exists(config["IMAGES_DIR"]):
        available_images = len([f for f in os.listdir(config["IMAGES_DIR"]) 
                              if f.lower().endswith(('png', 'jpg', 'jpeg'))])

    # Validation
    if processed_duration < required_duration:
        if not unprocessed_files:
            errors.append(f"Need {required_duration//60000}min audio, only have {processed_duration//60000}min")
        elif song_names_available < len(unprocessed_files):
            errors.append(f"{song_names_available} song names for {len(unprocessed_files)} songs")

    if title_names_available == 0:
        errors.append("No video titles available")
    
    if available_images == 0:
        errors.append("No template images available")

    return errors

def main():
    model = "VPM"
    
    config = {
        "UNPROCESSED_DIR": f"templates/{model}/{model}_unprocessed_songs",
        "PROCESSED_DIR": f"templates/{model}/{model}_processed_songs",
        "IMAGES_DIR": f"templates/{model}/{model}_images",
        "SONG_NAMES_FILE": f"templates/{model}/{model}_song_names.txt",
        "TITLE_TEMPLATE_FILE": f"templates/{model}/{model}_title_names.txt",
        "DESCRIPTION_TEMPLATE_FILE": f"templates/{model}/{model}_description.txt",
        "THUMBNAIL_TEXT_FILE": f"templates/{model}/{model}_thumbnail_text.txt",
        "TEMPLATES_DIR": f"templates/{model}",

        "DESCRIPTION_OUTPUT_FILE": "output/description.txt",
        "TITLE_OUTPUT_FILE": "output/title.txt",
        "AUDIO_MIX_FILE": "output/video-mix.mp3",
        "VIDEO_OUTPUT_FILE": "output/video-mix.mp4",
        "THUMBNAIL_OUTPUT": "output/thumbnail.jpg",

        "START_OFFSET": 10000,
        "SILENCE_THRESHOLD": -30,
        "MIN_SILENCE_2": 2000,
        "SEEK_STEP": 10,
        "VIDEO_LENGTH_MINUTES": 70,

        "RUN_INDIVIDUALLY": True,

        "DELETE_UNPROCESSED": True,
        "DELETE_PROCESSED": True,
        "DELETE_AUDIO_MIX": True,
        "DELETE_USED_IMAGES": True,
        "MARK_USED_SONG_NAMES": True,
        "MARK_USED_TITLE_NAMES": True,
    }

    logger.module_start()
    logger.info("Running preflight checks")
    errors = preflight_check(config)
    
    if errors:
        logger.error("Preflight check failed")
        for error in errors:
            logger.error(f"- {error}")
        logger.info("Current resource status:")
        print(get_resource_report(config))
        sys.exit(1)

    logger.success("All checks passed")
    
    try:
        cut_songs.process_songs(config)
        assemble_songs.assemble_songs(config)
        create_video.create_video(config)
        create_thumbnail.process_thumbnail(config)
        
        logger.success("Production completed")
        print(get_resource_report(config))
        
        # Cleanup after all processing: remove used image if enabled
        if "SELECTED_IMAGE" in config and os.path.exists(config["SELECTED_IMAGE"]):
            if config.get("DELETE_USED_IMAGES", True):
                os.remove(config["SELECTED_IMAGE"])
                logger.info(f"Removed used template image: {os.path.basename(config['SELECTED_IMAGE'])}")
            
    except Exception as e:
        logger.error(f"Production failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
