import requests

def get_crypto_price(crypto_symbol):
    url = "https://openexchangerates.org/api/latest.json?app_id=84c6243309e84299a2b028f8c55d21d8"
    response = requests.get(url)
    data = response.json()

    usd_to_usdt = data['rates']['USD']

    if crypto_symbol == "ltc":
        crypto_key = "litecoin"
    elif crypto_symbol == "btc":
        crypto_key = "bitcoin"
    else:
        raise ValueError("Invalid cryptocurrency symbol")

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_key}&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()

    crypto_to_usd = data[crypto_key]['usd']
    crypto_to_usdt = crypto_to_usd * usd_to_usdt

    return crypto_to_usdt
