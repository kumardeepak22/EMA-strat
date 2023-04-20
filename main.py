from broker.zerodha import Zerodha as zd
from utilities.utility import subscribed_symbol
import pandas as pd
from strategies.strategy import Strategy
import os
from creds import creds

# Create a dictionary to hold tick data
tick_data = {}

# Check if "data" folder exists, else create it
if not os.path.exists("data"):
    os.mkdir("data")
    print("Data folder created successfully!")
else:
    print("Folder already exists.")

def on_ticks(ws, ticks):
    """
    Function to handle ticks received from the Kite API

    Parameters:
    ws (obj): WebSocket instance
    ticks (list): list of tick data received from the API
    """
    for tick in ticks:
        # Extract required data from the tick
        instrument_token = tick['instrument_token']
        last_price = tick['last_price']
        timestamp = tick['timestamp']

        # Append the tick data to the tick_data dictionary
        if instrument_token not in tick_data:
            tick_data[instrument_token] = []
        tick_data[instrument_token].append({'timestamp': timestamp, 'ltp':last_price})

def on_connect(ws, response):
    """
    Function to handle connection to the Kite API

    Parameters:
    ws (obj): WebSocket instance
    response (dict): response received from the API
    """
    # Subscribe to required symbols and set mode
    tokens = [63923719]
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL,tokens)  

# Instantiate Zerodha object with credentials
market_data = zd(creds)

# Read strategy parameters from CSV file and extract required data
strategy_params = pd.read_csv('./strategy_parameters.csv').to_dict(orient='records')[0]
tradingsymbol, instrument_token = subscribed_symbol(strategy_params['symbol'],market_data.kite)
strategy_params['tradingsymbol'] = 'CRUDEOIL23MAYFUT' #tradingsymbol
strategy_params['instrument_token'] = 63923719 #instrument_token

# Print the instrument token for debugging purposes
print(strategy_params['instrument_token'])

# Set the on_ticks and on_connect functions of the Zerodha object to the defined functions
market_data.kws.on_ticks = on_ticks
market_data.kws.on_connect = on_connect
market_data.kws.connect(threaded=True)

# Create the Strategy object with required parameters
ema_cross = Strategy(strategy_params, market_data, tick_data)

# Run the strategy
ema_cross.run_strategy()
