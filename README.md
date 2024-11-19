# Proyecto Sistema de Gestión de Alumnos de Primaria

Este proyecto es una aplicación web desarrollada en Flask que gestiona el registro, asignación de tareas y comunicación entre docentes, alumnos y padres. Está diseñado para facilitar la interacción entre los usuarios, de acuerdo con sus roles, y mejorar la organización del trabajo escolar.

## Instrucciones para Ejecutar el Proyecto

1. Clonar el repositorio:

```bash
   git clone https://github.com/giseladevicente/Gestion-de-Alumnos-de-Primaria.git
```

2. Crear y activar entorno virtual:

```bash
python -m venv venv

# En Windows:
source venv\Scripts\activate

# En macOS/Linux:
source venv/bin/activate
```

3. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicación:

```bash
python app.py
```

## USUARIOS DE PRUEBA:

Todos los Usuarios utilizan el password **prueba123**

**ALUMNOS:**

- Mariano Perez - mperez@gmail.com
- Juan Ruiz - jruiz@gmail.com

**DOCENTE:**

- Florencia Ortiz - florortiz@gmail.com
- Flavia Ortega - fortega@gmail.com

**PADRE:**

- Maria Sanchez - msanchez@gmail.com
- Marcelo Figueroa - mfigueroa@gmail.com

## Tablas utilizadas en la Base de Datos (Workbrench)

```sql
CREATE TABLE IF NOT EXISTS usuarios (
id INT AUTO_INCREMENT PRIMARY KEY,
nombre_completo VARCHAR(255) NOT NULL,
correo_electronico VARCHAR(255) UNIQUE NOT NULL,
contraseña VARCHAR(255) NOT NULL,
rol ENUM('docente', 'alumno', 'padre') NOT NULL,
fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE perfiles_alumnos (
id INT AUTO_INCREMENT PRIMARY KEY,
alumno_id INT NOT NULL,
nombre_completo VARCHAR(255),
FOREIGN KEY (alumno_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE perfiles_padres (
id INT AUTO_INCREMENT PRIMARY KEY,
padre_id INT NOT NULL,
nombre_completo VARCHAR(255),
FOREIGN KEY (padre_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS relacion_padre_hijo (
id INT AUTO_INCREMENT PRIMARY KEY,
padre_id INT NOT NULL,
hijo_id INT NOT NULL,
FOREIGN KEY (padre_id) REFERENCES usuarios(id) ON DELETE CASCADE,
FOREIGN KEY (hijo_id) REFERENCES usuarios(id) ON DELETE CASCADE,
UNIQUE (padre_id, hijo_id)
);

CREATE TABLE tareas_examenes (
id INT AUTO_INCREMENT PRIMARY KEY,
docente_id INT NOT NULL,
titulo VARCHAR(255) NOT NULL,
descripcion TEXT,
fecha_entrega DATE NOT NULL,
archivo_adjunto VARCHAR(255),
FOREIGN KEY (docente_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE comunicados (
id INT AUTO_INCREMENT PRIMARY KEY,
docente_id INT NOT NULL,
tipo_comunicado ENUM('general', 'personalizado') NOT NULL,
contenido TEXT NOT NULL,
fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (docente_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE respuestas_comunicados (
id INT AUTO_INCREMENT PRIMARY KEY,
comunicado_id INT NOT NULL,
remitente_id INT NOT NULL,
respuesta TEXT NOT NULL,
fecha_respuesta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (comunicado_id) REFERENCES comunicados(id) ON DELETE CASCADE,
FOREIGN KEY (remitente_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE comunicados_destinatarios (
id INT AUTO_INCREMENT PRIMARY KEY,
comunicado_id INT NOT NULL,
usuario_id INT NOT NULL,
leido BOOLEAN DEFAULT FALSE,
FOREIGN KEY (comunicado_id) REFERENCES comunicados(id) ON DELETE CASCADE,
FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE tareas_alumnos (
id INT AUTO_INCREMENT PRIMARY KEY,
tarea_id INT NOT NULL,
alumno_id INT NOT NULL,
estado ENUM('pendiente', 'completada') DEFAULT 'pendiente',
FOREIGN KEY (tarea_id) REFERENCES tareas_examenes(id) ON DELETE CASCADE,
FOREIGN KEY (alumno_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
```
