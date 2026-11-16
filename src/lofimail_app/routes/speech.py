from flask import Blueprint, request

from ..services.speech import speak_text

bp = Blueprint("speech", __name__)


@bp.route("/speak")
def speak():
    text = request.args.get("text", "")
    print("SPEAK", text)
    return speak_text(text)
