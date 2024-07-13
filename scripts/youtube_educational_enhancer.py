import argparse
import os
from litellm import completion, completion_cost
from pytube import YouTube
import whisper
from whisper.utils import get_writer

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Constants
MODEL_NAME = "gpt-4o"
WHISPER_MODEL_SIZE = "medium"
DEFAULT_AUDIO_PATH = "audio.mp3"


def download_audio(youtube_url, output_path=DEFAULT_AUDIO_PATH):
    """Download the audio from YouTube."""
    yt = YouTube(youtube_url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    if not audio_stream:
        raise RuntimeError("No audio stream found.")
    audio_stream.download(filename=output_path)
    print(f"Downloaded audio to {output_path}")


def transcribe_audio(audio_path, output_dir):
    """Transcribe the audio using Whisper."""
    model = whisper.load_model(WHISPER_MODEL_SIZE)
    result = model.transcribe(audio_path, fp16=False)

    srt_writer = get_writer("srt", output_dir)
    srt_writer(result, os.path.join(output_dir, "transcript.srt"))

    return result["text"], result["segments"]


def save_to_file(content, filename):
    """Save the given content to a file."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Content saved to {filename}")


def read_from_file(filename):
    """Read content from a file."""
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


def generate_response(prompt):
    """Generate a response using LiteLLM."""
    messages = [{"content": prompt, "role": "user"}]
    response = completion(model=MODEL_NAME, messages=messages)

    cost = completion_cost(completion_response=response)
    formatted_string = f"${float(cost):.5f}"
    print(f"Response cost: {formatted_string}")

    return response["choices"][0]["message"]["content"]


def summarize_and_generate_questions(transcript):
    """Summarize the transcript and generate questions."""
    summary = generate_response(
        f"Please summarize the following transcript in French (level: DELF B1)\n\n{transcript}"
    )
    questions = generate_response(
        f"Using the summary text, generate 3 questions in French (level: DELF B1) to test comprehension of the content. Exclude any questions about the YouTube channel itself:\n\n{summary}"
    )
    return summary, questions


def answer_questions_in_french(summary, questions):
    """Answer questions in French based on the summary."""
    prompt = f"Based on the following summary: {summary}\n\nAnswer the following questions in French (level: DELF B1):\n\n{questions}"
    return generate_response(prompt)


def main(youtube_url):
    """Main function to handle the workflow."""
    audio_path = DEFAULT_AUDIO_PATH
    yt = YouTube(youtube_url)
    title = yt.title
    output_dir = title.replace(" ", "_")

    # Create directory for the title
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    audio_path = os.path.join(output_dir, "audio.mp3")

    # Download audio
    if not os.path.exists(audio_path):
        download_audio(youtube_url, audio_path)
    else:
        print(f"Audio already downloaded at {audio_path}")

    # Transcribe audio
    transcript_filename = os.path.join(output_dir, "transcript.txt")
    srt_filename = os.path.join(output_dir, "transcript.srt")
    if not os.path.exists(transcript_filename) or not os.path.exists(srt_filename):
        transcript, _ = transcribe_audio(audio_path, output_dir)
        save_to_file(transcript, transcript_filename)
    else:
        print(f"Transcript already exists at {transcript_filename}")
        print(f"SRT file already exists at {srt_filename}")
        transcript = read_from_file(transcript_filename)

    # Summarize and generate questions
    summary_filename = os.path.join(output_dir, "summary.txt")
    questions_filename = os.path.join(output_dir, "questions.txt")
    if not os.path.exists(summary_filename) or not os.path.exists(questions_filename):
        summary, questions = summarize_and_generate_questions(transcript)
        save_to_file(summary, summary_filename)
        save_to_file(questions, questions_filename)
    else:
        print(f"Summary already exists at {summary_filename}")
        print(f"Questions already exist at {questions_filename}")
        summary = read_from_file(summary_filename)
        questions = read_from_file(questions_filename)

    # Answer questions in French
    answers_filename = os.path.join(output_dir, "answers.txt")
    if not os.path.exists(answers_filename):
        answers = answer_questions_in_french(summary, questions)
        save_to_file(answers, answers_filename)
    else:
        print(f"Answers already exist at {answers_filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download, transcribe, and summarize YouTube audio."
    )
    parser.add_argument("youtube_url", help="URL of the YouTube video")
    args = parser.parse_args()

    main(args.youtube_url)
