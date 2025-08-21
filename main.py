import os
from openai import OpenAI

API_KEY = open(".api-key", "r").read().strip()

# All files are combined as the instructions for the prompt
INSTRUCTION_DIR = "instruction"

# All files are combined as the input for the prompt
INPUT_DIR = "input"

OUTPUT_FILE = "output.txt"


def main():
    instructions = ""
    input = ""

    try:
        input_files = os.listdir(INPUT_DIR)
    except FileNotFoundError:
        input_files = []

    for file in input_files:
        filename = f"{INPUT_DIR}/{file}"
        filename_is_a_file = os.path.isfile(filename)
        if not filename_is_a_file:
            continue
        try:
            with open(filename, "r", encoding="utf-8") as f:
                input += f"File: {filename}\n"
                input += f.read()
                input += "\n"
        except FileNotFoundError:
            continue
    try:
        instruction_files = os.listdir(INSTRUCTION_DIR)
    except FileNotFoundError:
        instruction_files = []

    for file in instruction_files:
        filename = f"{INSTRUCTION_DIR}/{file}"
        filename_is_a_file = os.path.isfile(filename)
        if not filename_is_a_file:
            continue
        try:
            with open(filename, "r", encoding="utf-8") as f:
                instructions += f.read()
        except FileNotFoundError:
            continue

    if not input.strip():
        print("No input data found.")
        return

    if not instructions.strip():
        print("No instructions found.")
        return

    with open(".provided-instructions", "w", encoding="utf-8") as f:
        f.write(instructions)

    with open(".provided-input", "w", encoding="utf-8") as f:
        f.write(input)

    client = OpenAI(
        api_key=API_KEY,
    )

    response = client.responses.create(
        model="gpt-5-nano",
        instructions=instructions,
        input=input,
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.output_text)


if __name__ == "__main__":
    main()
