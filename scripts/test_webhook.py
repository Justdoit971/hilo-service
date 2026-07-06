"""
Test local du webhook Hilo — simule un message Instagram entrant.

Usage:
    python scripts/test_webhook.py

Prérequis:
    - hilo-service tourne sur http://localhost:8000
    - Supabase configuré (URL + SERVICE_ROLE_KEY dans .env)
"""

import requests
import json


HILO_URL = "http://localhost:9000"


def test_health():
    resp = requests.get(f"{HILO_URL}/health")
    print(f"HEALTH: {resp.status_code} - {resp.json()}")


def test_draft_generation_curieux_es():
    """Simule un message court ES type 'Terreno'."""
    payload = {
        "tenant_slug": "vista-serena",
        "conversation_id": "test-conv-001",
        "incoming_message": "Terreno",
    }
    resp = requests.post(f"{HILO_URL}/draft/generate", json=payload)
    print("\n=== CURIEUX ES ===")
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))


def test_draft_generation_prospect_en():
    """Simule un message riche EN type Jordy."""
    payload = {
        "tenant_slug": "vista-serena",
        "conversation_id": "test-conv-002",
        "incoming_message": "Hi François, I'm interested in Lot B1 or B3 for a single villa with 180° ocean view. My budget is around 300K USD.",
    }
    resp = requests.post(f"{HILO_URL}/draft/generate", json=payload)
    print("\n=== PROSPECT EN ===")
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))


def test_draft_generation_agent_es():
    """Simule un message agent immobilier."""
    payload = {
        "tenant_slug": "vista-serena",
        "conversation_id": "test-conv-003",
        "incoming_message": "Hola, soy de una inmobiliaria y tengo clientes interesados en Miches.",
    }
    resp = requests.post(f"{HILO_URL}/draft/generate", json=payload)
    print("\n=== AGENT ES ===")
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))


def test_red_flag_confotur():
    """Simule un message mentionnant CONFOTUR — devrait lever un RED FLAG."""
    payload = {
        "tenant_slug": "vista-serena",
        "conversation_id": "test-conv-004",
        "incoming_message": "Buenos días, quisiera saber si sus terrenos tienen clasificación CONFOTUR.",
    }
    resp = requests.post(f"{HILO_URL}/draft/generate", json=payload)
    print("\n=== RED FLAG CONFOTUR ===")
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("=" * 60)
    print("Test Hilo POC — génération de drafts")
    print("=" * 60)

    test_health()
    test_draft_generation_curieux_es()
    test_draft_generation_prospect_en()
    test_draft_generation_agent_es()
    test_red_flag_confotur()

    print("\n" + "=" * 60)
    print("Tests terminés.")
    print("=" * 60)
