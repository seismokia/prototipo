# Registro de decisiones

Decisiones de diseño que no están fijadas en `docs/SPEC.md`. Cada entrada indica el contexto, la opción elegida y las alternativas descartadas.

## D-001 — Gestor de dependencias: uv con `uv.lock`

- **Fecha:** 2026-11-13 · **Fase:** 0
- **Contexto:** la especificación fija Python 3.12 pero no cómo se gestionan las dependencias.
- **Decisión:** `uv` con `uv.lock` versionado. Las imágenes Docker y el CI instalan con `uv sync --locked`.
- **Motivo:** instalaciones reproducibles y rápidas; uv descarga el intérprete 3.12 aunque la máquina tenga otra versión.
- **Alternativa descartada:** `pip` + `venv` con `requirements.txt`, más simple pero sin lockfile.

## D-002 — Lint y pruebas dentro de un contenedor

- **Fecha:** 2026-11-13 · **Fase:** 0
- **Contexto:** el equipo de desarrollo usa Windows con Python 3.13 y sin uv instalado.
- **Decisión:** `make lint` y `make test` se ejecutan en el servicio `tools` del compose (etapa `dev` de `infra/api.Dockerfile`, con el repositorio montado). El CI ejecuta los mismos comandos con uv directamente en el runner.
- **Motivo:** el único requisito local es Docker y `make`; mismo intérprete y mismas versiones para todos.
- **Alternativa descartada:** entorno virtual local, que obliga a instalar Python 3.12 o uv en cada máquina.

## D-003 — Un único `pyproject.toml`

- **Fecha:** 2026-11-13 · **Fase:** 0
- **Decisión:** un solo `pyproject.toml` en la raíz. Las dependencias de la API son las del proyecto; las del frontend van en el grupo `frontend` y las de desarrollo en `dev`. La imagen del frontend instala solo su grupo.
- **Motivo:** un único lockfile y una única configuración de ruff y pytest, sin que la imagen del frontend arrastre las dependencias de la API.
- **Alternativa descartada:** un proyecto por servicio (workspace), excesivo para el tamaño del prototipo.

## D-004 — Dependencias añadidas cuando se usan

- **Fecha:** 2026-11-13 · **Fase:** 0
- **Decisión:** SQLAlchemy y el driver de PostgreSQL no se añaden en la Fase 0; entrarán en la Fase 2 junto con el modelo de datos. El servicio `db` sí está en el compose, con la extensión `vector` creada al inicializar el volumen.
- **Motivo:** regla de `CLAUDE.md`: no añadir dependencias sin justificarlo.

## D-005 — Valores por defecto de desarrollo en el compose

- **Fecha:** 2026-11-13 · **Fase:** 0
- **Decisión:** `docker-compose.yml` lee las credenciales de PostgreSQL de variables de entorno y, si no existe `.env`, usa valores por defecto de desarrollo local (los mismos que `.env.example`).
- **Motivo:** `make up` funciona sin pasos previos. La base de datos solo contiene datos sintéticos y no hay ningún secreto real.
- **Límite:** cualquier secreto real (claves del proveedor LLM, Langfuse) irá solo en `.env`, sin valor por defecto.
