from flask import Flask, render_template, request, redirect
from reportlab.pdfgen import canvas
from flask import send_file
import io
import os
import mercadopago

app = Flask(__name__)

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

@app.route("/pdf")
def generar_pdf():
    # ⚠️ datos de ejemplo (luego los haremos dinámicos)
    capital = 10000
    mensual = 1000
    tasa = 10
    años = 10

    _, tabla = interes_compuesto_tabla(capital, mensual, tasa, años)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "Simulación de Inversión")

    pdf.setFont("Helvetica", 10)
    y = height - 100

    for fila in tabla:
        texto = f"Año {fila['año']}: ${fila['total']:,.2f}"
        pdf.drawString(50, y, texto)
        y -= 15

        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 50

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="simulacion_inversion.pdf",
        mimetype="application/pdf"
    )

@app.route("/pagar")
def pagar():
    preference_data = {
        "items": [
            {
                "title": "Versión PRO - Calculadora de Inversión",
                "quantity": 1,
                "unit_price": 45.0
            }
        ],
        "back_urls": {
            "success": "/exito",
            "failure": "/fallo",
            "pending": "/pendiente"
        },
        "auto_return": "approved"
    }

    preference = sdk.preference().create(preference_data)
    return redirect(preference["response"]["init_point"])

@app.route("/exito")
def exito():
    return "✅ Pago aprobado. Aquí activaremos PRO."

@app.route("/fallo")
def fallo():
    return "❌ Pago cancelado."

@app.route("/pendiente")
def pendiente():
    return "⏳ Pago pendiente."

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
    tabla_visible = []
    es_pro = False   # por ahora todos son gratis

    if request.method == "POST":
        capital = float(request.form["capital"])
        mensual = float(request.form["mensual"])
        tasa = float(request.form["tasa"])
        años = int(request.form["años"])

        resultado, tabla = interes_compuesto_tabla(
            capital, mensual, tasa, años
        )

        # 🔒 LÍMITE GRATIS: solo 5 años
        tabla_visible = tabla[:5]

    return render_template(
        "index.html",
        resultado=resultado,
        tabla=tabla_visible,
        es_pro=es_pro
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)