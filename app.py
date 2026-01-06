from flask import Flask, render_template, request
import os

app = Flask(__name__)

def interes_compuesto(capital, mensual, tasa_anual, años):
    tasa_mensual = tasa_anual / 12 / 100
    meses = años * 12
    total = capital

    for _ in range(meses):
        total = total * (1 + tasa_mensual) + mensual

    return round(total, 2)

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None

    if request.method == "POST":
        capital = float(request.form["capital"])
        mensual = float(request.form["mensual"])
        tasa = float(request.form["tasa"])
        años = int(request.form["años"])

        resultado = interes_compuesto(capital, mensual, tasa, años)

    return render_template("index.html", resultado=resultado)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)