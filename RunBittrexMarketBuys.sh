#!/bin/bash
echo "---Run Bittrex Market Buys---"
echo "Press [CTRL+C] to stop.."
while :
do
  python3 BittrexMarketBuys.py
  # Run every 12 hours
  sleep 43200
done