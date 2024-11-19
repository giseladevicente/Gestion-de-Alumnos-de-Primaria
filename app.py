from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from config import Config
from werkzeug.security import check_password_hash, generate_password_hash
from MySQLdb.cursors import DictCursor
import re # Validar correos electrónicos


app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL()
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

        # Validaciones
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, correo_electronico):
            return render_template('register.html', error="El correo electrónico no tiene un formato válido.")

        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
            return render_template('register.html', error="La contraseña debe tener al menos 8 caracteres, incluyendo letras y números.")
        
        try:
            # Verificación correo electrónico
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM usuarios WHERE correo_electronico = %s", (correo_electronico,))
            if cur.fetchone():
                cur.close()
                return "Correo electrónico ya registrado", 400
        # else:
            # Crear usuario
            hashed_password = generate_password_hash(password) # Se encripta la contraseña
            cur.execute("INSERT INTO usuarios (nombre_completo, correo_electronico, contraseña, rol) VALUES (%s, %s, %s, %s)", 
                        (nombre_completo, correo_electronico, hashed_password, role))
            mysql.connection.commit()
            
            # ID del usuario registrado
            cur.execute("SELECT id FROM usuarios WHERE correo_electronico = %s", (correo_electronico,))
            user_id = cur.fetchone()[0] # ID del usuario

            # Alumno en tabla perfiles_alumno 
            if role == 'alumno':
                cur.execute("INSERT INTO perfiles_alumnos (alumno_id, nombre_completo) VALUES (%s, %s)", 
                            (user_id, nombre_completo))
                mysql.connection.commit()
            
            cur.close()
            
            # return redirect(url_for('index'))
            return render_template('success.html', mensaje="Registro exitoso. Ahora puedes iniciar sesión.")

        except Exception as e:
            return render_template('register.html', error="Ocurrió un error al registrar el usuario. Intenta nuevamente.")
        
        finally:
            cur.close()


    return render_template('register.html')


# Inicio de Sesión - index.html
@app.route('/login', methods=['POST'])
def login():
    correo = request.form['email']
    password = request.form['password']
    rol_ingresado = request.form['role'] 

    # Verificación del usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE correo_electronico = %s", (correo,))
    user = cur.fetchone()
    cur.close()

    # Validaciones
    if not user:
        error = "El correo ingresado no está registrado."
        return render_template('index.html', error=error)

    if not check_password_hash(user[3], password):
        error = "La contraseña es incorrecta."
        return render_template('index.html', error=error)
    
    if user[4] != rol_ingresado:
        error = "El rol ingresado no coincide con el registrado."
        return render_template('index.html', error=error)
    
     # Inicio de sesión exitoso
    session['user_id'] = user[0]
    session['nombre_completo'] = user[1]
    session['role'] = user[4]
    return redirect(url_for('dashboard'))


# Contenido según rol - dashboard.html
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    role = session.get('role')
    nombre_completo = session.get('nombre_completo')
    
    return render_template('dashboard.html', role=role, nombre_completo=nombre_completo)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ALUMNOS
@app.route('/lista_alumnos')
def lista_alumnos():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.nombre_completo
        FROM perfiles_alumnos pa
        JOIN usuarios u ON pa.alumno_id = u.id
    """)
    alumnos = cur.fetchall()
    cur.close()
    return render_template('lista_alumnos.html', alumnos=alumnos)


# TAREAS
@app.route('/crear_tarea', methods=['GET', 'POST'])
def crear_tarea():
    if 'user_id' not in session or session.get('role') != 'docente':
        return redirect(url_for('index'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_entrega = request.form['fecha_entrega']
        archivo_adjunto = request.files['archivo_adjunto']

        # Archivo adjunto
        archivo_nombre = None
        if archivo_adjunto:
            archivo_nombre = archivo_adjunto.filename
            archivo_adjunto.save(f"uploads/{archivo_nombre}")

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tareas_examenes (docente_id, titulo, descripcion, fecha_entrega, archivo_adjunto) "
                    "VALUES (%s, %s, %s, %s, %s)", 
                    (session['user_id'], titulo, descripcion, fecha_entrega, archivo_nombre))
        
        mysql.connection.commit()
        cur.close()

        tarea_id = cur.lastrowid  # Obtener el ID de la tarea recién insertada

        # Obtener todos los alumnos (usuarios con rol 'alumno')
        cur.execute("SELECT id FROM perfiles_alumnos")
        alumnos = cur.fetchall()
       
        # Asignar la tarea a todos los alumnos
        for alumno in alumnos:
            cur.execute("""
                INSERT INTO tareas_alumnos (tarea_id, alumno_id) 
                VALUES (%s, %s)
            """, (tarea_id, alumno['id'], 'Pendiente')) # El estado inicial es "Pendiente")
        
        mysql.connection.commit()
        cur.close()


        return redirect(url_for('lista_tareas'))  # Redirigir a la lista de tareas

    return render_template('crear_tarea.html')


@app.route('/lista_tareas')
def lista_tareas():
    if 'user_id' not in session or session.get('role') != 'docente':
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, titulo, descripcion, fecha_entrega, archivo_adjunto FROM tareas_examenes WHERE docente_id = %s", 
                (session['user_id'],))
    tareas = cur.fetchall()
    cur.close()

    return render_template('lista_tareas.html', tareas=tareas)


# COMUNICADOS
@app.route('/crear_comunicado', methods=['GET', 'POST'])
def crear_comunicado():
    if 'user_id' not in session or session.get('role') != 'docente':
        return redirect(url_for('index'))  

    mensaje = None  # variable que almacena mensaje de éxito

    if request.method == 'POST':  
        contenido = request.form['contenido']  

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO comunicados (docente_id, tipo_comunicado, contenido) VALUES (%s, %s, %s)",
            (session['user_id'], 'general', contenido)
        )
        mysql.connection.commit()  
        cur.close()

        mensaje = "Comunicado general creado exitosamente."
        
        return redirect(url_for('lista_comunicados', mensaje=mensaje))

    return render_template('crear_comunicado.html', mensaje=mensaje)  


@app.route('/comunicados')
def lista_comunicados():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    mensaje = request.args.get('mensaje')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.id, c.contenido, c.fecha_envio, c.tipo_comunicado,
        (SELECT JSON_ARRAYAGG(JSON_OBJECT('respuesta', r.respuesta, 'remitente', u.nombre_completo, 'fecha', r.fecha_respuesta))
         FROM respuestas_comunicados r
         JOIN usuarios u ON r.remitente_id = u.id
         WHERE r.comunicado_id = c.id) AS respuestas
        FROM comunicados c
        ORDER BY c.fecha_envio DESC
    """)
    comunicados = cur.fetchall()
    cur.close()

    comunicados_format = [
        (row[0], row[1], row[2], row[3], eval(row[4]) if row[4] else None)
        for row in comunicados
    ]

    return render_template('lista_comunicados.html', comunicados=comunicados_format, mensaje=mensaje)


