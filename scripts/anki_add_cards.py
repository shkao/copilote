import json
import urllib.request


def request(action, **params):
    return {"action": action, "params": params, "version": 6}


def invoke(action, **params):
    requestJson = json.dumps(request(action, **params)).encode("utf-8")
    response = json.load(
        urllib.request.urlopen(
            urllib.request.Request("http://127.0.0.1:8765", requestJson)
        )
    )
    if len(response) != 2:
        raise Exception("response has an unexpected number of fields")
    if "error" not in response:
        raise Exception("response is missing required error field")
    if "result" not in response:
        raise Exception("response is missing required result field")
    if response["error"] is not None:
        raise Exception(response["error"])
    return response["result"]


def create_card(word, sentence, deck_name="French"):
    note = {
        "deckName": deck_name,
        "modelName": "Basic",
        "fields": {"Front": word, "Back": sentence},
        "tags": [],
    }
    try:
        return invoke("addNote", note=note)
    except Exception as e:
        if "deck was not found" in str(e).lower():
            invoke("createDeck", deck=deck_name)
            return invoke("addNote", note=note)
        elif "duplicate" in str(e).lower():
            print(
                f"Note with word '{word}' and sentence '{sentence}' already exists in deck '{deck_name}'."
            )
            return None
        else:
            raise e


# Example usage of create_card function
create_card("test", "This is an example sentence.")
