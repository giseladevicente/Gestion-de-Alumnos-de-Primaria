from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from config import Config
from werkzeug.security import check_password_hash, generate_password_hash
from MySQLdb.cursors import DictCursor
from datetime import datetime
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
        hijo_id = request.form.get('hijo_id') 

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
            
            # Crear usuario
            hashed_password = generate_password_hash(password) # Se encripta la contraseña
            cur.execute("INSERT INTO usuarios (nombre_completo, correo_electronico, contraseña, rol) VALUES (%s, %s, %s, %s)", 
                        (nombre_completo, correo_electronico, hashed_password, role))
            mysql.connection.commit()
            
            # ID del usuario registrado
            cur.execute("SELECT id FROM usuarios WHERE correo_electronico = %s", (correo_electronico,))
            user_id = cur.fetchone()[0] # ID del usuario

            # Alumno en perfiles_alumnos
            if role == 'alumno':
                cur.execute("INSERT INTO perfiles_alumnos (alumno_id, nombre_completo) VALUES (%s, %s)", (user_id, nombre_completo))
                mysql.connection.commit()

            # Relación Padre-Hijo
            if role == 'padre':
                if not hijo_id:
                    return render_template('register.html', error="Debes seleccionar un alumno para asociarlo con el padre.")
                
                cur.execute("INSERT INTO relacion_padre_hijo (padre_id, hijo_id) VALUES (%s, %s)", 
                                (user_id, hijo_id))
                mysql.connection.commit()
            
            cur.close()

            return render_template('success.html', mensaje="Registro exitoso. Ahora puedes iniciar sesión.")

        except Exception as e:
            return render_template('register.html', error="Ocurrió un error al registrar el usuario. Intenta nuevamente.")

    # Lista de alumnos rol padre
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre_completo FROM usuarios WHERE rol = 'alumno'")
    alumnos = cur.fetchall()  # Lista de tuplas (id, nombre_completo)
    cur.close()

    return render_template('register.html', alumnos=alumnos)


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

        try:
            cur.execute("INSERT INTO tareas_examenes (docente_id, titulo, descripcion, fecha_entrega, archivo_adjunto) "
                        "VALUES (%s, %s, %s, %s, %s)", 
                        (session['user_id'], titulo, descripcion, fecha_entrega, archivo_nombre))
            
            mysql.connection.commit()

            tarea_id = cur.lastrowid  # Obtener el ID de la tarea recién insertada

            # usuarios con rol 'alumno'
            cur.execute("SELECT id FROM perfiles_alumnos")
            alumnos = cur.fetchall()
        
            # Asignar tarea a todos los alumnos
            for alumno in alumnos:
                cur.execute("""
                    INSERT INTO tareas_alumnos (tarea_id, alumno_id) 
                    VALUES (%s, %s)
                """, (tarea_id, alumno['id'], 'Pendiente')) # Estado Inicial = "Pendiente" 
            
            mysql.connection.commit()

            return redirect(url_for('lista_tareas'))
        
        except Exception as e:
            mysql.connection.rollback()
            return render_template('crear_tarea.html', error="Ocurrió un error al crear la tarea. Intenta nuevamente.")

        finally:
            cur.close() 

    return render_template('crear_tarea.html')


@app.route('/lista_tareas')
def lista_tareas():
    if 'user_id' not in session or session.get('role') != 'docente':
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    cur.execute("""SELECT id, titulo, descripcion, fecha_entrega, archivo_adjunto FROM tareas_examenes WHERE docente_id = %s ORDER BY fecha_entrega DESC""", 
                (session['user_id'],))
    tareas = cur.fetchall()
    cur.close()

    fecha_actual = datetime.now().date()

    for tarea in tareas:
        print(tarea)

    return render_template('lista_tareas.html', tareas=tareas, fecha_actual=fecha_actual)




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

    estado = request.args.get('estado', 'todas')
    consulta = """
        SELECT te.id AS tarea_id, 
               te.titulo, 
               te.descripcion, 
               te.fecha_entrega,
               COALESCE(ta.estado, 'pendiente') AS estado
        FROM tareas_examenes te
        LEFT JOIN tareas_alumnos ta 
        ON te.id = ta.tarea_id AND ta.alumno_id = %s
    """

    if estado == 'pendientes':
        consulta += " WHERE COALESCE(ta.estado, 'pendiente') = 'pendiente'"
    elif estado == 'completadas':
        consulta += " WHERE COALESCE(ta.estado, 'pendiente') = 'completada'"
    cur.execute(consulta, (alumno_id,))
    tareas = cur.fetchall()
    cur.close()

    return render_template('tareas_alumno.html', tareas=tareas, nombre_completo=session['nombre_completo'])


