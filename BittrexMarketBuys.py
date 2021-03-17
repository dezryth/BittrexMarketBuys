import configparser
import datetime
import time
from datetime import datetime
from trade import trade

# Get config values
config = configparser.ConfigParser()
config.read("config.ini")
BittrexKey = config["DEFAULT"]["BittrexKey"]
BittrexSecret = config["DEFAULT"]["BittrexSecret"]

# Initialize Pushover for notifications. 
PushoverEnabled = 1
if (PushoverEnabled):
    PushoverToken = config["DEFAULT"]["PushoverToken"]
    PushoverUserKey = config["DEFAULT"]["PushoverUserKey"]

# Enable or disable testmode when ready to make live trades
global testMode
testMode = True  # Set to false when you're ready for real transactions

# Add all desired trades to a list of trades. Remove Pushover arguments if you are not using it.
trades = []
# cc, fiat, fundsToSpend
trades.append(trade('DCR', 'USD', 50, BittrexKey, BittrexSecret, PushoverToken, PushoverUserKey, testMode=True))
trades.append(trade('ETC', 'USD', 20, BittrexKey, BittrexSecret, PushoverToken, PushoverUserKey, testMode=True))

# Purchase if enough funds are available
print('-------------------------------------------------')
print('Time: ' + str(datetime.now()))

for trade in trades:
    print('')
    # Get available funds
    availableFunds = float(trade.getAvailableHoldings('USD'))
    print('Available USD: $' + str(availableFunds))
    
    availableCryptocurrency = float(trade.getAvailableHoldings(trade.cc))
    print('Available ' + str(trade.cc) + ': ' + str(availableCryptocurrency))

    # Get latest asking price
    print('Last ' + trade.cc + ' Ask: $' + str(trade.askPrice))

    # Check for available funds and initiate purchase
    if (availableFunds > trade.fundsToSpend):
        trade.Submit()
    else:
        if (PushoverEnabled):
            trade.PushoverNotify('Not enough available funds for ' + str(trade.cc)
                                + ' purchase!', 'Not Enough Funds')
            print('Not enough available funds for ' + trade.cc + ' order.')

print('-------------------------------------------------')
