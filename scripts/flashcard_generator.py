import json
import ollama
import logging
import urllib.request
import argparse
from DictionaryServices import DCSGetTermRangeInString, DCSCopyTextDefinition

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

API_URL = "http://127.0.0.1:8765"
DECK_NAME = "French::Le Creuset::Copilote"
MODEL_NAME = "Basic"


def get_response(prompt):
    try:
        response = ollama.chat(
            model="gemma2", messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        logging.error(f"Error getting response: {e}")
        raise


def invoke(action, **params):
    request_json = json.dumps(
        {"action": action, "params": params, "version": 6}
    ).encode("utf-8")
    try:
        with urllib.request.urlopen(
            urllib.request.Request(API_URL, request_json)
        ) as response:
            response_data = json.load(response)
        validate_response(response_data)
        return response_data["result"]
    except Exception as e:
        logging.error(f"Error invoking action '{action}': {e}")
        raise


def validate_response(response):
    if len(response) != 2 or "error" not in response or "result" not in response:
        raise ValueError("Invalid response structure")
    if response["error"]:
        raise Exception(response["error"])


def lookup(word):
    try:
        word_range = DCSGetTermRangeInString(None, word, 0)
        if not word_range:
            return "NOT FOUND"
        definition = DCSCopyTextDefinition(None, word, word_range)
        return definition if definition else "NOT FOUND"
    except Exception as e:
        logging.error(f"Error looking up word '{word}': {e}")
        return f"Error: {str(e)}"


def create_card(front, back, deck_name=DECK_NAME):
    note = {
        "deckName": deck_name,
        "modelName": MODEL_NAME,
        "fields": {"Front": front, "Back": back},
        "tags": [],
    }
    try:
        return invoke("addNote", note=note)
    except Exception as e:
        return handle_create_card_exception(e, note)


def handle_create_card_exception(exception, note):
    error_message = str(exception).lower()
    deck_name = note["deckName"]
    if "deck was not found" in error_message:
        logging.info(f"Deck '{deck_name}' not found. Creating deck.")
        invoke("createDeck", deck=deck_name)
        return invoke("addNote", note=note)
    elif "duplicate" in error_message:
        logging.info(f"Note already exists in deck '{deck_name}'.")
        return None
    else:
        logging.error(f"Error creating card: {exception}")
        raise exception


def main(word):
    description = lookup(word)
    prompt = (
        f"Please enhance and reformat the following dictionary definition for the word '{word}':\n\n"
        f"{description}\n\n so that it is clear, concise, and suitable for use in an Anki flashcard. "
        "DO NOT USE MARKDOWN, OUTPUT THE RESULT IN HTML FORMAT."
    )
    augmented_description = get_response(prompt)
    create_card(word, augmented_description)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create Anki flashcards for a given word."
    )
    parser.add_argument(
        "word", type=str, help="The word to lookup and create a flashcard for."
    )
    args = parser.parse_args()
    main(args.word)
