CREATE DATABASE `gestion_alumnos` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;


-- Tabla de comunicados enviados por docentes
CREATE TABLE `comunicados` (
  `id` int NOT NULL AUTO_INCREMENT,
  `docente_id` int NOT NULL,
  `tipo_comunicado` enum('general','personalizado') NOT NULL,
  `contenido` text NOT NULL,
  `fecha_envio` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `docente_id` (`docente_id`),
  CONSTRAINT `comunicados_ibfk_1` FOREIGN KEY (`docente_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- Relación entre comunicados y destinatarios
CREATE TABLE `comunicados_destinatarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `comunicado_id` int NOT NULL,
  `usuario_id` int NOT NULL,
  `leido` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `comunicado_id` (`comunicado_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `comunicados_destinatarios_ibfk_1` FOREIGN KEY (`comunicado_id`) REFERENCES `comunicados` (`id`) ON DELETE CASCADE,
  CONSTRAINT `comunicados_destinatarios_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- Tabla de perfiles de alumnos
CREATE TABLE `perfiles_alumnos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `alumno_id` int NOT NULL,
  `nombre_completo` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `alumno_id` (`alumno_id`),
  CONSTRAINT `perfiles_alumnos_ibfk_1` FOREIGN KEY (`alumno_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- Tabla de perfiles de padres
CREATE TABLE `perfiles_padres` (
  `id` int NOT NULL AUTO_INCREMENT,
  `padre_id` int NOT NULL,
  `nombre_completo` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `padre_id` (`padre_id`),
  CONSTRAINT `perfiles_padres_ibfk_1` FOREIGN KEY (`padre_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- Relación entre padres e hijos
CREATE TABLE `relacion_padre_hijo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `padre_id` int NOT NULL,
  `hijo_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `padre_id` (`padre_id`,`hijo_id`),
  KEY `hijo_id` (`hijo_id`),
  CONSTRAINT `relacion_padre_hijo_ibfk_1` FOREIGN KEY (`padre_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `relacion_padre_hijo_ibfk_2` FOREIGN KEY (`hijo_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- Respuestas a los comunicados
CREATE TABLE `respuestas_comunicados` (
  `id` int NOT NULL AUTO_INCREMENT,
  `comunicado_id` int NOT NULL,
  `remitente_id` int NOT NULL,
  `respuesta` text NOT NULL,
  `fecha_respuesta` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `comunicado_id` (`comunicado_id`),
  KEY `remitente_id` (`remitente_id`),
  CONSTRAINT `respuestas_comunicados_ibfk_1` FOREIGN KEY (`comunicado_id`) REFERENCES `comunicados` (`id`) ON DELETE CASCADE,
  CONSTRAINT `respuestas_comunicados_ibfk_2` FOREIGN KEY (`remitente_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- Tabla que vincula a los alumnos con sus tareas
CREATE TABLE `tareas_alumnos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tarea_id` int NOT NULL,
  `alumno_id` int NOT NULL,
  `estado` enum('pendiente','completada') DEFAULT 'pendiente',
  PRIMARY KEY (`id`),
  KEY `tarea_id` (`tarea_id`),
  KEY `alumno_id` (`alumno_id`),
  CONSTRAINT `tareas_alumnos_ibfk_1` FOREIGN KEY (`tarea_id`) REFERENCES `tareas_examenes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `tareas_alumnos_ibfk_2` FOREIGN KEY (`alumno_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- Tabla de tareas y exámenes
CREATE TABLE `tareas_examenes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `docente_id` int NOT NULL,
  `titulo` varchar(255) NOT NULL,
  `descripcion` text,
  `fecha_entrega` date NOT NULL,
  `archivo_adjunto` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `docente_id` (`docente_id`),
  CONSTRAINT `tareas_examenes_ibfk_1` FOREIGN KEY (`docente_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- Tabla de usuarios
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre_completo` varchar(255) NOT NULL,
  `correo_electronico` varchar(255) NOT NULL,
  `contraseña` varchar(255) NOT NULL,
  `rol` enum('docente','alumno','padre') NOT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo_electronico` (`correo_electronico`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
