import codecs
import datetime
import time
import hmac
import hashlib
import json
import requests
import sqlite3
import json
import collections
import subprocess
import configparser
import sys
from datetime import datetime
from pushover import init, Client

# Enable Push notifications
PushoverEnabled = 0

# SET IMPORTANT VARIABLES
testMode = True  # Set to false when you're ready for real transactions
cc = 'DCR'  # Ticker for the cryptocurrency you are buying
fiat = 'USD'  # What you're using to buy the cryptocurrency
market = cc + '-' + fiat  # The market on Bittrex e.g DCR-USD
fundsToSpend = 50  # Amount of funds to spend each time this script runs
purchaseFrequencyDays = 5  # Number of days to wait before another purchase

# Get last trade date if it exists from lasttrade.txt
try:
    with open('lasttrade.txt') as json_file:
        data = json.load(json_file)
    for x in data['data']:
        # This converts the json string back to a datetime object
        lastTradeDate = datetime.strptime(
            x['tradeTime'], '%Y-%m-%d %H:%M:%S.%f')
    # Determine if time to purchase again
    global dateDiff
    dateDiff = (datetime.now() - lastTradeDate).days
except:
    dateDiff = -1  # This is the first run/lasttrade.txt doesn't exist
    pass

# If not the first run, check if it's been enough days since last purchase or exit
if (dateDiff != -1 and dateDiff <= purchaseFrequencyDays):
    print("It has been " + str(dateDiff) +
          " days since the last purchase. Exiting.")
    sys.exit()

# Get config values
config = configparser.ConfigParser()
config.read("config.ini")
BittrexKey = config["DEFAULT"]["BittrexKey"]
BittrexSecret = config["DEFAULT"]["BittrexSecret"]

# Initialize Pushover for notifications
if (PushoverEnabled):
    PushoverToken = config["DEFAULT"]["PushoverToken"]
    PushoverUserKey = config["DEFAULT"]["PushoverUserKey"]
    init(PushoverToken)


# Variables
apisign = ''
headers = {'content-type': 'application/json'}


def signMessage(message):
    "Function to sign an API call"
    global BittrexSecret
    signature = hmac.new(codecs.encode(BittrexSecret),
                         codecs.encode(message), hashlib.sha512).hexdigest()
    return signature


def generateHash(message):
    "Function to generate a hash of a message"
    hash = hashlib.sha512(str(message).encode("utf-8")).hexdigest()
    return hash


def now_milliseconds():
    "Function to return timestamp in milliseconds"
    return int(time.time() * 1000)

######################################################################
# Bittrex API v3


def getMarket(market):
    "GET /markets/{marketSymbol}/ticker"
    timestamp = str(now_milliseconds())
    uri = 'https://api.bittrex.com/v3/markets/' + market + '/ticker'
    method = "GET"
    contentHash = generateHash("")
    subaccountId = ""
    preSign = timestamp + uri + method + contentHash + subaccountId
    signature = signMessage(preSign)
    headers = {
        'content-type': 'application/json',
        'Api-Key': BittrexKey,
        'Api-Timestamp': timestamp,
        'Api-Content-Hash': generateHash(""),
        'Api-Signature': signature
    }
    response = requests.get(uri, headers=headers)
    # print(response.text)
    jsonStr = json.loads(response.text)
    return jsonStr


def getAvailableHoldings(ticker):
    "GET /balances/{currencySymbol}"
    timestamp = str(now_milliseconds())
    uri = 'https://api.bittrex.com/v3/balances/' + ticker
    method = "GET"
    contentHash = generateHash("")
    subaccountId = ""
    preSign = timestamp + uri + method + contentHash + subaccountId
    signature = signMessage(preSign)
    headers = {
        'content-type': 'application/json',
        'Api-Key': BittrexKey,
        'Api-Timestamp': timestamp,
        'Api-Content-Hash': generateHash(""),
        'Api-Signature': signature
    }

    response = requests.get(uri, headers=headers)
    # print(response.text)
    jsonStr = json.loads(response.text)
    availableFunds = jsonStr["available"]
    return availableFunds


