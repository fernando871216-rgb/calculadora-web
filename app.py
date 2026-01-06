from flask import Flask, render_template, request, redirect
from reportlab.pdfgen import canvas
from flask import session
from reportlab.lib.pagesizes import letter
from flask import send_file
import io
import os
import mercadopago

app.secret_key = "INIFER"
app = Flask(__name__)

TASA_CETES = 10.0  # % anual, editable

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))



def interes_compuesto_tabla(capital, mensual, tasa, años):
    tabla = []
    total = capital
    tasa = tasa / 100

    for año in range(1, años + 1):
        total += mensual * 12
        total *= (1 + tasa)
        tabla.append({
            "año": año,
            "total": total
        })

    return total, tabla

def inversion_cetes(capital, tasa, años):
    tabla = []
    total = capital
    tasa = tasa / 100

    for año in range(1, años + 1):
        total *= (1 + tasa)
        tabla.append({
            "año": año,
            "total": total
        })

    return total, tabla


@app.route("/pdf")
def generar_pdf():
    es_pro = session.get("es_pro", False)

    capital = 10000
    mensual = 1000
    tasa = 10
    años = 10

    _, tabla = interes_compuesto_tabla(capital, mensual, tasa, años)

    if not es_pro:
        tabla = tabla[:5]

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # =====================
    # PORTADA
    # =====================
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 150, "Simulación de Inversión")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        width / 2,
        height - 200,
        "Reporte financiero personalizado"
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        width / 2,
        height - 240,
        "Generado automáticamente"
    )

    pdf.showPage()

    # =====================
    # RESUMEN
    # =====================
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "Resumen de inversión")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 90, f"Capital inicial: ${capital:,.2f}")
    pdf.drawString(50, height - 110, f"Aportación mensual: ${mensual:,.2f}")
    pdf.drawString(50, height - 130, f"Tasa anual: {tasa}%")
    pdf.drawString(50, height - 150, f"Años simulados: {años}")

    # =====================
    # CETES
    # =====================
    pdf.showPage()

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "Comparación con CETES")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(
        50,
        height - 90,
        f"Tasa CETES usada: {TASA_CETES}% anual"
    )

    y = height - 130

    total_cetes, tabla_cetes = inversion_cetes(capital, TASA_CETES, años)

    if not es_pro:
        tabla_cetes = tabla_cetes[:5]

    for fila in tabla_cetes:
        pdf.drawString(
            50,
            y,
            f"Año {fila['año']}: ${fila['total']:,.2f}"
        )
        y -= 18

    # =====================
    # TABLA PRINCIPAL
    # =====================
    pdf.showPage()

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "Evolución anual")

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, height - 90, "Año")
    pdf.drawString(150, height - 90, "Monto acumulado")

    y = height - 120
    pdf.setFont("Helvetica", 11)

    for fila in tabla:
        pdf.drawString(50, y, str(fila["año"]))
        pdf.drawRightString(300, y, f"${fila['total']:,.2f}")
        y -= 18

        if y < 60:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y = height - 60

    # =====================
    # BLOQUE PRO
    # =====================
    if not es_pro:
        pdf.showPage()

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, height - 100, "Versión gratuita")

        pdf.setFont("Helvetica", 12)
        pdf.drawString(
            50,
            height - 140,
            "Desbloquea la versión PRO para ver el reporte completo,"
        )
        pdf.drawString(
            50,
            height - 160,
            "exportar todos los años y obtener más herramientas."
        )

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="simulacion_inversion_pro.pdf",
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
    status = request.args.get("status")

    if status == "approved":
        session["es_pro"] = True
        return redirect("/")

    return "Pago no aprobado"


@app.route("/fallo")
def fallo():
    return "❌ Pago cancelado."

@app.route("/pendiente")
def pendiente():
    return "⏳ Pago pendiente."



@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    tabla = []
    tabla_visible = []
    tabla_cetes = []
    es_pro = session.get("es_pro", False)

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

        # CETES
        total_cetes, tabla_cetes = inversion_cetes(
            capital, TASA_CETES, años
        )

        if not es_pro:
            tabla_cetes = tabla_cetes[:5]

    return render_template(
        "index.html",
        resultado=resultado,
        tabla=tabla_visible,
        tabla_cetes=tabla_cetes,
        tasa_cetes=TASA_CETES,
        es_pro=es_pro
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)