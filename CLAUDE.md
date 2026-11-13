# CLAUDE.md — Asistente patrimonial (prototipo TFM)

Autor del proyecto: Moisés Gómez Rodríguez

La especificación funcional y técnica está en `docs/SPEC.md`. Es la fuente de verdad: si una petición la contradice, avisa antes de implementar.

## Stack

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy
- Streamlit (frontend)
- PostgreSQL 16 + pgvector
- Docker y Docker Compose
- pytest, ruff
- GitHub Actions

## Estructura

```
api/         Endpoints FastAPI, esquemas y acceso a datos
engine/      Motor de planificación determinista (sin dependencias de LLM)
llm/         Capa de abstracción del proveedor + FakeLLM
rag/         Ingesta, troceado y recuperación
frontend/    Aplicación Streamlit
infra/       Dockerfiles, compose, Prometheus, Grafana
docs/        SPEC.md, arquitectura, decisiones
tests/       unit/, integration/, eval/
```

## Comandos

- `make up` — levanta todos los servicios con Docker Compose
- `make test` — pruebas unitarias e integradas
- `make lint` — ruff (lint y formato)
- `make ingest` — carga la base de conocimiento
- `make eval` — evaluación del RAG y de los guardrails

## Reglas del dominio

1. El LLM nunca calcula cifras del plan. Cualquier número sale de `engine/`.
2. `engine/` no importa nada de `llm/`, `rag/` ni `api/`.
3. Los parámetros de cálculo viven en `engine/config/parametros.yaml`. Nunca se escriben en el código.
4. Toda respuesta explicativa incluye las citas de los fragmentos usados.
5. No se nombran productos, valores, ISIN ni entidades como recomendación. Solo clases de activo y tipos de producto.
6. Solo datos sintéticos. Ningún dato personal real en el repositorio.

## Reglas de código

- Código, nombres y commits en inglés; textos de interfaz y prompts en español.
- Tipado completo y modelos Pydantic en las fronteras (API, salidas del LLM).
- Toda llamada al proveedor pasa por `llm/`. Las pruebas usan `FakeLLM`; el CI no necesita claves.
- Los prompts son ficheros versionados en `llm/prompts/`, no cadenas incrustadas.
- Secretos solo por variables de entorno. Mantén `.env.example` actualizado y nunca subas `.env`.
- Logging estructurado en JSON con identificador de traza.

## Forma de trabajar

- Una tarea = una rama = un pull request pequeño.
- Commits con formato Conventional Commits.
- Cada cambio de funcionalidad incluye sus pruebas.
- Antes de dar una tarea por terminada: `make lint` y `make test` en verde, y README o docs actualizados si cambia el uso.
- Si una decisión de diseño no está en `docs/SPEC.md`, propón la opción y espera confirmación; después regístrala en `docs/decisiones.md`.
- No añadas dependencias sin justificarlo.
