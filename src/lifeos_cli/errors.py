from __future__ import annotations


class CliValidationError(ValueError):
    def __init__(self, message: str, *, command: str = "parse") -> None:
        super().__init__(message)
        self.command = command
        self.message = message


class CliConfigError(RuntimeError):
    pass
