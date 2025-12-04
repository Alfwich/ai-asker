import os
import time
import sys
from openai import OpenAI

API_KEY = open(".api-key", "r").read().strip()

# The first image here will be used as an image reference for video generation.
INPUT_DIR = "input"

MODEL = "sora-2"
SIZES = ["1280x720", "720x1280"]


def load_image_ref_from_input_dir(directory):
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


def log(msg):
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    message = f"[{date}] {msg}"
    sys.stdout.write(f"{message}\n")


def main():

    openai = OpenAI(api_key=API_KEY)

    videos = openai.videos.list()
    if not videos.data:
        log("No existing videos.")
    else:
        log("Existing videos:")
        for video in videos.data:
            log(f"\t{video}")

    log("\n")

    prompt = input("Please enter video prompt (end with Ctrl-D):\n").strip()
    while not prompt:
        log("### Prompt cannot be empty.")
        prompt = input("Please enter video prompt (end with Ctrl-D):\n").strip()

    seconds = input("Please enter video duration in seconds [4, 8, 12] (end with Ctrl-D):\n").strip()
    while seconds not in ("4", "8", "12"):
        log("### Invalid duration. Please enter 4, 8, or 12.")
        seconds = input("Please enter video duration in seconds [4, 8, 12] (end with Ctrl-D):\n").strip()

    size_idx = input("Please enter video size index [0=1280x720, 1=720x1280] (end with Ctrl-D):\n").strip()
    while size_idx not in ("0", "1"):
        log("### Invalid size index. Please enter 0 or 1.")
        size_idx = input("Please enter video size index [0, 1] (end with Ctrl-D):\n").strip()
    size = SIZES[int(size_idx)]

    image_reference_path = load_image_ref_from_input_dir(INPUT_DIR)

    video = None

    remix_video_id = input("Please enter remix video ID (or leave blank to create new video) (end with Ctrl-D):\n").strip()
    if remix_video_id:
        video = openai.videos.remix(
            video_id=remix_video_id,
            prompt=prompt)
    elif image_reference_path is not None and len(image_reference_path) > 0:
        with open(image_reference_path, "rb") as f:
            video = openai.videos.create(
                model=MODEL,
                size=size,
                seconds=seconds,
                prompt=prompt,
                input_reference=f)
    else:
        video = openai.videos.create(
            model=MODEL,
            size=size,
            seconds=seconds,
            prompt=prompt)

    log(f"Video generation started: {video}")

    progress = getattr(video, "progress", 0)
    bar_length = 50

    while video.status in ("in_progress", "queued"):
        # Refresh status
        video = openai.videos.retrieve(video.id)
        progress = getattr(video, "progress", 0)

        filled_length = int((progress / 100) * bar_length)
        bar = "=" * filled_length + "-" * (bar_length - filled_length)
        status_text = "Queued" if video.status == "queued" else "Processing"

        log(f"{status_text}: [{bar}] {progress:.1f}%")
        time.sleep(2)

    if video.status == "failed":
        message = getattr(
            getattr(video, "error", None), "message", "Video generation failed"
        )
        log(message)
        return

    log(f"Video generation completed: {video}")
    log("Downloading video content...")
    log(f"Video generation started: {video}")
    content = openai.videos.download_content(video.id, variant="video")
    content.write_to_file("video.mp4")

    log("Wrote video.mp4")


if __name__ == "__main__":
    main()
