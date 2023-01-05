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
PushoverEnabled = 1

# SET IMPORTANT VARIABLES
testMode = True # Set to false when you're ready for real transactions
target = 'DCR'  # Ticker for the ultimate cryptocurrency you are buying
source = 'USD'  # What you're using to buy the cryptocurrency
targetMarket = target + '-' + source  # The market to trade source for target on Bittrex e.g DCR-USD
fundsToSpend = 5  # Number of units of source to spend to trade each time this script runs
exchangeWithdrawalsEnabled = False # Enable to automatically withdraw from the exchange once you reach the limit - NYKNYC!
exchangeHoldingsLimit = 10 # Amount of target to keep on the exchange before initiating a withdrawal if enabled
buyOnBTCMarket = True # This will place a spot market buy trade for BTC with source before purchasing the target asset with BTC
btcMarket = 'BTC' + '-' + source # The market to trade source for BTC if enabled as an intermediary step.
if (buyOnBTCMarket == True):
  targetMarket = target + '-' + 'BTC'


# Get config values
config = configparser.ConfigParser()
config.read("config.ini")
BittrexKey = config["DEFAULT"]["BittrexKey"]
BittrexSecret = config["DEFAULT"]["BittrexSecret"]
Address = config["DEFAULT"]["Address"]

# Initialize Pushover for notifications
if (PushoverEnabled):
    PushoverToken = config["DEFAULT"]["PushoverToken"]
    PushoverUserKey = config["DEFAULT"]["PushoverUserKey"]
    init(PushoverToken)

# Variables
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

def postWithdrawal(currency, quantity):
  "POST /withdrawals"
  timestamp = str(now_milliseconds())
  uri = ('https://api.bittrex.com/v3/withdrawals')
  method = "POST"
  withdrawalRequest = {
        "currencySymbol": currency,
        "quantity": quantity,
        "cryptoAddress": Address
  }
  withdrawalRequestJson = json.dumps(withdrawalRequest)
  contentHash = generateHash(withdrawalRequestJson)
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

  response = requests.post(uri, data=withdrawalRequestJson, headers=headers)
  print(response.text)
  jsonStr = json.loads(response.text)
  return jsonStr

######################################################################
# Methods to take advantage of Bittrex API methods


def placeOrder(orderAmount, askPrice, market):
    "Generate market buy at asking price"
    quantity = orderAmount / askPrice
    quantity = round(quantity, 8)
    total = round(quantity * askPrice, 8)
    assets = market.split('-')    
    target = assets[0]
    source = assets[1]
    if (source == 'USD'):
      roundPlace = 2 
    else:
      roundPlace = 8
    print('Buying ' + str(quantity) + ' ' + target + ' for a total of '
          + '{:.{roundPlace}f}'.format(total, roundPlace = roundPlace)  + ' ' + source + ' at ' + '{:.{roundPlace}f}'.format(askPrice, roundPlace = roundPlace) + ' ' + source + ' each.')

    if (testMode == False):
        response = postOrder(market, 'BUY', 'MARKET',
                             'IMMEDIATE_OR_CANCEL', quantity)
        if response.get("id"):
            saveTrade('Bought', quantity, askPrice, total)
            if (PushoverEnabled):
              Client(PushoverUserKey).send_message('Bought ' + str(quantity) + ' ' + str(target)
                                                    + ' for a total of ' + '{:.{roundPlace}f}'.format(total, roundPlace = roundPlace) + ' ' + source + ' at ' 
                                                    + '{:.{roundPlace}f}'.format(askPrice, roundPlace = roundPlace) + ' ' + source + ' each.', title=target + ' Purchase')
        else:
            if (PushoverEnabled):
                Client(PushoverUserKey).send_message('Buy order failed. Reason: ' + str(response),
                                                     title=target + ' Purchase Failed')
            print('Buy order failed. Reason: ' + response["code"])
    else:
        saveTrade('Bought', quantity, askPrice, total, testMode)
        if (PushoverEnabled):
            Client(PushoverUserKey).send_message('**TEST MODE**: Bought ' + str(quantity) + ' ' + str(target)
                                                 + ' for a total of ' + '{:.{roundPlace}f}'.format(total, roundPlace = roundPlace) + ' ' + source + ' at ' 
                                                 + '{:.{roundPlace}f}'.format(askPrice, roundPlace = roundPlace) + ' ' + source + ' each.', title=target + ' Purchase')
    
    return quantity


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


print('-------------------------------------------------')
if (testMode == True):
  print('**TEST MODE**')
print('Time: ' + str(datetime.now()))

# Get available funds
availableFunds = float(getAvailableHoldings(source))
availableCryptocurrency = float(getAvailableHoldings(target))
print('Available '+ source +': $' + str(availableFunds))
print('Available ' + str(target) + ': ' + str(availableCryptocurrency))

# Get latest target ask price
jsonStr = getMarket(targetMarket)
lastTargetAsk = float(jsonStr['askRate'])
print('Last ' + targetMarket + ' Ask: ' + str(lastTargetAsk))

# Get latest BTC ask price
jsonStr = getMarket(btcMarket)
lastBTCAsk = float(jsonStr['askRate'])
print('Last ' + btcMarket + ' Ask: ' + str(lastBTCAsk))

# Check for available funds and initiate purchase if enough funds are available
if (availableFunds > fundsToSpend):
    if (buyOnBTCMarket):
      btcToSpend = placeOrder(fundsToSpend, lastBTCAsk, btcMarket)
      # Ensure order has had some time to be fulfilled
      time.sleep(10)
      placeOrder(btcToSpend, lastTargetAsk, targetMarket)
    else:
      placeOrder(fundsToSpend, lastTargetAsk, targetMarket)
    if ((availableFunds - fundsToSpend) < fundsToSpend):      
      if (PushoverEnabled):
        Client(PushoverUserKey).send_message('There will not be enough funds to complete another market purchase on the next run. Deposit more ' + str(source)
          + ' to Bittrex Wallet.', title='Deposit more ' + source + ' to Bittrex Wallet')
        print('There will not be enough funds to complete another market purchase on the next run. Deposit more ' + source + ' to Bittrex Wallet.')
else:
    if (PushoverEnabled):
        Client(PushoverUserKey).send_message('Not enough available funds for ' + str(target)
                                             + ' purchase!', title='Not Enough Funds')
        print("Not enough available funds for order.")

print('-------------------------------------------------')

if (exchangeWithdrawalsEnabled and Address):
  # Initiate Withdraw if current holdings on exchange exceed user defined limit.
  availableCryptocurrency = float(getAvailableHoldings(target))
  if (availableCryptocurrency > exchangeHoldingsLimit):
      # Ensure most recent order has had time to be fulfilled
      time.sleep(10)

      response = postWithdrawal(target, availableCryptocurrency)
      if response.get("id"):
        if (PushoverEnabled):
            Client(PushoverUserKey).send_message(str(availableCryptocurrency) + str(target) + ' was withdrawn to your wallet.\n' + 
                                                                      str(response), title=str(target) + ' Withdrawn From Exchange')
            print(str(availableCryptocurrency) + str(target) + ' was withdrawn to your wallet.')
