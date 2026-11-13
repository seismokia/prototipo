"""Streamlit frontend. It only talks to the API over HTTP."""

import os

import httpx
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")
REQUEST_TIMEOUT_SECONDS = 5.0

AVISO_LEGAL = (
    "Herramienta de planificación y educación financiera con datos sintéticos. "
    "No constituye asesoramiento en materia de inversión ni recomienda productos concretos."
)


def fetch_health() -> dict[str, str]:
    response = httpx.get(f"{API_URL}/health", timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title="Asistente patrimonial", page_icon="💶")
st.title("Asistente patrimonial")
st.caption("Prototipo — planificación financiera por objetivos")

st.subheader("Estado de la API")
try:
    health = fetch_health()
except httpx.HTTPError as error:
    st.error(f"No se puede contactar con la API en {API_URL}: {error}")
else:
    st.success("La API está operativa.")
    st.json(health)

if st.button("Volver a comprobar"):
    st.rerun()

st.divider()
st.caption(f"⚠️ {AVISO_LEGAL}")
