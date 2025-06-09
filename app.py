from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)

# Solo permite el origen de Netlify (ajusta si cambias de dominio)
CORS(app, resources={r"/contact": {"origins": "https://distriibuidorayd.netlify.app"}})

@app.route('/contact', methods=['POST'])
def contact():
    nombre = request.form.get('name')
    correo = request.form.get('email')
    asunto = request.form.get('subject')
    mensaje = request.form.get('message')
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not all([nombre, correo, asunto, mensaje]):
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    try:
        # Crear archivo si no existe y guardar el mensaje
        with open("mensajes_contacto.txt", "a", encoding="utf-8") as f:
            f.write(f"{fecha} | {nombre} | {correo} | {asunto} | {mensaje}\n")

        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Este bloque es solo para pruebas locales. Render usará gunicorn.
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
