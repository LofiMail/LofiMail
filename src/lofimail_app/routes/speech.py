"""Text-to-speech route."""

from flask import request

from tools.tospeech import speak_text


def speak():
    text = request.args.get("text", "")
    print("SPEAK", text)
    return speak_text(text)


def register_speech_routes(app):
    app.add_url_rule("/speak", endpoint="speak", view_func=speak, methods=["GET"])
