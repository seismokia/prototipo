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

## D-012 — Migraciones con Alembic, aplicadas al arrancar la API

- **Fecha:** 2026-11-13 · **Fase:** 2
- **Decisión:** el esquema relacional se crea con migraciones de Alembic en `api/db/migrations/`, escritas a mano. El contenedor `api` ejecuta `alembic upgrade head` antes de servir. La URL de la base de datos sale de `DATABASE_URL`, no de `alembic.ini`.
- **Motivo:** es la herramienta habitual con SQLAlchemy y deja el historial del esquema versionado; al aplicarse en el arranque, `make up` no necesita pasos manuales.
- **Alternativa descartada:** scripts SQL numerados, sin dependencia nueva pero con el control de versiones del esquema hecho a mano.
- **Dependencias añadidas:** `sqlalchemy`, `psycopg[binary]` (previstas en D-004) y `alembic`.
- **Límite:** migrar en el arranque es válido con una sola instancia de la API; con varias réplicas habría que hacerlo en un paso de despliegue aparte.

## D-013 — Pruebas de integración contra PostgreSQL real

- **Fecha:** 2026-11-13 · **Fase:** 2
- **Decisión:** las pruebas de integración usan PostgreSQL: el servicio `db` del compose en local y un contenedor de servicio en GitHub Actions. Trabajan en una base aparte (`asistente_test`, indicada en `TEST_DATABASE_URL`), que se vacía y se reconstruye con las migraciones reales en cada ejecución. Las pruebas se niegan a ejecutarse si el nombre de la base no termina en `_test`, y se omiten si la variable no está definida.
- **Motivo:** se prueban las migraciones y los tipos de PostgreSQL (JSONB ahora, pgvector en la Fase 4). Una prueba comprueba además que los modelos ORM coinciden con el esquema migrado.
- **Alternativa descartada:** SQLite en memoria, más rápido pero sin probar las migraciones ni los tipos reales.

## D-014 — Formato de la API: campos en inglés e importes como cadenas decimales

- **Fecha:** 2026-11-13 · **Fase:** 2
- **Decisión:** las rutas son las de la especificación (en español) y las tablas y columnas también. Los campos JSON van en inglés, igual que los modelos del motor, cuyo resultado se devuelve sin traducir. Los importes salen como cadenas decimales (`"1234.56"`) y se aceptan como cadena o número. Cierra el punto pendiente de D-006.
- **Motivo:** una sola nomenclatura entre motor y API, sin capa de alias; las cadenas conservan la exactitud del `Decimal`.
- **Consecuencia:** el frontend debe convertir los importes para mostrarlos o dibujarlos.

## D-015 — Usuario de demostración e identificadores

- **Fecha:** 2026-11-13 · **Fase:** 2
- **Decisión:** una migración crea el usuario de demostración con un identificador fijo. Todos los endpoints actúan sobre él mediante una dependencia (`get_current_user_id`), que es el único punto que habría que cambiar para añadir autenticación. Las claves primarias son UUID.
- **Tipos no fijados por la especificación:** importes en `NUMERIC(12, 2)`; `resultado_json`, `preguntas_json` y `fragmentos_ids` en JSONB; `tema` como texto; clave de `perfil` = `usuario_id`; clave de `conocimiento_usuario` = (`usuario_id`, `tema`); clave de `respuesta_pildora` = (`pildora_id`, `pregunta_idx`). Las tablas de formación y mensajes se crean ya, pero no se usan hasta las Fases 3 a 5 y pueden ajustarse entonces con una migración.

## D-016 — Comportamiento de los endpoints de perfil, objetivos y plan

- **Fecha:** 2026-11-13 · **Fase:** 2
- **`/perfil`:** `PUT` crea la ficha o la sustituye completa; `GET` devuelve 404 si no existe.
- **`/objetivos`:** `POST` devuelve 409 al intentar crear el cuarto; el borrado es `DELETE /objetivos/{id}`. No hay edición: se borra y se crea de nuevo.
- **`POST /plan`:** calcula con el perfil y los objetivos guardados, guarda cada cálculo en `plan` con su `parametros_version` y lo devuelve. Sin perfil devuelve 409. Sin objetivos devuelve la capacidad de ahorro y el fondo de emergencia.
- **`POST /plan/simular`:** acepta cambios parciales del perfil y una lista alternativa de objetivos, devuelve la entrada efectiva y el resultado, y no guarda nada. No permite cambiar los parámetros de cálculo: siguen saliendo solo de `parametros.yaml`.
- **Pendiente:** no hay `GET /plan` para recuperar el último plan guardado, porque la especificación no lo incluye; habrá que decidirlo en la Fase 6 si el frontend lo necesita.
