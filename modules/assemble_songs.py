import os
from pydub import AudioSegment
from logger import ColoredLogger

logger = ColoredLogger("ASSEMBLE")

def format_time(milliseconds):  # Updated to handle hours (but hide if zero)
    seconds = milliseconds // 1000
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes:02}:{seconds:02}"

def load_names(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        names = f.readlines()
    names = [name.strip() for name in names]
    for index, name in enumerate(names):
        if not name.startswith('-'):
            return names, index
    return names, None

def save_names(file_path, names):
    with open(file_path, 'w', encoding='utf-8') as f:
        for name in names:
            f.write(name + '\n')

def assemble_songs(config):
    logger.module_start()
    PROCESSED_DIR = config["PROCESSED_DIR"]
    DESCRIPTION_OUTPUT_FILE = config["DESCRIPTION_OUTPUT_FILE"]
    DESCRIPTION_TEMPLATE_FILE = config["DESCRIPTION_TEMPLATE_FILE"]
    VIDEO_LENGTH_MINUTES = config["VIDEO_LENGTH_MINUTES"]
    TITLE_TEMPLATE_FILE = config["TITLE_TEMPLATE_FILE"]
    TITLE_OUTPUT_FILE = config["TITLE_OUTPUT_FILE"]
    
    min_duration_ms = VIDEO_LENGTH_MINUTES * 60 * 1000

    try:
        # Load description template
        if not os.path.exists(DESCRIPTION_TEMPLATE_FILE):
            logger.error(f"Description template missing: {DESCRIPTION_TEMPLATE_FILE}")
            raise FileNotFoundError(f"Template not found: {DESCRIPTION_TEMPLATE_FILE}")
            
        with open(DESCRIPTION_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            description_template = f.read()

        # Process audio files
        audio_segments = []
        total_duration = 0
        track_list = []
        used_files = []

        logger.info(f"Scanning {PROCESSED_DIR}")
        for filename in os.listdir(PROCESSED_DIR):
            if filename.lower().endswith('.mp3'):
                file_path = os.path.join(PROCESSED_DIR, filename)
                audio = AudioSegment.from_mp3(file_path)
                audio_duration = len(audio)

                audio_segments.append(audio)
                track_list.append((filename[:-4], total_duration))
                used_files.append(file_path)
                total_duration += audio_duration

                if total_duration >= min_duration_ms:
                    break

        if total_duration < min_duration_ms:
            logger.error(f"Insufficient audio: {total_duration//60000}min")
            raise RuntimeError("Insufficient audio duration")

        logger.info(f"Total duration: {total_duration//60000}:{(total_duration%60000)//1000:02}")

        # Generate final audio mix
        final_audio = sum(audio_segments)
        output_path = config["AUDIO_MIX_FILE"]
        final_audio.export(output_path, format='mp3')
        logger.info(f"Exported audio mix: {output_path}")

        # Cleanup processed files if deletion is enabled
        if config.get("DELETE_PROCESSED", True):
            for file_path in used_files:
                os.remove(file_path)
            logger.info(f"Removed {len(used_files)} processed files")
        else:
            logger.info(f"Left {len(used_files)} processed files intact")

        # Generate description with template
        processed_desc = description_template.replace(
            "[video_length]", 
            str(VIDEO_LENGTH_MINUTES)
        )

        # Generate tracklist content
        tracklist_content = ["\nTrack list:"]
        for track_name, start_time in track_list:
            timestamp = format_time(start_time)
            tracklist_content.append(f"{timestamp} Spectraform - {track_name}")

        # Split the template at the placeholder
        if "[TRACKLIST_PLACEHOLDER]" not in processed_desc:
            logger.error("Tracklist placeholder missing in description template")
            raise ValueError("Missing [TRACKLIST_PLACEHOLDER] in description template")

        parts = processed_desc.split("[TRACKLIST_PLACEHOLDER]")
        final_description = parts[0] + "\n".join(tracklist_content) + parts[1]

        # Write the final description
        with open(DESCRIPTION_OUTPUT_FILE, 'w', encoding='utf-8') as desc_file:
            desc_file.write(final_description)
        logger.info("Generated description file")

        # Handle title selection
        names, next_name_index = load_names(TITLE_TEMPLATE_FILE)
        if next_name_index is None:
            logger.error("No available titles")
            raise RuntimeError("No titles available")

        title_name = names[next_name_index].replace("[video_length]", str(VIDEO_LENGTH_MINUTES))
        with open(TITLE_OUTPUT_FILE, 'w', encoding='utf-8') as title_file:
            title_file.write(title_name + '\n')
        
        if config.get("MARK_USED_TITLE_NAMES", True):
            names[next_name_index] = '-' + names[next_name_index]
            save_names(TITLE_TEMPLATE_FILE, names)
        logger.success("Assembly completed")

    except Exception as e:
        logger.error(f"Assembly failed: {str(e)}")
        raise