from .. import config
from .callmebot import CallMeBotNotifier
from .console import ConsoleNotifier

REGISTRY = {"console": ConsoleNotifier, "callmebot": CallMeBotNotifier}


def get_notifier():
    try:
        return REGISTRY[config.NOTIFIER]()
    except KeyError:
        raise SystemExit(f"Unknown NOTIFIER '{config.NOTIFIER}'. Choose from: {', '.join(REGISTRY)}")