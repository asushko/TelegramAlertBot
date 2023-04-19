from flask import Flask, render_template, request, redirect
import requests, random, os, time
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import atexit
import telepot

app = Flask(__name__)

word_list = [(160, 'AAPL', 162, None, False, False), (104, 'AMZN', 105, None, False, False)]
# apikeys_list = ['0c471a777f91b810299e5e3981522450','c487c7f54a0fdefa58f92596372acaf7',
#                 'ba46d09d77ac077b7bcbeab874df2ab5', '313e40cba8245e1accc76a64d3c241ac']

apikeys_list = ['34d3f176e718e216ee8560a150cb0000']
telegram_token  = os.getenv('TELEG_TOCKEN')
refreshDelay  = int(os.getenv('API_REFRESH', 60))
receiver_id = 729835175

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
    print(word_list)
    for i, (low, word, high, price, alertLow, alertHigh) in enumerate(word_list):
        new_price = get_ticker_data(word)
        if new_price is not None:
            if not alertLow and new_price <= low:
                sendMessage(f"{word} cross low {low} \n and now is {new_price}")
                word_list[i] = (low, word, high, new_price, True, alertHigh)
            elif not alertHigh and new_price >= high:
                sendMessage(f"{word} cross high {high} \n and now is {new_price}")
                word_list[i] = (low, word, high, new_price, alertLow, True)
            else:
                word_list[i] = (low, word, high, new_price, alertLow, alertHigh)


scheduler = BackgroundScheduler()
scheduler.add_job(func=update_ticker_prices, trigger="interval", seconds= refreshDelay)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# @app.context_processor
def inject_ticker_data():
    if request.path == '/':
        return {}
    ticker_data = {}
    for low, word, high, price in word_list:
        if not price:
            price = get_ticker_data(word)
            for i, (low, w, high, _) in enumerate(word_list):
                if w == word:
                    word_list[i] = (low, w, high, price)
        ticker_data[word] = price
    return {'ticker_data': ticker_data}

@app.route('/')
def index():
    return render_template('index.html', word_list=word_list)

@app.route('/add_word', methods=['POST'])
def add_word():
    word = request.form['word']
    low = float(request.form['low'])
    high = float(request.form['high'])
    word_list.append((low, word, high, None, False, False))
    return redirect('/')

@app.route('/remove_word', methods=['POST'])
def remove_word():
    word = request.form['word']
    for i, (low, w, high, price, alertLow, alertHigh) in enumerate(word_list):
        if w == word:
            word_list.pop(i)
            break
    return redirect('/')

if __name__ == '__main__':
    app.run()
