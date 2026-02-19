# BIG DATA PIPELINE LAB

<p align="center">
  <img src="https://img.shields.io/badge/Apache%20Airflow-017077?style=for-the-badge&logo=apache-airflow" alt="Airflow">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/MinIO-000000?style=for-the-badge&logo=minio" alt="MinIO">
  <img src="https://img.shields.io/badge/Metabase-509EE3?style=for-the-badge&logo=metabase" alt="Metabase">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker" alt="Docker">
</p>

---

## Descripcion

**BIG DATA PIPELINE LAB** es un ecosistema completo de procesamiento de datos construido con Docker Compose. Este proyecto implementa un pipeline ETL (Extract, Transform, Load) end-to-end para datos de criptomonedas, extrayendo informacion de la API publica de CoinGecko, transformandola y almacenandola para su analisis.

El proyecto esta diseñado para ser:

- **Professional**: Sigue las mejores practicas de la industria
- **Modular**: Cada componente tiene una responsabilidad única
- **Escalable**: Puede crecer con las necesidades del negocio
- **Listo para produccion**: Configuraciones de producción listas

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BIG DATA PIPELINE LAB                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │   CoinGecko │────▶│   Airflow   │────▶│    MinIO    │                  │
│   │     API     │     │  Orchestrator│     │  Data Lake  │                  │
│   └─────────────┘     └──────┬──────┘     └──────┬─────┘                  │
│                              │                    │                        │
│                              ▼                    │                        │
│                     ┌───────────────┐             │                        │
│                     │  PostgreSQL   │◀────────────┘                        │
│                     │Data Warehouse │                                     │
│                     └───────┬───────┘                                       │
│                             │                                               │
│                             ▼                                               │
│                     ┌───────────────┐                                       │
│                     │   Metabase    │                                       │
│                     │  Dashboard    │                                       │
│                     └───────────────┘                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

1. **Extract**: Airflow DAG ejecuta la tarea de extraccion desde la API de CoinGecko
2. **Store Raw**: Los datos crudos se guardan en MinIO (Data Lake)
3. **Transform**: Los datos se limpian, normalizan y enriquecen con pandas
4. **Load**: Los datos transformados se almacenan en PostgreSQL
5. **Visualize**: Metabase se conecta a PostgreSQL para crear dashboards

---

## Stack Tecnologico

| Componente | Version | Descripcion |
|------------|---------|-------------|
| Apache Airflow | 2.8.1 | Orquestacion de pipelines |
| PostgreSQL | 15-alpine | Base de datos relacional |
| MinIO | latest | Almacenamiento compatible con S3 |
| Metabase | latest | Herramienta de visualizacion |
| Redis | 7-alpine | Broker de Celery |
| Docker | latest | Contenedores |

---

## Estructura del Proyecto

```
big-data-pipeline-lab/
│
├── docker-compose.yml          # Orquestacion de servicios
├── Dockerfile.airflow          # Imagen personalizada de Airflow
├── .env                        # Variables de entorno
│
├── dags/
│   └── data_pipeline_dag.py   # DAG de Airflow
│
├── scripts/
│   ├── extract.py             # Extraccion de datos
│   ├── transform.py           # Transformacion de datos
│   └── load.py                # Carga a PostgreSQL
│
├── sql/
│   └── schema.sql             # Esquema de base de datos
│
└── README.md                  # Documentacion
```

---

## Requisitos Previos

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM disponibles
- 20GB espacio en disco

---

## Instalacion y Configuracion

### 1. Clonar el repositorio

```bash
git clone https://github.com/ieharo1/big-data-pipeline-lab.git
cd big-data-pipeline-lab
```

### 2. Configurar variables de entorno

El archivo `.env` ya esta configurado con valores por defecto. Puedes modificarlo segun tus necesidades:

```bash
# Airflow
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow_secure_2026

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_secure_2026
POSTGRES_DB=pipeline_warehouse

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin_secure_2026

# Metabase
METABASE_PASSWORD=metabase_secure_2026
```

### 3. Iniciar los servicios

```bash
# Iniciar todos los servicios
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f

# Ver estado de los servicios
docker compose ps
```

---

## Puertos Expuestos

| Servicio | Puerto | URL | Credenciales |
|----------|--------|-----|---------------|
| Airflow Webserver | 8080 | http://localhost:8080 | airflow / airflow_secure_2026 |
| Airflow Flower | 5555 | http://localhost:5555 | (opcional) |
| MinIO Console | 9001 | http://localhost:9001 | minioadmin / minioadmin_secure_2026 |
| MinIO API | 9000 | http://localhost:9000 | minioadmin / minioadmin_secure_2026 |
| Metabase | 3000 | http://localhost:3000 | zackharo1@gmail.com / metabase_secure_2026 |
| PostgreSQL | 5432 | localhost:5432 | postgres / postgres_secure_2026 |
| Redis | 6379 | localhost:6379 | (sin autenticacion) |

---

## Uso del Pipeline

