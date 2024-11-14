from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from config import Config
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

mysql = MySQL()
app.config.from_object(Config)
mysql.init_app(app)  

@app.route('/')
def index():
    return render_template('index.html')

# Registro Nuevo Usuario - register.html
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_completo = request.form['nombre_completo']
        correo_electronico = request.form['correo_electronico']
        password = request.form['password']
        role = request.form['role']
        
        hashed_password = generate_password_hash(password) # Se encripta la contraseña

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuarios (nombre_completo, correo_electronico, contraseña, rol) VALUES (%s, %s, %s, %s)", 
                    (nombre_completo, correo_electronico, hashed_password, role))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('index'))

    return render_template('register.html')


# Inicio de Sesión - index.html
@app.route('/login', methods=['POST'])
def login():
    correo = request.form['email']  
    password = request.form['password']
    role = request.form['role']

    # Verificar el usuario en la base de datos
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE correo_electronico = %s AND rol = %s", (correo, role))  # Aquí cambiamos 'username' por 'correo_electronico'
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[3], password):  # Usar el índice para la contraseña (tercer campo de la consulta)
        return redirect(url_for('dashboard', role=role))
    else:
        return redirect(url_for('index'))   


# Contenido según rol
@app.route('/dashboard/<role>')
def dashboard(role):
    return render_template('dashboard.html', role=role) 


@app.route('/add', methods=['POST'])
def add():
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    edad = request.form['edad']
    curso = request.form['curso']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO alumnos (nombre, apellido, edad, curso) VALUES (%s, %s, %s, %s)", (nombre, apellido, edad, curso))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)