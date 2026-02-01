class SummaryPrompt:

    VERSION = "v1"

    def build(self, text: str) -> str:
        return f"""
Summarize in 5 bullet points:

{text}
"""
