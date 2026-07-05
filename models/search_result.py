from dataclasses import dataclass
from typing import Optional

@dataclass
class SearchResult:
    symbol: str
    short_name: str
    exchange: str
    quote_type: str
    currency: Optional[str] = None
    
    @property
    def display_text(self) -> str:
        """Text shown in the suggestion dropdown."""
        return f"{self.symbol} - {self.short_name}"
    
    @property
    def metadata_text(self) -> str:
        """Detailed metadata shown below the search bar when selected."""
        currency_str = f"\nCurrency: {self.currency}" if self.currency else ""
        return f"Ticker: {self.symbol}\nExchange: {self.exchange}\nType: {self.quote_type}{currency_str}"
