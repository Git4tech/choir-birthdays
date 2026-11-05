from typing import Protocol


class Notifier(Protocol):
    name: str

    def send(self, message: str) -> None: ...