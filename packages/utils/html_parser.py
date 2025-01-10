from html.parser import HTMLParser
from typing import override


class IncidentHtmlDescriptionParser(HTMLParser):
    _instance: "IncidentHtmlDescriptionParser | None" = None

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.skip_until_closing_bracket: bool = False
        self.current_line: list[str] = []
        self.in_warning_message: bool = False

    @classmethod
    def get_instance(cls) -> "IncidentHtmlDescriptionParser":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def parse_text(cls, text: str | None) -> str:
        """Class method to parse HTML text using a cached instance."""
        if text is None:
            return ""

        instance = cls.get_instance()
        instance.text = []  # Reset the text buffer
        instance.skip_until_closing_bracket = False  # Reset the skip flag
        instance.in_warning_message = False
        instance.current_line = []
        instance.feed(text)
        return "\n".join(instance.text)  # Join with newlines instead of spaces

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Add newlines before certain elements
        if tag in ['h1', 'h2', 'li', 'p']:
            self.text.append('')  # Add empty line before these elements

    @override
    def handle_endtag(self, tag: str) -> None:
        # Add newlines after certain elements
        if tag in ['h1', 'h2', 'li', 'p']:
            if self.text and self.text[-1]:  # If there's text and it's not empty
                self.text.append('')  # Add empty line after these elements

    @override
    def handle_data(self, data: str):
        text = data.strip()

        # Check for warning message start
        if "You don't often get email from" in text:
            self.in_warning_message = True
            self.current_line = []

            if "[" in text:
                parts = text.split("[", 1)
                if parts[0].strip():
                    self.text.append(parts[0].strip())
                self.skip_until_closing_bracket = True
            return

        # If we're in warning mode, collect text until we see "Learn why"
        if self.in_warning_message:
            if "]" in text:
                self.skip_until_closing_bracket = False
                self.in_warning_message = False
                parts = text.split("]", 1)
                if len(parts) > 1 and parts[1].strip():
                    cleaned_text = parts[1].strip()
                    if not any(
                        x in cleaned_text
                        for x in ["Learn why this is important", "https://aka.ms/"]
                    ):
                        self.text.append(cleaned_text)
            elif "Learn why this is important" in text:
                self.in_warning_message = False
            return

        # Handle bracketed content
        if self.skip_until_closing_bracket:
            if "]" in text:
                self.skip_until_closing_bracket = False
                parts = text.split("]", 1)
                if len(parts) > 1 and parts[1].strip():
                    cleaned_text = parts[1].strip()
                    if not any(
                        x in cleaned_text
                        for x in ["Learn why this is important", "https://aka.ms/"]
                    ):
                        self.text.append(cleaned_text)
            return

        # Skip if we're in skip mode or if it's a comment
        if (
            text
            and not self.skip_until_closing_bracket
            and not text.startswith("<!--")
            and not text.endswith("-->")
        ):
            # Format key-value pairs with colons
            if ": " in text and not text.startswith("From:") and not text.startswith("Sent:"):
                key, value = text.split(": ", 1)
                self.text.append(f"{key}: {value}")
            else:
                self.text.append(text)

    @override
    def handle_comment(self, data: str):
        # Skip comments
        pass
