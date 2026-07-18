"""
Hilo Service — POC V0
======================

FastAPI service qui reçoit les webhooks Chatwoot et produit des drafts.

Endpoints:
    POST /webhook/chatwoot     Reçoit les événements Chatwoot (nouveau message, etc.)
    POST /draft/generate       Génère un draft à la demande
    GET  /health               Healthcheck
    GET  /                     Info service

Environnement:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY
    CHATWOOT_URL
    CHATWOOT_API_TOKEN
    ANTHROPIC_API_KEY
"""

import os
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

from engine.profile_detection import detect_profile
from engine.response_generator import generate_draft
from engine.canonical import load_canonical_snapshot
from engine.validators import check_red_flags
from db.supabase_client import (
    get_tenant_config as db_get_tenant_config,
    get_or_create_lead,
    save_conversation,
    save_message,
    save_draft,
    log_audit,
    mirror_lead_to_public,
)

# ============================================
# Setup
# ============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hilo")

app = FastAPI(title="Hilo Service", version="0.1.0-poc")

# Canonical chargé en mémoire au démarrage (V1 = snapshot local)
CANONICAL = load_canonical_snapshot()


# ============================================
# Models
# ============================================
class ChatwootWebhookPayload(BaseModel):
    """
    Payload minimal Chatwoot pour événement 'message_created'.
    Voir https://www.chatwoot.com/docs/product/others/webhooks
    """
    event: str
    id: Optional[int] = None
    content: Optional[str] = None
    message_type: Optional[str] = None  # 'incoming' | 'outgoing'
    conversation: Optional[dict] = None
    sender: Optional[dict] = None
    account: Optional[dict] = None
    inbox: Optional[dict] = None


class DraftGenerateRequest(BaseModel):
    tenant_slug: str
    conversation_id: str
    incoming_message: str
    lead_context: Optional[dict] = None


# ============================================
# Endpoints
# ============================================