### Acceder a Airflow

1. Abre http://localhost:8080 en tu navegador
2. Inicia sesion con:
   - Usuario: `airflow`
   - Contraseña: `airflow_secure_2026`
3. Busca el DAG `crypto_data_pipeline` en la lista
4. Activa el DAG haciendo clic en el switch
5. Dispara una ejecucion manual haciendo clic en "Play" > "Trigger DAG"

### Acceder a Metabase

1. Abre http://localhost:3000
2. Configura el idioma preferido
3. Inicia sesion con:
   - Email: `zackharo1@gmail.com`
   - Contraseña: `metabase_secure_2026`
4. Conecta a la base de datos PostgreSQL:
   - Host: `postgres`
   - Puerto: `5432`
   - Base de datos: `pipeline_warehouse`
   - Usuario: `postgres`
   - Contraseña: `postgres_secure_2026`
5. Explora los datos en las tablas `crypto_prices` y `price_aggregates`

### Acceder a MinIO

1. Abre http://localhost:9001
2. Inicia sesion con:
   - Access Key: `minioadmin`
   - Secret Key: `minioadmin_secure_2026`
3. Explora el bucket `pipeline-raw` donde se almacenan los datos crudos

---

## Verificar que Todo Funciona

### Verificar servicios

```bash
# Verificar estado de contenedores
docker compose ps

# Ver logs de Airflow
docker compose logs airflow-webserver

# Ver logs de PostgreSQL
docker compose logs postgres
```

### Verificar base de datos

```bash
# Conectar a PostgreSQL
docker exec -it pipeline_postgres psql -U postgres -d pipeline_warehouse

# Listar tablas
\dt

# Ver datos
SELECT * FROM crypto_prices LIMIT 5;
```

### Verificar MinIO

```bash
# Usar mc CLI
docker exec pipeline_minio mc ls local/pipeline-raw/
```

---

## Configuracion de Seguridad

### Buenas Practicas Implementadas

- Contraseñas fuertes en variables de entorno
- No hay credenciales hardcodeadas
- Red interna Docker para comunicacion entre servicios
- Healthchecks en todos los servicios
- Politicas de restart automatico

### Recomendaciones para Produccion

1. Cambiar todas las contraseñas por defecto
2. Habilitar SSL/TLS para todas las conexiones
3. Configurar backups automaticos de PostgreSQL
4. Implementar monitoreo con Prometheus/Grafana
5. Usar secretos de Kubernetes o HashiCorp Vault

---

## Desarrollo y Personalizacion

### Agregar nuevas fuentes de datos

1. Edita `scripts/extract.py`
2. Agrega la nueva logica de extraccion
3. Modifica `sql/schema.sql` si necesitas nuevas tablas
4. Actualiza el DAG en `dags/data_pipeline_dag.py`

### Personalizar transformaciones

Edita `scripts/transform.py` para agregar:

- Validaciones personalizadas
- Enriquecimiento de datos
- Reglas de negocio

### Crear nuevos dashboards en Metabase

1. Accede a Metabase
2. Crea preguntas sobre los datos
3. Organiza en dashboards
4. Comparte con tu equipo

---

## Comandos Utiles

```bash
# Iniciar servicios
docker compose up -d

# Detener servicios
docker compose down

# Reiniciar un servicio especifico
docker compose restart airflow-webserver

# Ver logs de un servicio
docker compose logs -f postgres

# Acceder al contenedor de Airflow
docker exec -it pipeline_airflow_webserver bash

# Rebuild de imagen
docker compose build airflow-webserver

# Limpiar volumenes (cuidado: borra datos)
docker compose down -v
```

---

## Solucion de Problemas

### Airflow no inicia

```bash
# Verificar logs
docker compose logs airflow-webserver

# Comprobar permisos
ls -la dags/ scripts/ sql/
```

### PostgreSQL no acepta conexiones

```bash
# Esperar a que este listo
docker compose logs postgres

# Verificar desde otro contenedor
docker exec -it pipeline_postgres pg_isready -U postgres
```

### Metabase no conecta a PostgreSQL

1. Verificar que PostgreSQL este saludable
2. Comprobar credenciales en variables de entorno
3. Esperar a que Metabase termine de iniciar (puede tomar 2-3 minutos)

---

## Desarrollado por Isaac Esteban Haro Torres

**Ingeniero en Sistemas · Full Stack · Automatización · Data**

- 📧 Email: zackharo1@gmail.com
- 📱 WhatsApp: 098805517
- 💻 GitHub: https://github.com/ieharo1
- 🌐 Portafolio: https://ieharo1.github.io/portafolio-isaac.haro/

---

## Licencia

© 2026 Isaac Esteban Haro Torres - Todos los derechos reservados.

---

## Acknowledgments

- [Apache Airflow](https://airflow.apache.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [MinIO](https://min.io/)
- [Metabase](https://www.metabase.com/)
- [CoinGecko API](https://www.coingecko.com/)
