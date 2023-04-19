from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import atexit

app = Flask(__name__)

def log_time():
    current_time = datetime.datetime.now()
    print(f'Current time: {current_time}')

scheduler = BackgroundScheduler()
scheduler.add_job(func=log_time, trigger="interval", seconds=1)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run()
