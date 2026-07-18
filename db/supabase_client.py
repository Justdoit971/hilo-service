"""Client Supabase pour Hilo - POC V0 (adapte SORIYA 2026-07-05).

Adaptations vs POC d'origine :
  - Schema dedie "hilo" (projet soriya-dev) via ClientOptions(schema="hilo").
    Prerequis : "hilo" ajoute aux Exposed schemas (Dashboard > Settings > API).
  - tenant_id = slug TEXT ('vista-serena'), convention maison : plus de table
    tenants a UUID ni de resolution slug->uuid.
Toutes les operations DB passent par ici. Lib supabase-py.
"""

import os
from datetime import datetime, timezone
from typing import Optional

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions


SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                "SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent etre configures")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY,
                                options=ClientOptions(schema="hilo"))
    return _client


# ============================================
# Tenants
# ============================================
def get_tenant_config(tenant_id: str) -> dict:
    """Config runtime du tenant depuis hilo.tenants (jsonb config)."""
    client = get_client()
    resp = (client.table("tenants").select("config")
            .eq("tenant_id", tenant_id).execute())
    if not resp.data:
        raise ValueError("Tenant '%s' introuvable dans hilo.tenants" % tenant_id)
    return resp.data[0]["config"] or {}


# ============================================
# Leads
# ============================================
def get_or_create_lead(
    tenant_id: str,
    sender: dict,
    channel: str,
    profile: dict,
) -> dict:
    """Recherche ou cree un lead a partir des infos sender Chatwoot."""
    client = get_client()

    chatwoot_contact_id = str(sender.get("id", ""))
    sender_name = sender.get("name", "unknown")

    existing = (
        client.table("leads")
        .select("*")
        .eq("tenant_id", tenant_id)
        .contains("external_ids", {"chatwoot_contact_id": chatwoot_contact_id})
        .execute()
    )

    if existing.data:
        lead = existing.data[0]
        client.table("leads").update({
            "last_interaction_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", lead["id"]).execute()
        return lead

    lead_id_str = generate_next_lead_id(tenant_id)

    new_lead = {
        "tenant_id": tenant_id,
        "lead_id": lead_id_str,
        "name": sender_name,
        "source": profile.get("source", "instagram"),
        "language": profile.get("language", "ES"),
        "contact_type": profile.get("type", "curieux"),
        "produit_interet": "vista-serena-terrain",
        "qualification": profile.get("qualification", "cold"),
        "next_step": "Suivi",
        "is_attributable_ig": profile.get("source") in ["instagram", "whatsapp"],
        "external_ids": {"chatwoot_contact_id": chatwoot_contact_id},
    }

    resp = client.table("leads").insert(new_lead).execute()
    return resp.data[0]


def generate_next_lead_id(tenant_id: str) -> str:
    """Genere le prochain lead_id au format L-YYYY-NNN (contrat Veris)."""
    client = get_client()
    year = datetime.now().year
    prefix = "L-%d-" % year

    resp = (
        client.table("leads")
        .select("lead_id")
        .eq("tenant_id", tenant_id)
        .like("lead_id", prefix + "%")
        .order("lead_id", desc=True)
        .limit(1)
        .execute()
    )

    if not resp.data:
        return prefix + "001"

    last_id = resp.data[0]["lead_id"]
    last_num = int(last_id.split("-")[-1])
    return "%s%03d" % (prefix, last_num + 1)


# ============================================
# Conversations
# ============================================
def save_conversation(
    tenant_id: str,
    lead_id: str,
    chatwoot_conv_id: int,
    channel: str,
) -> dict:
    client = get_client()

    existing = (
        client.table("conversations")
        .select("*")
        .eq("tenant_id", tenant_id)
        .eq("chatwoot_conversation_id", chatwoot_conv_id)
        .execute()
    )

    if existing.data:
        return existing.data[0]

    new_conv = {
        "tenant_id": tenant_id,
        "lead_id": lead_id,
        "channel": channel,
        "chatwoot_conversation_id": chatwoot_conv_id,
        "status": "open",
    }
    resp = client.table("conversations").insert(new_conv).execute()
    return resp.data[0]


# ============================================
# Messages
# ============================================
def save_message(
    tenant_id: str,
    conversation_id: str,
    direction: str,
    sender_type: str,
    content: str,
    chatwoot_message_id: Optional[int] = None,
    metadata: Optional[dict] = None,
) -> dict:
    client = get_client()

    new_msg = {
        "tenant_id": tenant_id,
        "conversation_id": conversation_id,
        "direction": direction,
        "sender_type": sender_type,
        "content": content,
        "chatwoot_message_id": chatwoot_message_id,
        "metadata": metadata or {},
    }
    resp = client.table("messages").insert(new_msg).execute()
    return resp.data[0]


# ============================================
# Drafts
# ============================================
def save_draft(
    tenant_id: str,
    conversation_id: str,
    triggered_by_message_id: str,
    original_draft: str,
    hilo_analysis: dict,
) -> dict:
    client = get_client()

    new_draft = {
        "tenant_id": tenant_id,
        "conversation_id": conversation_id,
        "triggered_by_message_id": triggered_by_message_id,
        "original_draft": original_draft,
        "hilo_analysis": hilo_analysis,
        "status": "pending",
    }
    resp = client.table("drafts").insert(new_draft).execute()
    return resp.data[0]


def mark_draft_sent(draft_id: str, sent_version: str, edit_diff: str = "") -> dict:
    client = get_client()
    resp = (
        client.table("drafts")
        .update({
            "sent_version": sent_version,
            "edit_diff": edit_diff,
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("id", draft_id)
        .execute()
    )
    return resp.data[0]


# ============================================
# Audit log
# ============================================
def log_audit(
    tenant_id: str,
    actor: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    before_data: Optional[dict] = None,
    after_data: Optional[dict] = None,
) -> dict:
    client = get_client()

    entry = {
        "tenant_id": tenant_id,
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "before_data": before_data,
        "after_data": after_data,
    }
    resp = client.table("audit_log").insert(entry).execute()
    return resp.data[0]


# ============================================
# Public schema (public.leads) - miroir console / Veris
# ============================================
_public_client: Optional[Client] = None


def get_public_client() -> Client:
    """Client Supabase schema PUBLIC (pas hilo) pour ecrire dans public.leads,
    la table lue par la console Soriya et Veris."""
    global _public_client
    if _public_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                "SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent etre configures")
        _public_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _public_client


def mirror_lead_to_public(tenant_id, sender, profile, lead_hilo):
    """Recopie / met a jour le lead dans public.leads via les MEMES RPC que la
    console (lead_insert / lead_update / leads_ingest_*). Dedup par huella
    'cw:<chatwoot_contact_id>'. Retourne le lead_id public (ou None)."""
    pub = get_public_client()
    sender = sender or {}
    lead_hilo = lead_hilo or {}
    contact_id = str(sender.get("id", ""))
    if not contact_id:
        return None

    huella = "cw:%s" % contact_id
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    changes = {
        "name": lead_hilo.get("name") or sender.get("name"),
        "source": profile.get("source", "instagram"),
        "language": profile.get("language", "ES"),
        "contact_type": profile.get("type", "curieux"),
        "produit_interet": lead_hilo.get("produit_interet", "vista-serena-terrain"),
        "qualification": profile.get("qualification", "cold"),
        "next_step": lead_hilo.get("next_step", "Suivi"),
        "last_interaction": now_iso,
    }

    seen = pub.rpc("leads_ingest_get", {"t": tenant_id, "h": huella}).execute()
    seen_data = seen.data if getattr(seen, "data", None) else None

    if seen_data and isinstance(seen_data, dict) and seen_data.get("lead_id"):
        pub_lead_id = seen_data["lead_id"]
        pub.rpc("lead_update", {"t": tenant_id, "lid": pub_lead_id,
                                "changes": changes, "who": "hilo-service"}).execute()
    else:
        changes["date_contact"] = now_iso[:10]
        ins = pub.rpc("lead_insert", {"t": tenant_id, "changes": changes,
                                      "who": "hilo-service"}).execute()
        pub_lead_id = ins.data
        if pub_lead_id:
            pub.rpc("leads_ingest_add", {"t": tenant_id, "h": huella,
                                         "lid": pub_lead_id, "who_": "hilo-service"}).execute()

    if pub_lead_id and profile.get("source") in ("instagram", "whatsapp"):
        pub.table("leads").update({"is_attributable_ig": 1}).eq("tenant_id", tenant_id).eq("lead_id", pub_lead_id).execute()

    return pub_lead_id
