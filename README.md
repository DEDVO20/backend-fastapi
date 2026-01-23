# Backend FastAPI - Sistema de Gestión de Calidad

Backend completo construido con FastAPI, Docker, PostgreSQL y pgAdmin para un Sistema de Gestión de Calidad (QMS).

## 🎉 Características Principales

- ✅ **35 Modelos SQLAlchemy** con relaciones completas
- ✅ **90+ Endpoints REST** completamente documentados
- ✅ **8 Routers FastAPI** organizados por módulo
- ✅ **Documentación Automática** con Swagger UI y ReDoc
- ✅ **Docker Compose** con FastAPI + PostgreSQL + pgAdmin
- ✅ **Scripts de Inicialización** automáticos
- ✅ **Validación con Pydantic** en todos los endpoints
- ✅ **Hot Reload** para desarrollo

## 🚀 Inicio Rápido

### 1. Clonar y Configurar

```bash
# Copiar ejemplo de variables de entorno
cp .env.example .env

# Editar .env con tus configuraciones (opcional en desarrollo)
```

### 2. Iniciar con Docker

```bash
# Construir imágenes
docker compose build

# Iniciar servicios
docker compose up -d
```

### 3. Inicializar Base de Datos

```bash
# Ejecutar script de inicialización (crea tablas + datos iniciales)
docker compose exec fastapi-app bash -c "chmod +x init_database.sh && ./init_database.sh"

# O manualmente:
docker compose exec fastapi-app python -m app.db.init_db
docker compose exec fastapi-app python -m app.db.seed_data
```

### 4. Acceder a la Aplicación

- **API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc
- **pgAdmin**: http://localhost:5050
  - Email: `admin@admin.com`
  - Password: `admin`

## 📊 Módulos Implementados

| Módulo | Endpoints | Descripción |
|--------|-----------|-------------|
| **Usuarios** | 10+ | Gestión de usuarios, áreas, roles y permisos |
| **Procesos** | 15+ | Procesos con PHVA, etapas, instancias, acciones |
| **Documentos** | 10+ | Gestión documental con versionado |
| **Calidad** | 20+ | Indicadores, no conformidades, acciones correctivas |
| **Auditorías** | 10+ | Auditorías internas/externas y hallazgos |
| **Riesgos** | 10+ | Gestión de riesgos con matriz probabilidad-impacto |
| **Capacitaciones** | 10+ | Programación, asistencia y certificación |
| **Sistema** | 15+ | Tickets, notificaciones y configuraciones |

**Total: 90+ endpoints REST**

## 🗂️ Estructura del Proyecto

```
backendFastApi/
├── app/
│   ├── main.py               # Aplicación FastAPI principal
│   ├── config.py             # Configuración (Pydantic Settings)
│   ├── database.py           # Setup SQLAlchemy
│   ├── api/                  # 8 routers REST
│   │   ├── usuarios.py
│   │   ├── procesos.py
│   │   ├── documentos.py
│   │   ├── calidad.py
│   │   ├── auditorias.py
│   │   ├── riesgos.py
│   │   ├── capacitaciones.py
│   │   └── sistema.py
│   ├── models/               # 35 modelos SQLAlchemy
│   ├── schemas/              # 40+ schemas Pydantic
│   └── db/
│       ├── init_db.py        # Crear tablas
│       └── seed_data.py      # Datos iniciales
├── Dockerfile                # Imagen optimizada
├── docker-compose.yml        # 3 servicios
├── requirements.txt          # Dependencias Python
└── README.md                 # Esta documentación
```

## 🔐 Credenciales por Defecto

**Usuario Administrador:**
```
Usuario: admin
Contraseña: admin123
```

**Base de Datos:**
```
Host: localhost
Puerto: 5432
Usuario: fastapi_user
Password: fastapi_password
Database: fastapi_db
```

> ⚠️ **Cambiar estas credenciales en producción**

## 📡 Ejemplos de Uso

### Crear un Usuario

```bash
curl -X POST "http://localhost:8000/api/v1/usuarios" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_usuario": "jperez",
    "email": "jperez@example.com",
    "nombre_completo": "Juan Pérez",
    "password": "secure123",
    "cargo": "Gerente",
    "area_id": null,
    "activo": true
  }'
```

### Crear una No Conformidad

```bash
curl -X POST "http://localhost:8000/api/v1/no-conformidades" \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "NC-001",
    "descripcion": "Producto no conforme detectado",
    "tipo": "producto",
    "fuente": "inspeccion",
    "fecha_deteccion": "2026-01-21T20:00:00Z",
    "estado": "abierta"
  }'
```

### Listar Auditorías

```bash
curl "http://localhost:8000/api/v1/auditorias?estado=programada&limit=10"
```

### Crear un Ticket

