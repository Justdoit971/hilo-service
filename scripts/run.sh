#!/bin/bash
# SORIYA / Hilo - wrapper de demarrage Clever Cloud (pattern maison eprouve)
# Nginx Clever ecoute :8080 et forwarde vers :9000 -> uvicorn DOIT etre sur 9000.
# CC_RUN_COMMAND n est pas fiable pour les commandes composees -> ce script commite.
set -e
export PYTHONUNBUFFERED=1
echo "[RUN] demarrage hilo-service (uvicorn :9000)"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-9000}"
