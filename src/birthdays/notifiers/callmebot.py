import requests

from .. import config


class CallMeBotNotifier:
    name = "callmebot"

    def send(self, message: str) -> None:
        if not (config.CALLMEBOT_PHONE and config.CALLMEBOT_APIKEY):
            raise RuntimeError("CALLMEBOT_PHONE / CALLMEBOT_APIKEY are not set")
        resp = requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={"phone": config.CALLMEBOT_PHONE, "text": message, "apikey": config.CALLMEBOT_APIKEY},
            timeout=30,
        )
        resp.raise_for_status()