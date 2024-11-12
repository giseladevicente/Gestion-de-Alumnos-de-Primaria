from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from config import Config
from werkzeug.security import check_password_hash

app = Flask(__name__)

mysql = MySQL()
app.config.from_object(Config)
mysql.init_app(app)  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    # Verificar el usuario en la base de datos
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE username = %s AND role = %s", (username, role))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user['password'], password):  # Verificar la contraseña hashada
        # Redirigir a la página del dashboard correspondiente al rol
        return redirect(url_for('dashboard', role=role))
    else:
        # Si la autenticación falla, redirigir al índice (inicio de sesión)
        return redirect(url_for('index'))

@app.route('/dashboard/<role>')
def dashboard(role):
    # Mostrar contenido diferente dependiendo del rol
    return render_template('dashboard.html', role=role)

if __name__ == '__main__':
    app.run(debug=True)