from dataclasses import dataclass, field
from typing import List

@dataclass
class AppSettings:
    recent_searches: List[str] = field(default_factory=list)
    last_interval: str = "1d"
    last_period: str = "1mo"
    last_export_format: str = "csv"
    
    def add_recent_search(self, symbol: str):
        if symbol in self.recent_searches:
            self.recent_searches.remove(symbol)
        self.recent_searches.insert(0, symbol)
        if len(self.recent_searches) > 10:
            self.recent_searches = self.recent_searches[:10]
