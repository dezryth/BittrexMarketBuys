# BittrexMarketBuys
[![ISC License](https://img.shields.io/badge/license-ISC-blue.svg)](http://copyfree.org)

## Overview

This is a Python script for recurring market buys on [Bittrex](https://bittrex.com/ "Bittrex"). Start dollar cost averaging into your favorite cryptocurrency ([Decred](https://decred.org "Decred"), right? 😉), or use this as a jumping-off point for a more sophisticated trading script. I wrote this to make cryptocurrency purchasing and investment strategy more accessible and configurable, and to make working with an API less intimidating for those that have never given it a shot. Not every cryptocurrency has a polished service like [Swan Bitcoin](https://www.swanbitcoin.com/dezryth/ "Swan Bitcoin"), but that doesn't mean we can't roll our own!

## Features

* Configure to purchase as much of whatever you want on Bittrex, as often as you want.
* Supports [Pushover](https://pushover.net "Pushover") for Push notifications to any devices you have the application installed on. Get notified whenever the script makes a trade!
* Stores info on the last trade in a txt file to be easily human readable and to determine next purchase date. (Full history is on Bittrex, of course)

## Getting Started
1. Clone the repository. 
2. Get an API Key/Secret from Bittrex with trading permissions and from Pushover (if you intend to use it). 
3. Copy or rename the sample-config.ini file to 'config.ini'.
4. Modify the script variables to set what you'd like to purchase, how much, and how often.
5. Test the script in test mode, and when you are comfortable, set testMode to False.
6. Run the script. See included example bash script to run the script periodically, or modify the python script to loop indefinitely and utilize `time.sleep()` if you prefer. 

## Support
If you need help, I am happy to provide direction/assistance. I am not responsible for any gains or losses you make utilizing this script, so only use it once you're comfortable and feel you know what you are doing! The code is commented so give it a read first.

If you'd like to support my work and show your appreciation, you can tip me Decred at address DsRDf6SzCY97VqCD67NF1jJrmD5YgWNFtQk

Enjoy! 

## License

BittrexMarketBuys is licensed under the [copyfree](http://copyfree.org) ISC License.