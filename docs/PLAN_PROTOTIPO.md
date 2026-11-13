# Plan del prototipo con Claude Code

Autor: Moisés Gómez Rodríguez

Cada fase es una sesión de trabajo con Claude Code sobre el repositorio. Copia el prompt, revisa el plan que proponga antes de que implemente y fusiona el pull request solo cuando se cumplan los criterios de aceptación.

## Preparación

1. Crea el repositorio en GitHub y clónalo.
2. Copia `CLAUDE.md` en la raíz y `SPEC.md` en `docs/SPEC.md`.
3. Haz el primer commit en `main`.

---

## Fase 0 — Esqueleto

**Prompt**

> Lee `CLAUDE.md` y `docs/SPEC.md`. Crea el esqueleto del proyecto: estructura de carpetas, `pyproject.toml`, Makefile con los comandos indicados, Dockerfile de `api` y de `frontend`, `docker-compose.yml` con api, frontend y PostgreSQL con pgvector, `.env.example`, endpoint `/health`, una página Streamlit que llame a `/health`, una prueba de ejemplo y un workflow de GitHub Actions con lint y pruebas. No implementes funcionalidad todavía. Antes de escribir código, enséñame el plan.

**Aceptación**
- `make up` levanta los tres servicios y la página muestra el estado de la API.
- `make lint` y `make test` pasan en local y en GitHub Actions.

## Fase 1 — Motor de planificación

**Prompt**

> Implementa `engine/` según el apartado 3.3 de la especificación: capacidad de ahorro, fondo de emergencia, reparto por prioridad, asignación por clase de activo y proyección en tres escenarios. Los parámetros se leen de `engine/config/parametros.yaml` con valores ilustrativos claramente marcados. Sin dependencias de LLM ni de base de datos. Incluye pruebas unitarias de los casos límite.

**Aceptación**
- Funciones puras con entrada y salida Pydantic.
- Cobertura alta del motor y casos límite probados (ahorro negativo, objetivo inviable, plazo de 60 meses).

## Fase 2 — Datos y API básica

**Prompt**

> Implementa el modelo relacional del apartado 5 con migraciones, un usuario de demostración y los endpoints de perfil, objetivos, `/plan` y `/plan/simular` del apartado 6. Añade pruebas de integración.

**Aceptación**
- Flujo perfil → objetivos → plan funcionando por API con datos sintéticos.

## Fase 3 — Capa LLM y perfilado conversacional

**Prompt**

> Implementa `llm/` con la interfaz de la especificación, un `FakeLLM` determinista y el adaptador del proveedor real configurado por variables de entorno. Después implementa `/perfil/chat`: el modelo extrae los datos a un esquema validado y pregunta lo que falte. Prompts en `llm/prompts/`. Pruebas con `FakeLLM`.

**Aceptación**
- El perfilado completa la ficha en una conversación y el usuario puede corregirla.
- El CI no necesita claves.

## Fase 4 — RAG y asistente

**Prompt**

> Implementa `rag/`: ingesta (troceado por secciones, embeddings, carga en pgvector con metadatos), recuperación híbrida con filtros y las tres colecciones del apartado 5. Implementa `/asistente/chat` con citas, la explicación del plan, la simulación mediante tool calling sobre el motor y el enrutado de preguntas fuera de alcance. Añade `make ingest`, un conjunto pequeño de documentos de ejemplo y `make eval` con el conjunto de evaluación.

**Aceptación**
- Toda respuesta incluye citas a fragmentos reales.
- Las preguntas sobre productos concretos se rechazan con el aviso.
- `make eval` informa recall y tasa de rechazo correcta.

## Fase 5 — Formación adaptativa

**Prompt**

> Implementa el módulo de formación del apartado 3.5: mapa de conocimientos a partir del test, selección de la píldora recomendada por similitud con las lagunas del usuario, generación de la píldora a partir de fragmentos recuperados con preguntas de comprobación, corrección y actualización de nivel.

**Aceptación**
- La píldora usa datos del usuario en el ejemplo y lleva citas.
- Responder las preguntas cambia el nivel del tema.

## Fase 6 — Frontend

**Prompt**

> Completa la aplicación Streamlit con cinco páginas: Perfil (chat y ficha editable), Objetivos, Plan (tabla, gráfico de escenarios y explicación), Asistente (chat con citas desplegables) y Formación (mapa, píldora y preguntas). Aviso legal visible en todas. El frontend solo habla con la API.

**Aceptación**
- El flujo completo se recorre desde la interfaz sin tocar la API a mano.

## Fase 7 — Observabilidad y entrega

**Prompt**

> Añade logging estructurado con identificador de traza, integración con Langfuse en la capa `llm/`, endpoint `/metrics`, Prometheus y Grafana en el compose con un panel básico, y un workflow de GitHub Actions que construya y publique las imágenes Docker. Actualiza el README con la puesta en marcha y un diagrama de arquitectura.

**Aceptación**
- Cada respuesta del asistente es trazable: entrada, fragmentos, llamada al motor y salida.
- Las imágenes se construyen automáticamente al fusionar en `main`.

---

## Consejos de uso

- Pide siempre el plan antes de la implementación y recórtalo si se excede del alcance.
- Una fase por rama y por pull request. Revisa el diff completo antes de fusionar.
- Si aparece una decisión no prevista, que quede anotada en `docs/decisiones.md`: será material directo para la memoria.
- Cuando el grupo esté formado, cada fase se puede dividir en issues de GitHub Projects y repartirse.
