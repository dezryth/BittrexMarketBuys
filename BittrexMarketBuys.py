import configparser
import datetime
import time
from datetime import datetime
from Trade import Trade

# Enable Push notifications
PushoverEnabled = 0

# Get config values
config = configparser.ConfigParser()
config.read("config.ini")
BittrexKey = config["DEFAULT"]["BittrexKey"]
BittrexSecret = config["DEFAULT"]["BittrexSecret"]

# Initialize Pushover for notifications
if (PushoverEnabled):
    PushoverToken = config["DEFAULT"]["PushoverToken"]
    PushoverUserKey = config["DEFAULT"]["PushoverUserKey"]

# Enable or disable testmode when ready to make live trades
global testMode
testMode = True  # Set to false when you're ready for real transactions

# Add all desired trades to a list of trades.
trades = []
# cc, fiat, fundsToSpend
trades.append(Trade('DCR', 'USD', 50, BittrexKey, BittrexSecret, testMode=True))
trades.append(Trade('ETC', 'USD', 20, BittrexKey, BittrexSecret, testMode=True))

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
