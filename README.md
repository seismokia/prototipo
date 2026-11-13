# Asistente patrimonial (prototipo TFM)

Autor: Moisés Gómez Rodríguez

Asistente conversacional de planificación financiera por objetivos para particulares en España. Es una herramienta de **planificación y educación financiera** con datos sintéticos: no presta asesoramiento en materia de inversión ni recomienda productos concretos.

- Especificación: [docs/SPEC.md](docs/SPEC.md)
- Plan por fases: [docs/PLAN_PROTOTIPO.md](docs/PLAN_PROTOTIPO.md)
- Decisiones de diseño: [docs/decisiones.md](docs/decisiones.md)

**Estado actual:** Fase 1 (motor de planificación). Existen el endpoint `/health`, una página que muestra el estado de la API y el motor determinista en `engine/`, todavía sin exponer por la API.

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
| `make test` | Pruebas unitarias e integradas (pytest), con cobertura mínima del 90 % en `engine/` |
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

GitHub Actions ejecuta ruff y pytest en cada push a `main` y en cada pull request ([.github/workflows/ci.yml](.github/workflows/ci.yml)). No necesita claves.

## Motor de planificación

`engine/` calcula el plan sin LLM ni base de datos: capacidad de ahorro, fondo de emergencia, reparto por prioridad, asignación por clase de activo y proyección en tres escenarios. El punto de entrada es `build_plan(plan_input, params)`.

Los parámetros de cálculo están en [engine/config/parametros.yaml](engine/config/parametros.yaml). **Sus valores son ilustrativos** y están pendientes de validar. Los supuestos del cálculo están en [docs/decisiones.md](docs/decisiones.md) (D-006 a D-011).
