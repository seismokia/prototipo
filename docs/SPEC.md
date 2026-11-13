# Asistente patrimonial con IA generativa — Especificación del prototipo

- **Autor:** Moisés Gómez Rodríguez
- **Contexto:** Proyecto Júpiter (TFM), Máster en IA, Cloud Computing y DevOps — Pontia
- **Versión:** 0.1 (prototipo)
- **Nombre de trabajo:** `asistente-patrimonial` (provisional)

## 1. Objetivo

Asistente conversacional de planificación financiera por objetivos para particulares en España. A partir del perfil económico y familiar y de los objetivos del usuario, elabora un plan de ahorro e inversión a corto y medio plazo (hasta 5 años), lo explica con fuentes citadas y forma al usuario para que lo entienda.

Es una herramienta de **planificación y educación financiera**. No presta asesoramiento en materia de inversión: trabaja con clases de activo y tipos de producto, nunca con productos o valores concretos.

## 2. Principios de diseño (no negociables)

1. **El LLM interpreta y explica; no calcula.** Toda cifra del plan la produce el motor determinista.
2. **Toda explicación lleva cita** a un fragmento recuperado de la base de conocimiento.
3. **Sin productos concretos.** No se nombran fondos, acciones, ISIN ni entidades como recomendación.
4. **Datos sintéticos.** El prototipo no usa datos personales reales ni conexión bancaria.
5. **Trazabilidad.** De cada respuesta se registra: entrada, fragmentos usados, llamada al motor y salida.

## 3. Alcance del prototipo

Un único flujo de extremo a extremo.

### 3.1 Perfilado conversacional
- Chat guiado que recoge: ingresos netos mensuales, gastos mensuales, deudas (cuota mensual), ahorro actual, situación familiar (personas a cargo).
- Test breve: 5 preguntas de conocimientos y 3 de tolerancia al riesgo.
- El LLM extrae los datos a un esquema Pydantic validado. Si falta o es ambiguo un dato, pregunta.
- Resultado: ficha de perfil que el usuario puede revisar y corregir.
- Perfil de riesgo resultante: `conservador`, `moderado` o `dinamico`.

### 3.2 Objetivos
- Hasta 3 objetivos: nombre, importe, plazo en meses (máx. 60), prioridad (1-3).
- Comprobación de viabilidad frente a la capacidad de ahorro.

### 3.3 Plan (motor determinista)
- Capacidad de ahorro = ingresos − gastos − cuotas de deuda.
- Fondo de emergencia = N meses de gastos (N configurable por perfil).
- Reparto de la aportación mensual entre objetivos por prioridad.
- Asignación por clase de activo según plazo del objetivo y perfil de riesgo (tabla configurable).
- Proyección en tres escenarios (pesimista, central, optimista) con rentabilidades supuestas por clase de activo (configurables).
- Salida: aportación mensual por objetivo, asignación, serie temporal por escenario e indicador de si se alcanza el objetivo.

> Todos los parámetros (meses de fondo de emergencia, tabla de asignación, rentabilidades supuestas) viven en `engine/config/parametros.yaml`. Los valores iniciales son **ilustrativos** y deben validarse y justificarse en la memoria.

Clases de activo del prototipo: `liquidez`, `monetario`, `renta_fija_corto`, `renta_fija_medio`, `renta_variable_global`.

### 3.4 Asistente con RAG
- Explicación del plan generada por el LLM a partir de la salida del motor y de fragmentos recuperados.
- Preguntas libres sobre el plan y sobre conceptos financieros, con citas.
- Simulación "¿y si…?": el LLM traduce la petición a parámetros y relanza el motor (tool calling).
- Guardrails: enrutado semántico de preguntas fuera de alcance, aviso legal visible, rechazo de peticiones de productos concretos.

### 3.5 Formación adaptativa
- Temario: 6 temas × 3 niveles.
  1. Ahorro y presupuesto
  2. Renta fija y monetarios
  3. Fondos y ETF
  4. Riesgo y diversificación
  5. Costes y comisiones
  6. Fiscalidad del ahorro
- Mapa de conocimientos inicial a partir del test.
- Píldora bajo demanda y una recomendada. Cada píldora: 200-300 palabras, ejemplo con los datos del usuario, citas y 2-3 preguntas de comprobación.
- Las respuestas actualizan el nivel del usuario por tema.

### 3.6 Fuera de alcance
Análisis de fondos y empresas mediante APIs externas, seguimiento mensual con datos reales, conexión bancaria, fiscalidad detallada, autenticación real (el prototipo usa un usuario de demostración), notificaciones y gamificación.

## 4. Arquitectura

