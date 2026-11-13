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

## D-006 — Importes en `Decimal` y redondeo al céntimo

- **Fecha:** 2026-11-13 · **Fase:** 1
- **Decisión:** el motor trabaja con `Decimal`. Las salidas se redondean al céntimo; la proyección acumula sin redondear y solo redondea la serie que devuelve.
- **Motivo:** las cifras del plan deben ser exactas y reproducibles; con `float` aparecen diferencias de céntimos difíciles de explicar.
- **Consecuencia:** al serializar a JSON los importes salen como cadenas. La Fase 2 decidirá el formato de la API.

## D-007 — Fondo de emergencia: se completa en paralelo a los objetivos

- **Fecha:** 2026-11-13 · **Fase:** 1
- **Contexto:** la especificación define el tamaño del fondo (N meses de gastos) pero no cómo convive con los objetivos.
- **Decisión:** N depende del perfil de riesgo. El ahorro actual cubre primero el fondo. Si falta, una fracción configurable de la capacidad de ahorro (`fraccion_capacidad_ahorro`) va al fondo hasta completarlo y el resto a los objetivos. Si sobra, el excedente se reparte como capital inicial de los objetivos por orden de prioridad.
- **Alternativa descartada:** exigir el fondo completo antes de aportar a ningún objetivo; más simple, pero deja a muchos perfiles sin plan durante meses.
- **Límite:** el fondo se calcula sobre los gastos, sin incluir las cuotas de deuda, y no se proyecta con rentabilidad (se supone en liquidez).

## D-008 — Reparto por prioridad en cascada, mes a mes y sin contar rentabilidad

- **Fecha:** 2026-11-13 · **Fase:** 1
- **Decisión:** cada mes, tras la parte del fondo, los objetivos se atienden por prioridad (1 primero; en caso de empate, el de menor plazo). Cada uno pide una cuota constante: lo que le falta entre los meses que le quedan, redondeada al céntimo hacia arriba. Si un mes no recibe la cuota completa, se recalcula al mes siguiente, de modo que recupera el retraso cuando se libera dinero (fondo completado u objetivo anterior terminado). La última cuota absorbe el redondeo.
- **Motivo:** la cuota no cuenta con la rentabilidad esperada (criterio prudente y fácil de explicar). Un objetivo es `feasible` si capital inicial más aportaciones alcanzan el importe sin rentabilidad; el indicador `goal_reached` de cada escenario sí la tiene en cuenta.
- **Consecuencia:** la aportación de un objetivo puede cambiar en el tiempo; la salida incluye la serie mensual y su resumen por tramos.
- **Alternativa descartada:** reparto proporcional a la prioridad, que deja todos los objetivos a medias cuando el ahorro no llega.

## D-009 — Tabla de asignación por tramos de plazo y perfil

- **Fecha:** 2026-11-13 · **Fase:** 1
- **Decisión:** tres tramos de plazo (hasta 12, 36 y 60 meses) por tres perfiles de riesgo, con porcentajes por clase de activo que suman 100. La carga de parámetros rechaza tablas incompletas, que no sumen 100 o cuyo último tramo no cubra 60 meses.
- **Límite:** la asignación es constante durante todo el plazo; no se reduce el riesgo al acercarse el vencimiento.

## D-010 — Supuestos de la proyección

- **Fecha:** 2026-11-13 · **Fase:** 1
- **Decisión:** capitalización mensual con la rentabilidad mensual equivalente de cada clase de activo, ponderada por la asignación; aportación al final de cada mes. Cifras nominales: sin inflación, comisiones ni impuestos. Un objetivo se da por alcanzado en un escenario si el saldo final es mayor o igual que el importe.
- **Motivo:** modelo mínimo y explicable. Los tres escenarios son deterministas, no una simulación estocástica.

## D-011 — Parámetros en YAML con claves en español; límites del dominio en el código

- **Fecha:** 2026-11-13 · **Fase:** 1
- **Decisión:** `engine/config/parametros.yaml` usa claves en español y se valida con Pydantic (atributos en inglés mediante alias). Los valores son ilustrativos y así se indica en la cabecera y en `version`. Los límites que fija la especificación (máximo 3 objetivos, 60 meses, prioridad 1-3) son restricciones de los modelos de entrada, no parámetros de cálculo.
- **Dependencias añadidas:** `pyyaml` (lectura del YAML; ya estaba en el lockfile como dependencia transitiva de uvicorn) y `pytest-cov` en desarrollo. `make test` y el CI exigen un 90 % de cobertura de `engine/`.
