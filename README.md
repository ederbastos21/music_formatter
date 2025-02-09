# Video Production Automation Tool

This Python program automates the creation of video content by processing audio files, assembling them into a single mix, generating a video with a static image, and creating a thumbnail. Below is a concise explanation of how the program works.

---

## **Overview**

The program consists of several modules that handle different stages of the video production process:

1. **`main.py`**: The entry point of the program. It orchestrates the workflow, performs preflight checks, and calls other modules.
2. **`cut_songs.py`**: Processes raw audio files by trimming silence and applying fades.
3. **`assemble_songs.py`**: Combines processed audio files into a single mix and generates a description file.
4. **`create_video.py`**: Creates a video by overlaying the audio mix onto a static image.
5. **`create_thumbnail.py`**: Generates a thumbnail for the video with custom text overlays.
6. **`logger.py`**: Provides colored logging for better visibility of program output.

---

## **How It Works**

### **1. Preflight Checks**
- The program starts by validating resources (e.g., audio files, images, and text templates) to ensure all required components are available.
- It checks for:
  - Sufficient audio duration.
  - Availability of song names, titles, and images.
  - Proper configuration settings.

### **2. Audio Processing**
- Raw audio files in the `UNPROCESSED_DIR` are processed:
  - Silence at the beginning and end is trimmed.
  - Fades are applied to smooth transitions.
  - Processed files are saved in the `PROCESSED_DIR`.

### **3. Audio Assembly**
- Processed audio files are combined into a single mix.
- A description file is generated, including a tracklist with timestamps.
- A title is selected from a pool of available titles.

### **4. Video Creation**
- The audio mix is overlaid onto a randomly selected image from the `IMAGES_DIR`.
- The final video is saved as an MP4 file.

### **5. Thumbnail Creation**
- A thumbnail is generated using the selected image and custom text (e.g., video title and duration).
- Text is rendered with optional borders, spacing, and alignment.

### **6. Cleanup**
- Temporary files (e.g., processed audio, used images) are deleted if configured to do so.

---

## **Configuration**

The program uses a `config` dictionary in `main.py` to define paths, settings, and behavior. Key configurations include:

- **Directories**:
  - `UNPROCESSED_DIR`: Folder for raw audio files.
  - `PROCESSED_DIR`: Folder for processed audio files.
  - `IMAGES_DIR`: Folder for template images.
- **Files**:
  - `SONG_NAMES_FILE`: List of song names.
  - `TITLE_TEMPLATE_FILE`: List of video titles.
  - `DESCRIPTION_TEMPLATE_FILE`: Template for video descriptions.
- **Settings**:
  - `VIDEO_LENGTH_MINUTES`: Target duration of the video.
  - `DELETE_UNPROCESSED`: Whether to delete raw audio files after processing.
  - `DELETE_PROCESSED`: Whether to delete processed audio files after assembly.

---

## **Usage**

1. Place raw audio files in the `UNPROCESSED_DIR`.
2. Ensure all required text files (e.g., song names, titles) are populated.
3. Run `main.py`:
   ```bash
   python main.py