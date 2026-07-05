def is_valid_ticker(ticker: str) -> bool:
    """Basic validation for ticker strings."""
    if not ticker or len(ticker.strip()) == 0:
        return False
    return True
