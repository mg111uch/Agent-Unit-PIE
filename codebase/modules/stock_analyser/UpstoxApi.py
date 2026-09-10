import requests

nifty_key = 'NSE_INDEX%7CNifty%2050'
interval = '30minute'
to_date = '2026-09-10'
from_date = '2026-09-10'
# url = 'https://api.upstox.com/v2/historical-candle/'+nifty_key+'/'+interval+'/'+to_date+'/'+from_date
url = 'https://api.upstox.com/v2/historical-candle/intraday/'+nifty_key+'/'+interval
headers = {
    'Accept': 'application/json'
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    dataDump = response.json()
    candles = dataDump['data']['candles']
    print(candles)
else:
    print(f"Error: {response.status_code} - {response.text}")