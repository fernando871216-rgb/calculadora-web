from flask import Flask, render_template, request
import os

app = Flask(__name__)

def interes_compuesto_tabla(capital, mensual, tasa_anual, años):
    tasa_mensual = tasa_anual / 12 / 100
    total = capital
    tabla = []

    for año in range(1, años + 1):
        for _ in range(12):
            total = total * (1 + tasa_mensual) + mensual
        tabla.append({
            "año": año,
            "total": round(total, 2)
        })

    return round(total, 2), tabla

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    tabla = []

    if request.method == "POST":
        capital = float(request.form["capital"])
        mensual = float(request.form["mensual"])
        tasa = float(request.form["tasa"])
        años = int(request.form["años"])

        resultado, tabla = interes_compuesto_tabla(
            capital, mensual, tasa, años
        )

    return render_template(
        "index.html",
        resultado=resultado,
        tabla=tabla
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)