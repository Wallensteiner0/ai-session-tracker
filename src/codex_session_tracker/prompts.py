from __future__ import annotations


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    if not value and default is not None:
        return default
    return value


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    default_text = "ja" if default else "nein"
    value = ask(prompt, default_text).lower()
    return value in {"j", "ja", "y", "yes"}


def ask_rating(prompt: str) -> int:
    while True:
        value = ask(prompt)
        try:
            rating = int(value)
        except ValueError:
            print("Bitte eine Zahl zwischen 1 und 5 eingeben.")
            continue
        if 1 <= rating <= 5:
            return rating
        print("Bitte eine Zahl zwischen 1 und 5 eingeben.")
