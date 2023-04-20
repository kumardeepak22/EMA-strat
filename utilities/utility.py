import pandas as pd
from datetime import datetime

# Define market timing
MARKET_OPEN_TIME = '23:25'
MARKET_CLOSE_TIME = '23:29'

def subscribed_symbol(symbol, kite):
    """
    Function to extract required data for a given symbol

    Parameters:
    symbol (str): trading symbol
    kite (obj): Kite object

    Returns:
        trading symbol and instrument token
    """
    # Get instrument data for the required symbol
    instruments = pd.DataFrame(kite.instruments())
    tradinginstrument = instruments[(instruments['name']=='NIFTY') & (instruments['segment']=='NFO-FUT')]
    expiry = tradinginstrument.expiry.min()
    tradinginstrument = tradinginstrument[tradinginstrument['expiry']==expiry]
    # Return trading symbol and instrument token for the required symbol
    return tradinginstrument.tradingsymbol.values[0], tradinginstrument.instrument_token.values[0]

def time_now():
    return datetime.now()
