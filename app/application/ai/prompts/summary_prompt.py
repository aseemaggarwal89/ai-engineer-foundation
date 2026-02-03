class SummaryPrompt:
    """
    Deterministic prompt builder.
    """

    VERSION = "v1"

    def build(self, text: str) -> str:
        return (
    "Summarize the following text into EXACTLY 5 short bullet points.\n"
    "Do not explain. Do not add extra text.\n\n"
    f"Text:\n{text}"
)
