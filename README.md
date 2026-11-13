# Asistente patrimonial (prototipo TFM)

Autor: Moisés Gómez Rodríguez

Asistente conversacional de planificación financiera por objetivos para particulares en España. Es una herramienta de **planificación y educación financiera** con datos sintéticos: no presta asesoramiento en materia de inversión ni recomienda productos concretos.

- Especificación: [docs/SPEC.md](docs/SPEC.md)
- Plan por fases: [docs/PLAN_PROTOTIPO.md](docs/PLAN_PROTOTIPO.md)
- Decisiones de diseño: [docs/decisiones.md](docs/decisiones.md)

**Estado actual:** Fase 2 (datos y API básica). La API guarda el perfil y los objetivos de un usuario de demostración en PostgreSQL y calcula el plan con el motor determinista. El frontend todavía solo muestra el estado de la API.

## Requisitos

- Docker con Docker Compose
- `make` (en Windows: `winget install ezwinports.make`)

No hace falta instalar Python ni dependencias en la máquina: el lint y las pruebas se ejecutan dentro de un contenedor.

## Puesta en marcha

```bash
make up
```

| Servicio | URL |
|---|---|
| Frontend (Streamlit) | http://localhost:8501 |
| API (FastAPI) | http://localhost:8000/health |
| Documentación de la API | http://localhost:8000/docs |
| PostgreSQL + pgvector | `localhost:5432` |

Para cambiar puertos o credenciales locales, copia `.env.example` a `.env` y edítalo. Sin `.env` se usan los valores por defecto de desarrollo.

## Comandos

| Comando | Qué hace |
|---|---|
| `make up` | Construye y levanta `api`, `frontend` y `db` |
| `make down` | Detiene los servicios |
| `make logs` | Muestra los logs en vivo |
| `make migrate` | Aplica las migraciones pendientes (también se aplican al arrancar `api`) |
| `make test` | Pruebas unitarias e integradas (pytest), con cobertura mínima del 90 % en `engine/`. Levanta `db` para las de integración |
| `make lint` | Ruff: lint y comprobación de formato |
| `make format` | Aplica las correcciones y el formato de ruff |
| `make lock` | Regenera `uv.lock` tras cambiar `pyproject.toml` |
| `make ingest` | Carga la base de conocimiento (Fase 4, aún sin implementar) |
| `make eval` | Evaluación del RAG y los guardrails (Fase 4, aún sin implementar) |

Sin `make`, los equivalentes son `docker compose up --build -d` y `docker compose run --rm --build tools pytest` (o `ruff check .`, `ruff format --check .`).

## Estructura

```
api/         Endpoints FastAPI, esquemas y acceso a datos
engine/      Motor de planificación determinista (sin dependencias de LLM)
llm/         Capa de abstracción del proveedor + FakeLLM
rag/         Ingesta, troceado y recuperación
frontend/    Aplicación Streamlit
infra/       Dockerfiles e inicialización de la base de datos
docs/        SPEC.md, plan y decisiones
tests/       unit/, integration/, eval/
```

## Integración continua

GitHub Actions ejecuta ruff y pytest en cada push a `main` y en cada pull request ([.github/workflows/ci.yml](.github/workflows/ci.yml)). Las pruebas de integración usan un contenedor de PostgreSQL del propio job. No necesita claves.

## Motor de planificación

`engine/` calcula el plan sin LLM ni base de datos: capacidad de ahorro, fondo de emergencia, reparto por prioridad, asignación por clase de activo y proyección en tres escenarios. El punto de entrada es `build_plan(plan_input, params)`.

Los parámetros de cálculo están en [engine/config/parametros.yaml](engine/config/parametros.yaml). **Sus valores son ilustrativos** y están pendientes de validar. Los supuestos del cálculo están en [docs/decisiones.md](docs/decisiones.md) (D-006 a D-011).

## Base de datos y migraciones

El modelo relacional del apartado 5 de la especificación está en [api/db/models.py](api/db/models.py) y se crea con migraciones de Alembic ([api/db/migrations/versions/](api/db/migrations/versions/)). El contenedor `api` las aplica al arrancar, así que `make up` deja la base lista, con un **usuario de demostración** sobre el que actúan todos los endpoints (no hay autenticación).

Para añadir una migración tras cambiar los modelos:

```bash
docker compose run --rm tools alembic revision --autogenerate -m "describe the change"
```

Las pruebas de integración usan una base de datos aparte (`asistente_test`), que se crea sola y se reconstruye con las migraciones en cada ejecución. Nunca tocan la base de la aplicación.

## API

Los nombres de los campos JSON están en inglés, como en el motor. Los importes se devuelven como cadenas decimales (`"1234.56"`) y se aceptan como cadena o número. La documentación interactiva está en http://localhost:8000/docs.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio |
| GET | `/perfil` | Devuelve la ficha de perfil (404 si aún no existe) |
| PUT | `/perfil` | Crea la ficha o la sustituye completa |
| GET | `/objetivos` | Lista los objetivos por orden de prioridad |
| POST | `/objetivos` | Crea un objetivo (409 si ya hay tres) |
| DELETE | `/objetivos/{id}` | Borra un objetivo |
| POST | `/plan` | Calcula el plan con el perfil y los objetivos guardados y lo guarda (409 si no hay perfil) |
| POST | `/plan/simular` | Calcula un plan con valores alternativos de perfil u objetivos; no guarda nada |

Flujo completo con datos sintéticos:

```bash
curl -X PUT http://localhost:8000/perfil -H "Content-Type: application/json" -d '{"monthly_income": "2500", "monthly_expenses": "1500", "monthly_debt_payment": "200", "current_savings": "3000", "dependents": 1, "risk_profile": "moderado"}'
```

```bash
curl -X POST http://localhost:8000/objetivos -H "Content-Type: application/json" -d '{"name": "Entrada del piso", "amount": "12000", "term_months": 60, "priority": 1}'
```

```bash
curl -X POST http://localhost:8000/plan
```

```bash
curl -X POST http://localhost:8000/plan/simular -H "Content-Type: application/json" -d '{"profile": {"monthly_income": "3000"}}'
```
