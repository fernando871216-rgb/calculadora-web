from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "MI WEB YA FUNCIONA EN INTERNET 🚀"

if __name__ == "__main__":
    app.run()