```bash
curl -X POST "http://localhost:8000/api/v1/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "TK-001",
    "titulo": "Solicitud de soporte",
    "descripcion": "Necesito ayuda con el sistema",
    "categoria": "soporte",
    "prioridad": "media"
  }'
```

## 🔧 Comandos Docker Útiles

```bash
# Ver logs en tiempo real
docker compose logs -f fastapi-app

# Reiniciar solo la API
docker compose restart fastapi-app

# Ver estado de servicios
docker compose ps

# Detener todo
docker compose down

# Reconstruir después de cambios en código
docker compose up -d --build

# Conectar a PostgreSQL
docker compose exec postgres psql -U fastapi_user -d fastapi_db

# Ver tablas creadas
docker compose exec postgres psql -U fastapi_user -d fastapi_db -c "\dt"

# Ejecutar shell en contenedor FastAPI
docker compose exec fastapi-app bash
```

## 🛠️ Tecnologías Utilizadas

- **FastAPI** 0.109.0 - Framework web moderno
- **SQLAlchemy** 2.0.25 - ORM para Python
- **Pydantic** 2.5.3 - Validación de datos
- **PostgreSQL** 15 - Base de datos relacional
- **Docker** & **Docker Compose** - Contenedorización
- **pgAdmin** 4 - Administración de PostgreSQL
- **Uvicorn** - Servidor ASGI
- **Python** 3.11

## 📚 Documentación de API

La documentación completa e interactiva está disponible en:

- **Swagger UI**: http://localhost:8000/docs
  - Interfaz interactiva para probar endpoints
  - Esquemas de request/response
  - Ejemplos de uso
  
- **ReDoc**: http://localhost:8000/redoc
  - Documentación alternativa más detallada
  - Mejor para lectura

## ✅ Características Implementadas

- ✅ CRUD completo para todas las entidades (35 modelos)
- ✅ Validación automática con Pydantic
- ✅ Filtros en endpoints GET (estado, tipo, categoría, etc.)
- ✅ Paginación con skip/limit
- ✅ Relaciones entre modelos (Foreign Keys)
- ✅ Cascade Delete/Update
- ✅ Índices en campos frecuentes
- ✅ UUID como Primary Keys
- ✅ Timestamps automáticos (creado_en, actualizado_en)
- ✅ Validación de códigos únicos
- ✅ CORS configurado
- ✅ Hot Reload en desarrollo
- ✅ Gestión de errores HTTP
- ✅ Documentación automática

## 🎯 Próximas Mejoras Sugeridas

1. **Autenticación y Autorización**
   - [ ] Implementar JWT para autenticación
   - [ ] Middleware de autorización basado en roles
   - [ ] Endpoints de login/logout
   - [ ] Refresh tokens

2. **Tests**
   - [ ] Tests unitarios con pytest
   - [ ] Tests de integración
   - [ ] Coverage reports

3. **Migraciones**
   - [ ] Configurar Alembic
   - [ ] Versionado de esquema de BD

4. **Producción**
   - [ ] Secrets management (Vault, AWS Secrets)
   - [ ] SSL/TLS
   - [ ] Rate limiting
   - [ ] Logging estructurado
   - [ ] Monitoreo (Prometheus, Grafana)

5. **Funcionalidades**
   - [ ] Carga de archivos
   - [ ] Exportación a PDF/Excel
   - [ ] Notificaciones en tiempo real (WebSockets)
   - [ ] Búsqueda full-text

## 🐛 Troubleshooting

### Error: Puerto 8000 en uso
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8001:8000"  # Usar puerto 8001 en lugar de 8000
```

### Error: Base de datos no conecta
```bash
# Verificar que PostgreSQL esté corriendo
docker compose ps

# Revisar logs de PostgreSQL
docker compose logs postgres

# Reiniciar servicios
docker compose restart
```

### Error: Tablas no existen
```bash
# Ejecutar script de inicialización
docker compose exec fastapi-app python -m app.db.init_db
```

## 📄 Licencia

Este proyecto es de código abierto. Puedes modificarlo según tus necesidades.

## 👨‍💻 Desarrollo

### Agregar un Nuevo Endpoint

1. Crear modelo en `app/models/`
2. Crear schemas en `app/schemas/`
3. Crear router en `app/api/`
4. Importar en `app/main.py`

### Variables de Entorno

Configurables en `.env`:

```env
# Database
DATABASE_URL=postgresql://fastapi_user:fastapi_password@postgres:5432/fastapi_db

# App
APP_NAME=Sistema de Gestión de Calidad
APP_VERSION=1.0.0
ENVIRONMENT=development
SECRET_KEY=your-secret-key-change-in-production

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

**¡Sistema completo y listo para usar!** 🚀

Para cualquier duda, consulta la documentación interactiva en `/docs`.