@app.get("/")
def root():
    return {
        "service": "Hilo",
        "version": "0.1.0-poc",
        "tenant_default": "vista-serena",
        "canonical_version": CANONICAL.get("_meta", {}).get("version"),
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/webhook/chatwoot")
async def chatwoot_webhook(
    payload: ChatwootWebhookPayload,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """
    Handler principal des webhooks Chatwoot.

    On ne traite que les messages entrants (message_type == 'incoming').
    Le traitement est mis en background pour répondre 200 vite à Chatwoot.
    """
    # Regle 11 : secret partage sur l'URL du webhook
    _secret = os.getenv("HILO_WEBHOOK_SECRET")
    if _secret and request.query_params.get("token") != _secret:
        raise HTTPException(status_code=401, detail="invalid webhook token")

    logger.info(f"Webhook received: event={payload.event}")

    # On ne gère que message_created pour le POC
    if payload.event != "message_created":
        return {"status": "ignored", "reason": "event_not_handled"}

    if payload.message_type != "incoming":
        return {"status": "ignored", "reason": "not_incoming_message"}

    # Traitement en background
    background_tasks.add_task(
        process_incoming_message,
        payload.model_dump(),
    )

    return {"status": "accepted", "message": "Draft will be generated"}


@app.post("/draft/generate")
def draft_generate(req: DraftGenerateRequest):
    """
    Génération de draft à la demande (utile pour tests + retry).
    """
    tenant_config = get_tenant_config(req.tenant_slug)
    profile_analysis = detect_profile(req.incoming_message, tenant_config)
    red_flags = check_red_flags(req.incoming_message, CANONICAL)

    draft_text = generate_draft(
        message=req.incoming_message,
        profile=profile_analysis,
        canonical=CANONICAL,
        tenant_config=tenant_config,
        lead_context=req.lead_context or {},
    )

    return {
        "draft": draft_text,
        "profile": profile_analysis,
        "red_flags": red_flags,
        "canonical_version": CANONICAL["_meta"]["version"],
    }


# ============================================
# Business logic
# ============================================

def process_incoming_message(payload: dict):
    """
    Workflow complet:
    1. Extraire les infos utiles du payload Chatwoot
    2. Créer/mettre à jour le lead en Supabase
    3. Enregistrer la conversation + message
    4. Détecter profil + langue + source
    5. Générer draft
    6. Poster le draft comme note interne dans Chatwoot
    7. Audit log
    """
    try:
        tenant_slug = "vista-serena"  # POC: hardcoded
        tenant_config = get_tenant_config(tenant_slug)

        conv = payload.get("conversation", {})
        sender = payload.get("sender", {})
        inbox = payload.get("inbox", {})

        chatwoot_conv_id = conv.get("id")
        content = payload.get("content", "")

        # 1. Détection profil
        profile = detect_profile(content, tenant_config)
        logger.info(f"Profile detected: {profile}")

        # 2. Lead upsert
        lead = get_or_create_lead(
            tenant_id=tenant_slug,
            sender=sender,
            channel=inbox.get("channel_type", "instagram_dm"),
            profile=profile,
        )

        # 2b. Miroir vers public.leads (console + Veris) - non bloquant
        try:
            _pub_id = mirror_lead_to_public(tenant_slug, sender, profile, lead)
            logger.info(f"Lead mirrored to public.leads: {_pub_id}")
        except Exception as _e:
            logger.exception(f"Mirror public.leads failed (non-blocking): {_e}")

        # 3. Conversation
        conversation = save_conversation(
            tenant_id=tenant_slug,
            lead_id=lead["id"],
            chatwoot_conv_id=chatwoot_conv_id,
            channel=inbox.get("channel_type", "instagram_dm"),
        )

        # 4. Message
        message = save_message(
            tenant_id=tenant_slug,
            conversation_id=conversation["id"],
            direction="inbound",
            sender_type="lead",
            content=content,
            chatwoot_message_id=payload.get("id"),
        )

        # 5. RED FLAGS
        red_flags = check_red_flags(content, CANONICAL)
        if red_flags:
            logger.warning(f"RED FLAGS detected: {red_flags}")

        # 6. Générer draft
        draft_text = generate_draft(
            message=content,
            profile=profile,
            canonical=CANONICAL,
            tenant_config=tenant_config,
            lead_context={"lead": lead},
        )

        # 7. Sauvegarder le draft
        draft = save_draft(
            tenant_id=tenant_slug,
            conversation_id=conversation["id"],
            triggered_by_message_id=message["id"],
            original_draft=draft_text,
            hilo_analysis={
                "profile": profile,
                "red_flags": red_flags,
                "canonical_version": CANONICAL["_meta"]["version"],
            },
        )

        # 8. Poster comme note interne dans Chatwoot
        post_draft_to_chatwoot(
            chatwoot_conv_id=chatwoot_conv_id,
            draft_text=draft_text,
            profile=profile,
            red_flags=red_flags,
        )

        # 9. Audit log
        log_audit(
            tenant_id=tenant_slug,
            actor="hilo-service",
            action="draft_generated",
            entity_type="draft",
            entity_id=draft["id"],
            after_data={"draft_length": len(draft_text)},
        )

        logger.info(f"Draft generated and posted for conv {chatwoot_conv_id}")

    except Exception as e:
        logger.exception(f"Error processing message: {e}")


def post_draft_to_chatwoot(
    chatwoot_conv_id: int,
    draft_text: str,
    profile: dict,
    red_flags: list,
):
    """
    Poste le draft dans Chatwoot comme note privée (private note).
    L'agent la voit, la modifie, puis envoie manuellement.
    """
    import requests

    chatwoot_url = os.getenv("CHATWOOT_URL")
    chatwoot_token = os.getenv("CHATWOOT_API_TOKEN")
    account_id = os.getenv("CHATWOOT_ACCOUNT_ID", "1")

    if not chatwoot_url or not chatwoot_token:
        logger.error("Chatwoot credentials not configured")
        return

    # Construction de la note interne
    note_parts = [
        "🌴 **Draft Hilo**",
        "",
        draft_text,
        "",
        "---",
        f"📊 Profil détecté: **{profile.get('type', 'unknown')}** ({profile.get('language', '?')})",
    ]

    if red_flags:
        note_parts.append("")
        note_parts.append("🚩 **RED FLAGS**:")
        for rf in red_flags:
            note_parts.append(f"- {rf}")

    note_content = "\n".join(note_parts)

    url = f"{chatwoot_url}/api/v1/accounts/{account_id}/conversations/{chatwoot_conv_id}/messages"
    headers = {
        "api_access_token": chatwoot_token,
        "Content-Type": "application/json",
    }
    body = {
        "content": note_content,
        "message_type": "outgoing",
        "private": True,  # NOTE INTERNE, pas envoyée au client
    }

    resp = requests.post(url, json=body, headers=headers, timeout=10)
    if resp.status_code >= 400:
        logger.error(f"Chatwoot post error: {resp.status_code} - {resp.text}")
    else:
        logger.info(f"Draft posted as private note in conv {chatwoot_conv_id}")


def get_tenant_config(tenant_slug: str) -> dict:
    """Config tenant : Supabase (hilo.tenants) d'abord, fallback fichier local
    (permet les tests sans base)."""
    try:
        return db_get_tenant_config(tenant_slug)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Config tenant via Supabase indisponible ({e}), fallback local")
        import json
        with open("configs/tenant_vista_serena.json", encoding="utf-8") as f:
            return json.load(f)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
