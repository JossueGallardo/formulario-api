from flask import Flask, request, jsonify, session, redirect, url_for, send_file, Response
from flask_cors import CORS
from datetime import datetime
import os
import sqlite3
import csv
import io

app = Flask(__name__)
app.secret_key = "secreto_super_seguro_2025"
CORS(app, resources={r"/contact": {"origins": "https://distriibuidorayd.netlify.app"}})

# ---------- Inicializar base de datos SQLite ----------
def init_db():
    conn = sqlite3.connect('mensajes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            asunto TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------- Ruta para recibir datos del formulario ----------
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
        with open("mensajes_contacto.txt", "a", encoding="utf-8") as f:
            f.write(f"{fecha} | {nombre} | {correo} | {asunto} | {mensaje}\n")

        conn = sqlite3.connect('mensajes.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO mensajes (nombre, correo, asunto, mensaje, fecha)
            VALUES (?, ?, ?, ?, ?)
        ''', (nombre, correo, asunto, mensaje, fecha))
        conn.commit()
        conn.close()

        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------- Login protegido ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        clave = request.form.get('clave')
        if clave == 'admin123':
            session['logueado'] = True
            return redirect(url_for('ver_mensajes'))
        else:
            return '<h3>Clave incorrecta</h3><a href="/login">Intentar de nuevo</a>'
    return '''
        <form method="POST">
            <h2>Ingreso protegido</h2>
            <label>Clave de acceso:</label><br>
            <input type="password" name="clave"><br><br>
            <button type="submit">Entrar</button>
        </form>
    '''

# ---------- Visualizar mensajes desde la base de datos ----------
@app.route('/ver-mensajes')
def ver_mensajes():
    if not session.get('logueado'):
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect('mensajes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT fecha, nombre, correo, asunto, mensaje FROM mensajes ORDER BY id DESC')
        mensajes = cursor.fetchall()
        conn.close()

        html = "<h3>Mensajes recibidos:</h3><ul>"
        for fecha, nombre, correo, asunto, mensaje in mensajes:
            html += f"""
            <li>
                <strong>Hora:</strong> {fecha}<br>
                <strong>Nombre:</strong> {nombre}<br>
                <strong>Correo:</strong> {correo}<br>
                <strong>Asunto:</strong> {asunto}<br>
                <strong>Mensaje:</strong><br>{mensaje}
            </li><hr>
            """
        html += "</ul>"
        html += '''
            <a href="/descargar-mensajes"><button>📥 Descargar mensajes (TXT)</button></a>
            <a href="/descargar-sql"><button>📄 Descargar mensajes (SQL - CSV)</button></a><br><br>
            <a href="/logout">Cerrar sesión</a>
        '''
        return html

    except Exception as e:
        return f"Error: {e}", 500

# ---------- Descargar archivo de respaldo (txt) ----------
@app.route('/descargar-mensajes')
def descargar_mensajes():
    if not session.get('logueado'):
        return redirect(url_for('login'))

    filepath = "mensajes_contacto.txt"
    if not os.path.exists(filepath):
        return "Archivo no encontrado.", 404
    return send_file(filepath, as_attachment=True)

# ---------- Descargar mensajes desde SQLite como CSV ----------
@app.route('/descargar-sql')
def descargar_sql():
    if not session.get('logueado'):
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect('mensajes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT fecha, nombre, correo, asunto, mensaje FROM mensajes ORDER BY id DESC')
        mensajes = cursor.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Fecha', 'Nombre', 'Correo', 'Asunto', 'Mensaje'])
        writer.writerows(mensajes)
        output.seek(0)

        return Response(output, mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=mensajes_sql.csv'})

    except Exception as e:
        return f"Error al generar CSV: {e}", 500

# ---------- Cerrar sesión ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- Ejecutar aplicación ----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
