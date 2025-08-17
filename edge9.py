class TextProcessor:
    def clean_text(self, text):
        # Remove various whitespace characters
        text = text.replace("\n", " ")  # newlines
        text = text.replace("\t", " ")  # tabs
        text = text.replace("\r", " ")  # carriage returns
        return text.strip()