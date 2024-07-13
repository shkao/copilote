import os
import re
from pathlib import Path
from pydub import AudioSegment
import openai
import argparse


def clean_markdown_text(text):
    text = re.sub(r"!?\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"#+", "", text)
    text = re.sub(r"\*\*?(.*?)\*\*?", r"\1", text)
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)
    text = re.sub(r">", "", text)
    text = re.sub(r"[-*_]", "", text)
    return text.strip()


def split_text(text, limit=4096):
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip(" ")
    return chunks


def text_to_speech(text_chunks, voice="echo", speed=0.75):
    audio_chunks = []
    client = openai.Client()
    for i, chunk in enumerate(text_chunks):
        params = {
            "model": "tts-1-hd",
            "voice": voice,
            "input": chunk.strip(),
            "speed": speed,
        }
        audio_path = Path(f"temp_chunk_{i}.mp3")
        try:
            response = client.audio.speech.create(**params)
            response.stream_to_file(str(audio_path))
            audio_chunks.append(AudioSegment.from_mp3(audio_path))
            os.remove(audio_path)
        except Exception as e:
            print(f"Error: {e}")
    return audio_chunks


def combine_audio(chunks):
    combined = AudioSegment.empty()
    for chunk in chunks:
        combined += chunk
    return combined


def process_markdown_file(file_path):
    output_path = Path(file_path).with_suffix(".mp3")
    if not output_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        cleaned_text = clean_markdown_text(text)
        text_chunks = split_text(cleaned_text)
        audio_chunks = text_to_speech(text_chunks)
        combined_audio = combine_audio(audio_chunks)
        combined_audio.export(output_path, format="mp3")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a Markdown file to speech.",
    )
    parser.add_argument(
        "file",
        type=str,
        help="The Markdown file to convert.",
    )
    args = parser.parse_args()

    if args.file and os.path.isfile(args.file) and args.file.endswith(".md"):
        process_markdown_file(args.file)
    else:
        print("Error: Please provide a valid Markdown file.")
        parser.print_help()
