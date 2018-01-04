#!/usr/bin/python
import urllib2,ssl,json,time,datetime

#TODO:
# HANDLE ERRORS BETTER
# flags to compare btc or usd [or any other] -- sort of done with baseCurrency
# add optional labels for wallets
# sort and report most profitable from yiimp -- done in another script instead
# dont getYiimp() for each wallet. this is excessive and dumb.

baseCurrency = 'BTC'
csvfilename = 'wallets.csv'
scrollerfilename = '/home/u/.irssi/scripts/scroll.txt'

portfolio={ #define wallet addresses here
 # "vtc":"VrgAYSL3NPtHtcfN6s4oryBgDRXS1hrifG" # put your wallets here in this format
}

hashrate={ # hashrate dictionary -- DEPRECATED see above
  "vtc":34, #MH/s
  "crea":0.571, # GH/s
  "gbx":0.757, #MH/s
  "xvg":8.00 #MH/s
}

explorers={ #url to your explorer of your coin. replace 'coin' with XXXX and address with ZZZZ in url.
  "default":"https://chainz.cryptoid.info/XXXX/api.dws?q=getbalance&a=ZZZZ",\
  "gbx":"http://explorer.gobyte.network:5001/ext/getbalance/ZZZZ",\
  "xvg":"https://verge-blockchain.info/ext/getbalance/ZZZZ"
}

longname={ # long names of coins, for CMC
  "gbx":"gobyte",\
  "btc":"bitcoin",\
  "vtc":"vertcoin",\
  "crea":"creativecoin",\
  "xvg":"verge"
}

def colorNumber(number): #for colorified term output
  if number < 0:
    color = '\033[91m'
  else:
    color = '\033[92m'
  string = color + str(number) + '\033[0m'
  return string

def request(url):
  ctx=ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE
  opener = urllib2.build_opener(urllib2.HTTPSHandler(context=ctx))
  opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
  try:
    req = opener.open(url).read()
  except :
    return 0
  return req

def getYiimp():
  data = json.loads(request("http://api.yiimp.eu/api/currencies"))
  return data

def getPrice(coin): #percent_change_1h _24h _7d
  lname = longname.get(coin,"")
  data = json.loads(request("https://api.coinmarketcap.com/v1/ticker/" + lname + "/"))
  return data#[0]["price_usd"]

#btcprice=getPrice("BTC")[0]["price_usd"]

def getWallet(coin, address):
  global baseCurrency
  btcprice=getPrice("BTC")[0]["price_usd"]
  if (baseCurrency == 'BTC'):
    price = getPrice(coin)[0]["price_btc"]
    price = float(price)*10**8 #convert to sats. i'm sick of looking at excessive leading zeros ffs.
    baseCurrency = 'SAT'
  else:
    baseCurrency = '$USD'
    price = getPrice(coin)[0]["price_usd"]

  change1h = float(getPrice(coin)[0]["percent_change_1h"])
  change24h= float(getPrice(coin)[0]["percent_change_24h"])
  change7d = float(getPrice(coin)[0]["percent_change_7d"])
  yiimp=getYiimp()
  btcpmh = float(yiimp[coin.upper()]["estimate"])/1000
  usdpmh = btcpmh * float(btcprice)
  hashrt = hashrate.get(coin,1)
  usdpd  = usdpmh * hashrt
  url = explorers.get(coin,explorers["default"])
  url = url.replace("XXXX", coin)
  url = url.replace("ZZZZ",address)
  try:
    walletbal = float(request(url))
  except:
    walletbal = 0
  print "[ " + longname.get(coin,"") + " (1h/24h/7d: %s/%s/%s) ]" % (colorNumber(change1h), colorNumber(change24h), colorNumber(change7d))
  print "  %s/%s:\t%6.0f\tMining (USD/d):\t$%8.2f (at %4.1fxH/s)" % (baseCurrency,coin,float(price), usdpd, hashrt)
  print "  Wallet bal.: \t%10.8f\tWallet (%s):\t%10.0f" % (float(walletbal),baseCurrency,(float(price) * float(walletbal)))
  results = {
    "coin":coin,
    "change1h":change1h,
    "change24h":change24h,
    "change7d":change7d,
    "price":float(price),
    "usdpd":usdpd,
    "hashrt":hashrt,
    "bal":float(walletbal),
    "val":(float(price) * float(walletbal))
  }
  return results

def outputCSV(w):
  f = open(csvfilename, "a+")
  line = str(time.time()) + ','
  for coin in w:
    line += "%s,%9.8f,%8.2f,%10.8f,%8.2f," % (coin, w[coin]["price"],w[coin]["usdpd"],w[coin]["bal"],w[coin]["val"])
  #print line
  line += "\n"
  f.write(line)
  f.close()

def outputScroller(w,s):
  global baseCurrency
  ts = time.time()
  dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
  scrollerstring=''
  for coin in w:
    scrollerstring += "%s:%6.0f %s (%4.2f/%4.2f/%4.2f) [%10.8f (%8.0f %s)]///" % (coin, w[coin]["price"], baseCurrency,w[coin]["change1h"],w[coin]["change24h"],w[coin]["change7d"], w[coin]["bal"],w[coin]["val"],baseCurrency)
  scrollerstring += " Total value: %10.0f %s /// " % (s,baseCurrency)
  scrollerstring += "%s UTC" % dt
  f = open(scrollerfilename, "w+")
  print scrollerstring.upper()
  f.write(scrollerstring.upper())
  f.close()

def getAll():
  sum=0
  wallets={}
  for coin in portfolio.keys():
    walletdata = getWallet(coin, portfolio[coin])
    sum += walletdata["val"]
    wallets[coin] = walletdata
  outputCSV(wallets)
  outputScroller(wallets,sum)

getAll()
