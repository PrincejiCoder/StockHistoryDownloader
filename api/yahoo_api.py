import yfinance as yf
import requests
import pandas as pd
from typing import List, Tuple
from models.search_result import SearchResult
from utils.logger import logger

class YahooAPI:
    @staticmethod
    def search_ticker(query: str) -> List[SearchResult]:
        if not query:
            return []
            
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {"q": query, "quotesCount": 10, "newsCount": 0}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for quote in data.get('quotes', []):
                # Filter to only equity, etfs, indices etc
                if 'quoteType' in quote and 'symbol' in quote:
                    results.append(SearchResult(
                        symbol=quote.get('symbol', ''),
                        short_name=quote.get('shortname', quote.get('longname', 'Unknown')),
                        exchange=quote.get('exchange', 'Unknown'),
                        quote_type=quote.get('quoteType', 'Unknown'),
                        currency=quote.get('currency', '')
                    ))
            return results
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise Exception("Search failed. Check your internet connection or try again.")
            
    @staticmethod
    def fetch_history(symbol: str, period: str, interval: str) -> pd.DataFrame:
        logger.info(f"Fetching history for {symbol}, period={period}, interval={interval}")
        try:
            df = yf.download(
                symbol,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=False
            )
            
            if df.empty:
                return df
                
            # Flatten multi-index columns if present (from recent yfinance changes)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df.columns = [str(c).lower() for c in df.columns]
            df = df.reset_index()
            
            # Standardize date column
            if "Datetime" in df.columns:
                df.rename(columns={"Datetime": "datetime"}, inplace=True)
            elif "Date" in df.columns:
                df.rename(columns={"Date": "datetime"}, inplace=True)
                
            df.columns = [str(c).lower() for c in df.columns]
            
            # Format datetime
            df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
            df["datetime"] = df["datetime"].dt.tz_convert("Asia/Kolkata")
            
            # Drop rows missing OHLC
            df = df.dropna(subset=["open", "high", "low", "close"])
            
            return df
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            raise Exception(f"Failed to download data: {e}")
