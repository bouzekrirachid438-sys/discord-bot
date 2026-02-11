from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    return "Karys Shop Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    keep_alive()
    print("Keep-alive server started!")
