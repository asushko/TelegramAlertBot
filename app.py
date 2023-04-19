import atexit
import os
import random
import redis
import requests
import telepot
import time
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

REDIS_HASH_KEY = 'stock_data'

word_list = [(277, 'MSFT', 193, None, False, False), (100, 'AMZN', 104.2, None, False, False)]
apikeys_list = ['34d3f176e718e216ee8560a150cb0000', '0c471a777f91b810299e5e3981522450','c487c7f54a0fdefa58f92596372acaf7',
                'ba46d09d77ac077b7bcbeab874df2ab5', '313e40cba8245e1accc76a64d3c241ac']

# apikeys_list = []
REDIS_CONNECTION_URL = os.getenv('REDIS_URL')
telegram_token = os.getenv('TELEG_TOCKEN')
refreshDelay = int(os.getenv('API_REFRESH', 60))

receiver_id = 729835175

# Connection string

# Connect to the Redis server using the connection string
redis_connection = redis.StrictRedis.from_url(REDIS_CONNECTION_URL, decode_responses=True)
# Store initial data in Redis hash
for low, word, high, price, alertLow, alertHigh in word_list:
    redis_connection.hset(REDIS_HASH_KEY, word, str((low, high, price, alertLow, alertHigh)))


def sendMessage(text):
    bot = telepot.Bot(telegram_token)
    bot.sendMessage(receiver_id,text)

def get_ticker_data(word):
    api_key = random.choice(apikeys_list)
    url = f"https://financialmodelingprep.com/api/v3/quote-short/{word}?apikey={api_key}"
    print("Getting ticker data from URL:", url)
    response = requests.get(url)
    data = response.json()
    if data and isinstance(data, list) and len(data) > 0 and 'price' in data[0]:
        return data[0]['price']  # Return the price instead of updating word_list
    else:
        print("API key is over:", api_key)
        time.sleep(2)
        return get_ticker_data(word)


def update_ticker_prices():
    stock_data = redis_connection.hgetall(REDIS_HASH_KEY)

    for word, data_str in stock_data.items():
        low, high, price, alertLow, alertHigh = eval(data_str)
        new_price = get_ticker_data(word)

        if new_price is not None:
            if not alertLow and new_price <= low:
                sendMessage(f"{word} cross low {low} \n and now is {new_price}")
                alertLow = True
            elif not alertHigh and new_price >= high:
                sendMessage(f"{word} cross high {high} \n and now is {new_price}")
                alertHigh = True

            # Update the data in the Redis hash
            redis_connection.hset(REDIS_HASH_KEY, word, str((low, high, new_price, alertLow, alertHigh)))

update_ticker_prices()
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_ticker_prices, trigger="interval", seconds= refreshDelay)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

@app.context_processor
def inject_ticker_data():

    ticker_data = {}
    stock_data = redis_connection.hgetall(REDIS_HASH_KEY)

    for word, data_str in stock_data.items():
        low, high, price, alertLow, alertHigh = eval(data_str)
        ticker_data[word] = price
    return {'ticker_data': ticker_data}

@app.route('/')
def index():
    stock_data = redis_connection.hgetall(REDIS_HASH_KEY)
    word_list = []

    for word, data_str in stock_data.items():
        low, high, price, alertLow, alertHigh = eval(data_str)
        word_list.append((low, word, high, price, alertLow, alertHigh))

    return render_template('index.html', word_list=word_list)

@app.route('/add_word', methods=['POST'])
def add_word():
    word = request.form['word']
    low = float(request.form['low'])
    high = float(request.form['high'])
    redis_connection.hset(REDIS_HASH_KEY, word, str((low, high, None, False, False)))
    return redirect('/')

@app.route('/remove_word', methods=['POST'])
def remove_word():
    word = request.form['word']
    redis_connection.hdel(REDIS_HASH_KEY, word)
    return redirect('/')

if __name__ == '__main__':
    app.run()
