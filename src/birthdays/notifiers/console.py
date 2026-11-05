class ConsoleNotifier:
    name = "console"

    def send(self, message: str) -> None:
        print(message)