"""
Détection de profil client — POC V0

Version simplifiée qui applique la grille de qualification Hilo :
- curieux : message court, aucun signal qualifiant
- prospect : nom + questions structurées OU projet précis
- agent : mots-clés "inmobiliaria", "realty", "estrategias comerciales"
- client : lead déjà connu et en pipeline avancé

Version V1 : remplacée par appel LLM Claude pour analyse fine.
"""

import re
from typing import Optional


# ============================================
# Détection langue
# ============================================
def detect_language(message: str) -> str:
    """Détection simple par mots-clés."""
    msg = message.lower()

    # Espagnol
    es_markers = [
        "hola", "buenos", "buenas", "gracias", "quiero", "quisiera",
        "podría", "podria", "información", "información", "precio",
        "terreno", "inversión", "inversion", "cuánto", "cuando",
        "usted", "es", "está", "estoy"
    ]
    # Anglais
    en_markers = [
        "hi", "hello", "thanks", "thank you", "please", "i'm",
        "would like", "could you", "how much", "when", "where",
        "interested", "budget", "villa", "land", "invest"
    ]
    # Français
    fr_markers = [
        "bonjour", "bonsoir", "merci", "je voudrais", "pouvez-vous",
        "combien", "quand", "terrain", "investissement",
        "intéressé", "villa", "budget"
    ]

    scores = {
        "ES": sum(1 for m in es_markers if m in msg),
        "EN": sum(1 for m in en_markers if m in msg),
        "FR": sum(1 for m in fr_markers if m in msg),
    }

    max_lang = max(scores, key=scores.get)
    if scores[max_lang] == 0:
        return "ES"  # défaut Vista Serena

    return max_lang


# ============================================
# Détection type de profil
# ============================================
def detect_profile_type(message: str, sender_info: dict) -> str:
    """
    Retourne : 'curieux' | 'prospect' | 'agent' | 'inconnu'
    """
    msg = message.lower()
    sender_name = sender_info.get("name", "").lower() if sender_info else ""

    # 1. Détection AGENT
    agent_keywords = [
        "inmobiliaria", "realty", "real estate",
        "estrategias comerciales", "broker", "agente",
        "referral", "co-broking", "mls"
    ]
    if any(kw in msg or kw in sender_name for kw in agent_keywords):
        return "agent"

    # 2. Détection PROSPECT (signaux forts)
    prospect_signals = 0

    # Longueur message > 100 caractères = signal
    if len(message) > 100:
        prospect_signals += 1

    # Mentions de lots spécifiques
    if re.search(r"\b(lot|lote|parcela)\s*[a-f][1-6]?\b", msg):
        prospect_signals += 2

    # Mentions de budget
    if re.search(r"\b(usd|dollars?|dolares|budget|presupuesto|\$)\s*\d", msg):
        prospect_signals += 2

    # Mentions de projet
    if any(kw in msg for kw in ["villa", "eco-lodge", "hotel", "inversión", "invest", "proyecto"]):
        prospect_signals += 1

    # Questions structurées
    question_count = msg.count("?")
    if question_count >= 2:
        prospect_signals += 1

    # Mention géographie (pays, ville)
    if any(kw in msg for kw in ["desde", "vengo de", "from", "based in", "paris", "madrid", "miami", "new york"]):
        prospect_signals += 1

    if prospect_signals >= 2:
        return "prospect"

    # 3. Par défaut : CURIEUX
    return "curieux"


# ============================================
# Détection source (via message d'entrée)
# ============================================
def detect_source(message: str, channel: str) -> str:
    """
    Retourne le champ 'source' canonical.
    """
    msg = message.lower()

    # Landing Page Google Ads
    if "landing page" in msg or "google ads" in msg:
        return "google_ads"

    # SEO / trouvé sur Google
    if "google" in msg and ("encontré" in msg or "found" in msg or "trouvé" in msg):
        return "seo_organic"

    # Référencé par quelqu'un
    if any(kw in msg for kw in ["me hablaron", "on m'a parlé", "referred by", "recomendado"]):
        return "referral"

    # Instagram (mention explicite)
    if "instagram" in msg or "ig" in msg:
        return "instagram"

    # Par canal Chatwoot
    if channel == "instagram_dm":
        return "instagram"
    if channel == "whatsapp":
        return "whatsapp"
    if channel == "email":
        return "email"

    return "direct"


# ============================================
# Fonction principale
# ============================================
def detect_profile(message: str, tenant_config: dict, sender_info: Optional[dict] = None, channel: Optional[str] = None) -> dict:
    """
    Analyse complète d'un message entrant.

    Retourne :
    {
        "type": "curieux" | "prospect" | "agent",
        "language": "ES" | "EN" | "FR",
        "source": "instagram" | "whatsapp" | ...,
        "qualification": "cold" | "warm" | "hot",
        "signals": [...],
    }
    """
    sender_info = sender_info or {}
    channel = channel or "instagram_dm"

    profile_type = detect_profile_type(message, sender_info)
    language = detect_language(message)
    source = detect_source(message, channel)

    # Qualification initiale
    qualification_map = {
        "curieux": "cold",
        "prospect": "warm",
        "agent": "perdu",
    }
    qualification = qualification_map.get(profile_type, "cold")

    return {
        "type": profile_type,
        "language": language,
        "source": source,
        "qualification": qualification,
        "channel": channel,
    }
