def normalize_email(email: str) -> str:
    """
    Apply the project's email identity normalization policy.

    This intentionally stays simple: trim surrounding whitespace and compare
    email addresses case-insensitively.
    """
    return email.strip().lower()