```
[Streamlit] --HTTP--> [FastAPI]
                         |-- engine/  (cálculo determinista, sin LLM)
                         |-- llm/     (capa de abstracción del proveedor)
                         |-- rag/     (ingesta y recuperación)
                         |-- PostgreSQL + pgvector
                         |-- Langfuse (trazas LLM) / Prometheus (métricas)
```

| Servicio | Tecnología |
|---|---|
| `api` | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy |
| `frontend` | Streamlit |
| `db` | PostgreSQL 16 + extensión pgvector |
| `observabilidad` | Langfuse, Prometheus, Grafana |

Capa `llm/`: interfaz única (`generar`, `generar_estructurado`, `embeber`) con dos implementaciones: el proveedor real, elegido por variable de entorno, y un `FakeLLM` determinista para pruebas y CI.

## 5. Modelo de datos

### Relacional
- `usuario` (id, nombre, creado_en)
- `perfil` (usuario_id, ingresos, gastos, cuota_deuda, ahorro_actual, personas_a_cargo, perfil_riesgo, actualizado_en)
- `objetivo` (id, usuario_id, nombre, importe, plazo_meses, prioridad)
- `plan` (id, usuario_id, parametros_version, resultado_json, creado_en)
- `conocimiento_usuario` (usuario_id, tema, nivel, actualizado_en)
- `pildora` (id, usuario_id, tema, nivel, contenido, preguntas_json, fragmentos_ids, creado_en)
- `respuesta_pildora` (pildora_id, pregunta_idx, correcta, creado_en)
- `mensaje` (id, usuario_id, rol, contenido, traza_id, creado_en)

### Vectorial (pgvector)
| Colección | Contenido | Metadatos |
|---|---|---|
| `conocimiento` | Guías CNMV y Banco de España, fiscalidad AEAT, glosario | fuente, url, fecha_publicacion, tema, nivel, vigente |
| `temario` | Descripción de cada tema y nivel | tema, nivel, prerrequisitos |
| `fuera_de_alcance` | Ejemplos de preguntas a rechazar | categoria, respuesta_tipo |

- Troceado por secciones, con el título de la sección en cada fragmento.
- Recuperación híbrida (vectorial + texto completo) con filtro por metadatos.
- Los datos del usuario y las cifras **no** van a la base vectorial.

## 6. API (v1)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio |
| POST | `/perfil/chat` | Turno del perfilado conversacional |
| GET / PUT | `/perfil` | Consultar o corregir la ficha |
| GET / POST / DELETE | `/objetivos` | Gestión de objetivos |
| POST | `/plan` | Calcula el plan (motor) |
| POST | `/plan/simular` | Simulación con parámetros alternativos |
| POST | `/asistente/chat` | Pregunta libre con RAG y citas |
| GET | `/formacion/mapa` | Mapa de conocimientos |
| POST | `/formacion/pildora` | Genera píldora (tema opcional) |
| POST | `/formacion/pildora/{id}/respuestas` | Corrige y actualiza nivel |
| GET | `/metrics` | Métricas Prometheus |

## 7. Observabilidad

- Logging estructurado en JSON con identificador de traza por petición.
- Langfuse: prompt, respuesta, tokens, coste, latencia y fragmentos recuperados por llamada.
- Prometheus: latencia y errores por endpoint, llamadas al LLM, preguntas rechazadas por guardrails.

## 8. Calidad y evaluación

- Pruebas unitarias del motor (casos límite: capacidad de ahorro negativa, objetivo inviable, plazo máximo).
- Pruebas de integración de la API con `FakeLLM`.
- Conjunto de evaluación del RAG: preguntas con fragmento esperado (recall en los k primeros) y fidelidad a la fuente.
- Conjunto de evaluación de guardrails: preguntas que deben rechazarse.

## 9. Correspondencia con el guion del Proyecto Júpiter

| Requisito | Dónde se cumple |
|---|---|
| Modelo de IA generativa | Perfilado, asistente, píldoras |
| Base de datos vectorial | pgvector: RAG, temario, guardrails |
| MVP funcional | Flujo completo perfil → objetivos → plan → asistente → formación |
| API de modelo fundacional | Capa `llm/` |
| CI/CD | GitHub Actions |
| Monitorización y logging | Langfuse, Prometheus, logs JSON |
| Docker | Dockerfile por servicio y Docker Compose |
| Pruebas | pytest, unitarias e integradas |

## 10. Decisiones pendientes

- Proveedor del modelo fundacional y modelo de embeddings.
- Valores definitivos de `parametros.yaml` y su justificación.
- Fuentes concretas de la base de conocimiento y su licencia de uso.
- Plataforma cloud de despliegue.
