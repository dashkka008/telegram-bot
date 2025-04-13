from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

bookings = [
    {"id": 1, "user_id": 12345, "workspace_id": 1, "start_time": "2023-10-01 09:00:00", "end_time": "2023-10-01 12:00:00", "status": "active"},
    {"id": 2, "user_id": 67890, "workspace_id": 2, "start_time": "2023-10-01 13:00:00", "end_time": "2023-10-01 15:00:00", "status": "completed"},
]

@app.route("/")
def admin_panel():
    return render_template("admin.html", bookings=bookings)

@app.route("/filter", methods=["POST"])
def filter_bookings():
    status = request.form.get("status")
    filtered = [b for b in bookings if b["status"] == status] if status else bookings
    return render_template("admin.html", bookings=filtered)
@app.route("/delete/<int:booking_id>")
def delete_booking(booking_id):
    global bookings
    bookings = [b for b in bookings if b["id"] != booking_id]
    return redirect(url_for("admin_panel"))

@app.route("/export_excel")
def export_excel():
    df = pd.DataFrame(bookings)
    excel_file = "bookings_report.xlsx"
    df.to_excel(excel_file, index=False, engine="openpyxl")
    return send_file(excel_file, as_attachment=True)

@app.route("/export_pdf")
def export_pdf():
    pdf_file = "bookings_report.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    c.drawString(100, 750, "Отчет по бронированиям:")
    y_position = 730
    for booking in bookings:
        c.drawString(100, y_position, f"ID: {booking['id']}, Место: {booking['workspace_id']}, Время: {booking['start_time']} - {booking['end_time']}, Статус: {booking['status']}")
        y_position -= 20
    c.save()
    return send_file(pdf_file, as_attachment=True)


@app.route("/report")
def generate_report():
    df = pd.DataFrame(bookings)
    if not df.empty:
        df["start_time"] = pd.to_datetime(df["start_time"])
        df["day"] = df["start_time"].dt.date
        daily_load = df.groupby("day").size()

        plt.figure(figsize=(10, 5))
        daily_load.plot(kind="bar", color="skyblue")
        plt.title("Загрузка офиса за неделю")
        plt.xlabel("Дата")
        plt.ylabel("Количество бронирований")

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close()
    else:
        image_base64 = None

    return render_template("report.html", chart=image_base64)

if __name__ == "__main__":
    app.run(debug=True)