class BulletParser:
    """
    Parses bullet-style AI output into structured data.
    """

    def parse(self, text: str) -> list[str]:
        lines = [line.strip("-• ").strip() for line in text.splitlines()]
        return [line for line in lines if line]
