#cut_songs.py
import os
from pydub import AudioSegment
from pydub.silence import detect_silence
from logger import ColoredLogger

logger = ColoredLogger("CUT")

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

def process_songs(config):
    logger.module_start()
    UNPROCESSED_DIR = config["UNPROCESSED_DIR"]
    PROCESSED_DIR = config["PROCESSED_DIR"]
    NAMES_FILE_PATH = config["SONG_NAMES_FILE"]
    
    try:
        if not os.path.exists(PROCESSED_DIR):
            os.makedirs(PROCESSED_DIR)
            logger.info(f"Created directory: {PROCESSED_DIR}")

        names, next_name_index = load_names(NAMES_FILE_PATH)
        if next_name_index is None:
            logger.error("No song names available")
            return

        processed_count = 0
        for filename in os.listdir(UNPROCESSED_DIR):
            if filename.lower().endswith('.mp3'):
                file_path = os.path.join(UNPROCESSED_DIR, filename)
                logger.info(f"Processing: {filename}")

                audio = AudioSegment.from_mp3(file_path)

                # Skip if the original file is too short
                if audio.duration_seconds < 120:
                    logger.info(f"Skipping {filename}, duration too short ({audio.duration_seconds:.2f}s)")
                    if config.get("DELETE_UNPROCESSED", True):
                        os.remove(file_path)  # Delete the original file if enabled
                    continue  # Move to the next file

                analysis_segment = audio[config["START_OFFSET"]:]
                
                silences = detect_silence(
                    analysis_segment,
                    min_silence_len=config["MIN_SILENCE_2"],
                    silence_thresh=config["SILENCE_THRESHOLD"],
                    seek_step=config["SEEK_STEP"]
                )

                if silences:
                    silence_start = config["START_OFFSET"] + silences[0][0]
                    new_end = silence_start + 2000
                else:
                    new_end = len(audio)

                if new_end >= 6000:
                    fade_start = new_end - 6000
                    fade_end = new_end - 2000
                    fade_duration = fade_end - fade_start
                    final_audio = audio[:fade_start] + \
                                audio[fade_start:fade_end].fade_out(fade_duration) + \
                                AudioSegment.silent(duration=2000)
                else:
                    final_audio = audio[:new_end]

                new_filename = f"{names[next_name_index]}.mp3"
                output_path = os.path.join(PROCESSED_DIR, new_filename)
                final_audio.export(output_path, format="mp3")
                logger.info(f"Saved as: {new_filename}")

                # Verify duration of the processed file
                duration = final_audio.duration_seconds
                if duration < 120:  # 2 minutes = 120 seconds
                    logger.info(f"File too short ({duration:.2f}s). Removing: {new_filename} and original")
                    os.remove(output_path)  # Remove the processed file
                    if config.get("DELETE_UNPROCESSED", True):
                        os.remove(file_path)     # Remove the original file if enabled
                else:
                    if config.get("DELETE_UNPROCESSED", True):
                        os.remove(file_path)  # Remove the original file if deletion is enabled
                        logger.info(f"Removed original: {filename}")
                    else:
                        logger.info(f"Left original intact: {filename}")
                    
                    # Mark the name as used only if the file is valid and marking is enabled
                    if config.get("MARK_USED_SONG_NAMES", True):
                        names[next_name_index] = '-' + names[next_name_index]
                        save_names(NAMES_FILE_PATH, names)
                    processed_count += 1

                names, next_name_index = load_names(NAMES_FILE_PATH)
                if next_name_index is None:
                    logger.warning("No more song names available")
                    break

        logger.success(f"Processed {processed_count} files")

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise

if __name__ == "__main__":
    config = {
        "UNPROCESSED_DIR": "unprocessed_songs",
        "PROCESSED_DIR": "processed_songs",
        "SONG_NAMES_FILE": "templates/VPM/VPM_song_names.txt",
        "START_OFFSET": 10000,
        "SILENCE_THRESHOLD": -30,
        "MIN_SILENCE_2": 2000,
        "SEEK_STEP": 10,
        "DELETE_UNPROCESSED": True,
        "MARK_USED_SONG_NAMES": True
    }
    process_songs(config)