# COMUNICADOS

# COMUNICADOS GENERALES
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
        comunicado_id = cur.lastrowid  # ID comunicado recién creado

        cur.execute(
            "INSERT INTO comunicados_destinatarios (comunicado_id, usuario_id) VALUES (%s, %s)",
            (comunicado_id, destinatario)
        )
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('lista_comunicados', mensaje='Comunicado creado con éxito.'))

    # Alumnos y padres para la selección
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre_completo FROM usuarios WHERE rol = 'alumno'")
    alumnos = cur.fetchall()
     
    cur.execute("""
        SELECT p.id, CONCAT(p.nombre_completo, ' (Hijo: ', h.nombre_completo, ')') AS nombre_con_hijo
        FROM usuarios p
        JOIN relacion_padre_hijo rph ON p.id = rph.padre_id
        JOIN usuarios h ON rph.hijo_id = h.id
        WHERE p.rol = 'padre'
    """)
    padres = cur.fetchall()
    cur.close()

    return render_template('crear_comunicado_personalizado.html', alumnos=alumnos, padres=padres)


# LISTA COMUNICADOS 
@app.route('/comunicados')
def lista_comunicados():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    mensaje = request.args.get('mensaje')
    user_id = session['user_id']
    role = session.get('role')

    cur = mysql.connection.cursor()

    if role == 'docente':
        cur.execute("""
SELECT c.id, c.contenido, c.fecha_envio, c.tipo_comunicado,
            (SELECT JSON_ARRAYAGG(JSON_OBJECT('respuesta', r.respuesta, 'remitente', u.nombre_completo, 'fecha', r.fecha_respuesta))
            FROM respuestas_comunicados r
            JOIN usuarios u ON r.remitente_id = u.id
            WHERE r.comunicado_id = c.id) AS respuestas,
            (SELECT GROUP_CONCAT(u.nombre_completo SEPARATOR ', ') 
            FROM comunicados_destinatarios cd 
            JOIN usuarios u ON cd.usuario_id = u.id 
            WHERE cd.comunicado_id = c.id) AS destinatarios
        FROM comunicados c
        LEFT JOIN comunicados_destinatarios cd ON c.id = cd.comunicado_id
        WHERE c.docente_id = %s OR c.tipo_comunicado = 'general' OR cd.usuario_id = %s
        GROUP BY c.id
        ORDER BY c.fecha_envio DESC
        """, (user_id, user_id))
    else:  # Rol alumno u otro
        cur.execute("""
        SELECT c.id, c.contenido, c.fecha_envio, c.tipo_comunicado, 
               MAX(cd.leido) AS leido,  -- Obtenemos el estado 'leído' para el comunicado
               (SELECT JSON_ARRAYAGG(JSON_OBJECT('respuesta', r.respuesta, 'remitente', u.nombre_completo, 'fecha', r.fecha_respuesta))
                FROM respuestas_comunicados r
                JOIN usuarios u ON r.remitente_id = u.id
                WHERE r.comunicado_id = c.id) AS respuestas,
               (SELECT GROUP_CONCAT(u.nombre_completo SEPARATOR ', ') 
                FROM comunicados_destinatarios cd 
                JOIN usuarios u ON cd.usuario_id = u.id 
                WHERE cd.comunicado_id = c.id) AS destinatarios
        FROM comunicados c
        LEFT JOIN comunicados_destinatarios cd ON c.id = cd.comunicado_id
        WHERE c.tipo_comunicado = 'general' OR (c.tipo_comunicado = 'personalizado' AND cd.usuario_id = %s)
        GROUP BY c.id
        ORDER BY c.fecha_envio DESC
        """, (user_id,))


    comunicados = cur.fetchall()
    cur.close()

    comunicados_format = [
        (row[0], row[1], row[2], row[3], row[4] if row[4] is not None else 0, row[5])  # No usamos eval()
        for row in comunicados
    ]

    # print(comunicados)


    return render_template('lista_comunicados.html', comunicados=comunicados_format, mensaje=mensaje)


# COMUNICADOS LEIDOS
@app.route('/marcar_leido/<int:comunicado_id>', methods=['POST'])
def marcar_como_leido(comunicado_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']

    print(f"Comunicado ID: {comunicado_id}, Usuario ID: {user_id}") 

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE comunicados_destinatarios
        SET leido = 1
        WHERE comunicado_id = %s AND usuario_id = %s
    """, (comunicado_id, user_id))
    
    mysql.connection.commit()
    cur.close()

    print("Comunicado marcado como leído.") 

    return redirect(url_for('lista_comunicados'))


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
