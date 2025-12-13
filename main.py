import os
import time
import argparse
from openai import OpenAI

API_KEY = open(".api-key", "r").read().strip()

# All files are combined as the instructions for the prompt
INSTRUCTION_DIR = "instruction"

# All files are combined as the input for the prompt
INPUT_DIR = "input"

OUTPUT_FILE = "output.txt"

# Models
MODEL_GPT_5_1 = "gpt-5.1"
MODEL_GPT_5 = "gpt-5"
MODEL_GPT_5_MINI = "gpt-5-mini"
MODEL_GPT_5_NANO = "gpt-5-nano"

DEFAULT_MODEL = MODEL_GPT_5_1


def format_transcript(transcript):
    """
    transcript: list of dicts with keys {role: 'user'|'assistant', content: str, label: optional}
    Returns a single string containing the conversation so far.
    """
    lines = []
    lines.append("Conversation so far:")
    for turn in transcript:
        speaker = "User" if turn["role"] == "user" else "Assistant"
        label = turn.get("label")
        title = f"{speaker}" + (f" - {label}" if label else "")
        lines.append(f"{title}:\n{turn['content']}\n")
    lines.append("Please continue by responding to the most recent user message.")
    return "\n".join(lines)


def send_request(client, model, instructions, input_text):
    start_time = time.time()
    print(f"# Sending request to OpenAI API... at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    response = client.responses.create(
        model=model,
        instructions=instructions,
        reasoning={
            "effort": "high"
        },
        input=input_text,
    )
    end_time = time.time()
    total_time = end_time - start_time
    print(f"# Total time thinking: {total_time:.2f} seconds")
    return response


def load_combined_text_from_dir(directory):
    combined = ""
    try:
        files = os.listdir(directory)
    except FileNotFoundError:
        files = []

    for file in files:
        filename = f"{directory}/{file}"
        if not os.path.isfile(filename):
            continue
        try:
            with open(filename, "r", encoding="utf-8") as f:
                if directory == INPUT_DIR:
                    combined += f"File: {filename}\n"
                combined += f.read()
                combined += "\n"
        except FileNotFoundError:
            continue
    return combined


def append_to_output(header, content):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write(header + "\n")
        f.write("-" * 80 + "\n")
        f.write(content.strip() + "\n")


def main():
    parser = argparse.ArgumentParser(description="Send a request to the OpenAI Responses API with optional follow-ups.")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        choices=[MODEL_GPT_5, MODEL_GPT_5_MINI, MODEL_GPT_5_NANO],
        help="Model to use.",
    )
    parser.add_argument(
        "--interactive",
        default=True,
        action="store_true",
        help="Enable interactive follow-up mode after the first response.",
    )
    args = parser.parse_args()

    instructions = load_combined_text_from_dir(INSTRUCTION_DIR)
    input_text = load_combined_text_from_dir(INPUT_DIR)

    print(f"# Using model {args.model}")

    if not input_text:
        input_text = input("Please enter input text (end with Ctrl-D):\n").strip()

    if not input_text.strip():
        print("# No input data found.")
        return

    if not instructions:
        instructions = input("Please enter instructions (end with Ctrl-D):\n").strip()

    if not instructions.strip():
        print("# No instructions found.")
        return

    client = OpenAI(api_key=API_KEY)

    # First request
    response_num = 0
    response = send_request(client, args.model, instructions, input_text)
    first_output = response.output_text

    with open(f"response_{response_num}.txt", "w", encoding="utf-8") as f:
        f.write(first_output.strip() + "\n")
        response_num += 1

    print(response.output_text)

    # Overwrite or create output.txt with the initial response
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"INITIAL RESPONSE\n  input: {input_text}\n  instructions: {instructions}\n")
        f.write("=" * 80 + "\n")
        f.write(first_output.strip() + "\n")

    print(f"# Response saved to {OUTPUT_FILE}")

    # Prepare transcript for follow-ups
    transcript = [
        {"role": "user", "content": input_text, "label": "Original input"},
        {"role": "assistant", "content": first_output, "label": "Initial response"},
    ]

    # Interactive follow-up mode
    if args.interactive:
        count = 1
        while True:
            try:
                user_followup = input("# Enter follow-up (empty line to finish): ").strip()
            except EOFError:
                break

            if not user_followup:
                break

            transcript.append({"role": "user", "content": user_followup, "label": f"Interactive follow-up {count}"})
            followup_input = format_transcript(transcript)
            followup_response = send_request(client, args.model, instructions, followup_input)
            followup_output = followup_response.output_text

            with open(f"response_{response_num}.txt", "w", encoding="utf-8") as f:
                f.write(followup_output.strip() + "\n")
                response_num += 1
            transcript.append({"role": "assistant", "content": followup_output, "label": f"Interactive follow-up {count} response"})

            append_to_output(f"INTERACTIVE FOLLOW-UP {count}\n{user_followup}", followup_output)

            print(followup_output)

            print(f"# Interactive follow-up {count} response appended to {OUTPUT_FILE}")
            count += 1


if __name__ == "__main__":
    main()
