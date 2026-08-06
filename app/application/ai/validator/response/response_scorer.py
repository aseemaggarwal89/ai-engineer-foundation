class AIResponseScorer:
    """
    Assigns a simple structural response score.
    Later you can replace with LLM-as-judge.
    """

    def score_bullets(self, bullets: list[str]) -> float:
        if not bullets:
            return 0.0
        
        avg_len = sum(len(b) for b in bullets) / len(bullets)

        score = 0.5

        if avg_len > 60:
            score += 0.2

        if len(bullets) >= 5:
            score += 0.2

        return min(score, 1.0)
    
    def score(self, text: str) -> float:

        score = 1.0

        if len(text) < 50:
            score -= 0.3

        if "maybe" in text.lower():
            score -= 0.1

        return max(score, 0.0)
