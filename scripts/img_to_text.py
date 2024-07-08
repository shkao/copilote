import os
import base64
import requests
import argparse
from PIL import Image
from datetime import datetime

api_key = os.getenv("OPENAI_API_KEY")


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def downsize_image(image_path, max_size=(2000, 2000)):
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        downsized_path = "downsized_" + os.path.basename(image_path)
        img.save(downsized_path)
        return downsized_path


def create_payload(base64_image):
    return {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Please extract important French vocabulary words from the provided image. "
                            "List each distinct French word on a new line without any symbols or additional characters. "
                            "For verbs, provide the bare infinitive forms. "
                            "For nouns, provide the singular form. "
                            "For adjectives, provide the masculine singular form. "
                            "Ensure that no leading '-' is included. "
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }


def process_image(image_path, output_file):
    downsized_image_path = downsize_image(image_path)
    base64_image = encode_image(downsized_image_path)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = create_payload(base64_image)

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )

    response_data = response.json()
    new_words = response_data["choices"][0]["message"]["content"].split("\n")

    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            existing_words = set(f.read().splitlines())
    else:
        existing_words = set()

    unique_words = [word for word in new_words if word and word not in existing_words]

    with open(output_file, "a") as f:
        for word in unique_words:
            f.write(word + "\n")

    os.remove(downsized_image_path)


def main():
    parser = argparse.ArgumentParser(
        description="Process an image or a directory of images."
    )
    parser.add_argument(
        "input_paths",
        type=str,
        nargs="+",
        help="Path to the image file(s) or directory containing images",
    )
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"french_vocabulary_{timestamp}.txt"

    for input_path in args.input_paths:
        if os.path.isdir(input_path):
            for filename in os.listdir(input_path):
                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    process_image(os.path.join(input_path, filename), output_file)
        else:
            process_image(input_path, output_file)


if __name__ == "__main__":
    main()
