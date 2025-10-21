import json
import traceback
from numpy import divide
import pandas as pd
import logging


logger = logging.getLogger(__name__)


class Symbol:
    
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path

    def load(self):

        try:
            with open(self.json_file_path, mode="r", encoding="utf-8") as read_file:
                symbol = json.load(read_file)
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return None
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing JSON: {e}")
            return None
        
        if symbol["chart"]["error"] is not None:
            logger.error(f"Error in response: {symbol['chart']['error']}")
            return None

        if len(symbol["chart"]["result"]) != 1:
            logger.error("Wrong number of results found in the response.")
            return None


        try:
                
            # Parse the metadata

            self.currency = symbol["chart"]["result"][0]["meta"]["currency"]
            self.name = symbol["chart"]["result"][0]["meta"]["symbol"]
            self.dataGranularity = symbol["chart"]["result"][0]["meta"]["dataGranularity"]
            self.exchangeName = symbol["chart"]["result"][0]["meta"]["exchangeName"]
            self.fullExchangeName = symbol["chart"]["result"][0]["meta"]["fullExchangeName"]
            self.instrumentType = symbol["chart"]["result"][0]["meta"]["instrumentType"]
            self.gmtoffset = symbol["chart"]["result"][0]["meta"]["gmtoffset"] # in seconds
            self.timezone = symbol["chart"]["result"][0]["meta"]["timezone"]
            self.timezoneName = symbol["chart"]["result"][0]["meta"]["exchangeTimezoneName"]
            

            # Parse timestamp and indicators

            df = pd.DataFrame({'timestamp': symbol["chart"]["result"][0]["timestamp"]})
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['close'] = symbol["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            df['open'] = symbol["chart"]["result"][0]["indicators"]["quote"][0]["open"]
            df['high'] = symbol["chart"]["result"][0]["indicators"]["quote"][0]["high"]
            df['low'] = symbol["chart"]["result"][0]["indicators"]["quote"][0]["low"]
            df['volume'] = symbol["chart"]["result"][0]["indicators"]["quote"][0]["volume"]
            # TODO: verificare a cosa serve l' adjclose: lo sostituisco al close ?
            df['adjclose'] = symbol["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"]
            self.ochlvDf = df


            # Parse events (Dividends)

            dividends_data = self.safe_get(symbol, ["chart", "result", 0, "events", "dividends"])
            if dividends_data:
                df = pd.DataFrame.from_dict(dividends_data, orient="index")
                df.index.name = "timestamp"
                df.reset_index(inplace=True)
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
                df["date"] = pd.to_datetime(df["date"], unit="s")
                self.eventsDf = df

            # TODO: parse other events

        except (Exception) as e:
            
            logger.error(f"Error parsing JSON: {e}")
            print(traceback.format_exc())
            return None
            
    def safe_get(self, d, path, default=None):
        """Safely get nested dictionary/list values by following a path list."""

        current = d
        for p in path:
            if isinstance(current, dict):
                current = current.get(p, default)
            elif isinstance(current, list):
                try:
                    current = current[p]
                except (IndexError, TypeError):
                    return default
            else:
                return default
        return current