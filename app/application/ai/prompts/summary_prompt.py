class SummaryPrompt:
    """
    Deterministic prompt builder.
    """

    VERSION = "v1"

    def build(self, text: str) -> str:
        return f"""
Summarize the following text into 5 concise bullet points.

Text:
{text}
"""
