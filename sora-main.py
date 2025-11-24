import os
import time
import sys
from openai import OpenAI

API_KEY = open(".api-key", "r").read().strip()

# The first image here will be used as an image reference for video generation.
INPUT_DIR = "input"

MODEL = "sora-2"
SIZE = "1280x720"


def load_image_ref_from_input_dir(directory):
    combined = ""
    try:
        files = os.listdir(directory)
    except FileNotFoundError:
        files = []

    for file in files:
        filename = f"{directory}/{file}"
        if not os.path.isfile(filename):
            continue

        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            return filename

    return None


def main():

    openai = OpenAI(api_key=API_KEY)

    videos = openai.videos.list()
    if not videos.data:
        print("# No existing videos.")
    else:
        print("# Existing videos:")
        for video in videos.data:
            print(f"- {video}")

    print("\n")

    prompt = input("Please enter video prompt (end with Ctrl-D):\n").strip()
    if not prompt.strip():
        print("# No prompt.")
        return

    seconds = input("Please enter video duration in seconds [4, 8, 12] (end with Ctrl-D):\n").strip()
    if not seconds.strip():
        print("# No seconds.")
        return

    video = None

    remix_video_id = input("Please enter remix video ID (or leave blank to create new video) (end with Ctrl-D):\n").strip()
    if remix_video_id:
        video = openai.videos.remix(
            video_id=remix_video_id,
            prompt=prompt)
    else:
        image_reference_path = load_image_ref_from_input_dir(INPUT_DIR)
        if image_reference_path is not None:
            with open(image_reference_path, "rb") as f:
                video = openai.videos.create(
                    model=MODEL,
                    size=SIZE,
                    seconds=seconds,
                    prompt=prompt,
                    input_reference=f)
        else:
            video = openai.videos.create(
                model=MODEL,
                size=SIZE,
                seconds=seconds,
                prompt=prompt)

    print("Video generation started:", video)

    progress = getattr(video, "progress", 0)
    bar_length = 30

    while video.status in ("in_progress", "queued"):
        # Refresh status
        video = openai.videos.retrieve(video.id)
        progress = getattr(video, "progress", 0)

        filled_length = int((progress / 100) * bar_length)
        bar = "=" * filled_length + "-" * (bar_length - filled_length)
        status_text = "Queued" if video.status == "queued" else "Processing"

        sys.stdout.write(f"{status_text}: [{bar}] {progress:.1f}%\n")
        time.sleep(2)

    # Move to next line after progress loop
    sys.stdout.write("\n")

    if video.status == "failed":
        message = getattr(
            getattr(video, "error", None), "message", "Video generation failed"
        )
        print(message)
        return

    print("Video generation completed:", video)
    print("Downloading video content...")

    print("Video generation started:", video)
    content = openai.videos.download_content(video.id, variant="video")
    content.write_to_file("video.mp4")

    print("Wrote video.mp4")


if __name__ == "__main__":
    main()