def postOrder(market, direction, type, timeInForce, quantity):
    "POST /orders"
    timestamp = str(now_milliseconds())
    uri = ('https://api.bittrex.com/v3/orders')
    method = "POST"
    orderRequest = {
        "marketSymbol": market,
        "direction": direction,
        "type": type,
        "quantity": quantity,
        "timeInForce": timeInForce
    }
    orderRequestJson = json.dumps(orderRequest)
    contentHash = generateHash(orderRequestJson)
    subaccountId = ""
    preSign = timestamp + uri + method + contentHash + subaccountId
    signature = signMessage(preSign)

    headers = {
        'content-type': 'application/json',
        'Api-Key': BittrexKey,
        'Api-Timestamp': timestamp,
        'Api-Content-Hash': contentHash,
        'Api-Signature': signature
    }

    response = requests.post(uri, data=orderRequestJson, headers=headers)
    print(response.text)
    jsonStr = json.loads(response.text)
    return jsonStr

######################################################################
# Methods to take advantage of Bittrex API methods


def buyCryptocurrency(orderAmount, askPrice, testMode):
    "Generate market buy at asking price"
    quantity = orderAmount / askPrice
    quantity = round(quantity, 8)
    total = round(quantity * askPrice, 8)
    print('Buying ' + str(quantity) + ' ' + str(cc) + ' for a total of $'
          + str(round(total, 2)) + ' at $' + str(round(askPrice, 2)) + ' each.')

    if (testMode != True):
        response = postOrder(market, 'BUY', 'MARKET',
                             'IMMEDIATE_OR_CANCEL', quantity)
        if response.get("id"):
            saveTrade('Bought', quantity, askPrice, total)
            if (PushoverEnabled):
                Client(PushoverUserKey).send_message('Bought ' + str(quantity) + str(cc)
                                                     + ' for $' + str(round(total, 2)), title=cc + ' Purchase')
        else:
            if (PushoverEnabled):
                Client(PushoverUserKey).send_message('Buy order failed. Reason: ' + str(response),
                                                     title=cc + ' Purchase Failed')
            print('Buy order failed. Reason: ' + response["code"])
    else:
        saveTrade('Bought', quantity, askPrice, total, testMode)
        if (PushoverEnabled):
            Client(PushoverUserKey).send_message('**TEST MODE**: Bought ' + str(quantity) + str(cc)
                                                 + ' for $' + str(round(total, 2)), title=cc + ' Purchase')
        print('**TEST MODE**')


def saveTrade(action, quantity, price, total, testMode=False):
    "Save trade details to a file called 'lasttrade.txt'"
    data = {}
    data['data'] = []
    data['data'].append({
        'action': action,
        'quantity': quantity,
        'price': price,
        'totalPrice': total,
        'tradeTime': str(datetime.now()),
        'testMode': testMode
    })
    with open('lasttrade.txt', 'w') as outfile:
        json.dump(data, outfile)


# Purchase if enough funds are available
print('-------------------------------------------------')
print('Time: ' + str(datetime.now()))

# Get available funds
availableFunds = float(getAvailableHoldings('USD'))
availableCryptocurrency = float(getAvailableHoldings(cc))
print('Available USD: $' + str(availableFunds))
print('Available ' + str(cc) + ': ' + str(availableCryptocurrency))

# Get latest asking price
jsonStr = getMarket(market)
lastAsk = float(jsonStr['askRate'])
print('Last Ask: $' + str(lastAsk))

# Check for available funds and initiate purchase
if (availableFunds > fundsToSpend):
    buyCryptocurrency(fundsToSpend, lastAsk, testMode)
else:
    if (PushoverEnabled):
        Client(PushoverUserKey).send_message('Not enough available funds for ' + str(cc)
                                             + ' purchase!', title='Not Enough Funds')
        print("Not enough available funds for order.")

print('-------------------------------------------------')