# COMUNICADOS PERSONALIZADOS
@app.route('/crear_comunicado_personalizado', methods=['GET', 'POST'])
def crear_comunicado_personalizado():
    if 'user_id' not in session or session.get('role') != 'docente':
        return redirect(url_for('index'))  

    if request.method == 'POST':  
        destinatario = request.form['destinatario']
        contenido = request.form['contenido']
        tipo_comunicado = request.form['personalizado']

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO comunicados (docente_id, tipo_comunicado, contenido) VALUES (%s, %s, %s)",
            (session['user_id'], tipo_comunicado, contenido)
        )
        comunicado_id = cur.lastrowid  # Obtiene el ID del comunicado recién creado

        cur.execute(
            "INSERT INTO comunicados_destinatarios (comunicado_id, usuario_id) VALUES (%s, %s)",
            (comunicado_id, destinatario)
        )
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('lista_comunicados', mensaje='Comunicado creado con éxito.'))
    
    return render_template('crear_comunicado_personalizado.html')


# PERFIL ALUMNO

### ESTADOS DE TAREAS
@app.route('/tareas_alumno', methods=['GET', 'POST'])
def tareas_alumno():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    alumno_id = session['user_id']

    # Actualización de estados de tareas
    if request.method == 'POST':
        cur = mysql.connection.cursor(DictCursor)
        for key, value in request.form.items():
            if key.startswith("estado_"):
                tarea_id = int(key.split("_")[1])

                cur.execute("""
                    SELECT id FROM tareas_alumnos
                    WHERE alumno_id = %s AND tarea_id = %s
                """, (alumno_id, tarea_id))
                resultado = cur.fetchone()

                if resultado:
                    cur.execute("""
                        UPDATE tareas_alumnos
                        SET estado = %s
                        WHERE id = %s
                    """, (value, resultado['id']))
                else:
                    cur.execute("""
                        INSERT INTO tareas_alumnos (tarea_id, alumno_id, estado)
                        VALUES (%s, %s, %s)
                    """, (tarea_id, alumno_id, value))

        mysql.connection.commit()
        cur.close()
        return redirect(url_for('tareas_alumno'))

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        INSERT INTO tareas_alumnos (tarea_id, alumno_id, estado)
        SELECT te.id, %s, 'pendiente'
        FROM tareas_examenes te
        LEFT JOIN tareas_alumnos ta ON te.id = ta.tarea_id AND ta.alumno_id = %s
        WHERE ta.id IS NULL
    """, (alumno_id, alumno_id))
    mysql.connection.commit()

    # Consultar tareas con sus estados
    cur.execute("""
        SELECT te.id AS tarea_id, 
               te.titulo, 
               te.descripcion, 
               te.fecha_entrega,
               COALESCE(ta.estado, 'pendiente') AS estado
        FROM tareas_examenes te
        LEFT JOIN tareas_alumnos ta 
        ON te.id = ta.tarea_id AND ta.alumno_id = %s
    """, (alumno_id,))
    tareas = cur.fetchall()
    cur.close()

    return render_template('tareas_alumno.html', tareas=tareas, nombre_completo=session['nombre_completo'])


### RESPONDER COMUNICADOS
@app.route('/responder_comunicado/<int:comunicado_id>', methods=['POST'])
def responder_comunicado(comunicado_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    respuesta = request.form['respuesta']
    if not respuesta:
        return redirect(url_for('lista_comunicados', mensaje='La respuesta no puede estar vacía.'))

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO respuestas_comunicados (comunicado_id, remitente_id, respuesta) VALUES (%s, %s, %s)",
        (comunicado_id, session['user_id'], respuesta)
    )
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('lista_comunicados', mensaje='Respuesta enviada con éxito.'))



if __name__ == '__main__':
    app.run(debug=True)
