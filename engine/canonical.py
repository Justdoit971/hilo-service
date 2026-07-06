"""
Lecture du canonical_facts.json — POC V0

V0 : lecture d'un snapshot local (fichier JSON copié depuis le repo SORIYA).
V1 : appel Mira via HTTP (source de vérité en temps réel).
"""

import json
import os
from pathlib import Path


CANONICAL_PATH = os.getenv(
    "CANONICAL_PATH",
    str(Path(__file__).parent.parent / "configs" / "canonical_snapshot.json"),
)


def load_canonical_snapshot() -> dict:
    """Charge le snapshot canonical au démarrage du service."""
    try:
        with open(CANONICAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback : canonical minimal pour éviter le crash
        return {
            "_meta": {"version": "unknown", "tenant": "vista-serena"},
            "brochures_v3": {"base_url": "", "es": "", "en": "", "fr": ""},
        }


def reload_canonical() -> dict:
    """
    Recharge le canonical depuis le fichier.
    À appeler périodiquement (ex: toutes les heures via cron/scheduler).
    """
    return load_canonical_snapshot()
