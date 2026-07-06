"""
Génération de draft — POC V0

V0 : templates statiques par profil × langue.
V1 : appel Claude API avec system prompt Hilo + contexte lead.
"""

from typing import Optional


# ============================================
# Templates par profil × langue
# ============================================

TEMPLATES_CURIEUX = {
    "ES": """Hola, gracias por su interés en Vista Serena 🌴

Para enviarle información personalizada, ¿podría compartir conmigo?:

1. ¿Desde qué país nos contacta?
2. ¿Qué tipo de proyecto le interesa (villa privada, inversión, proyecto turístico)?
3. ¿Tiene un presupuesto aproximado en mente?

Mientras tanto, aquí tiene el folleto completo:
📄 {brochure_url}

🌐 www.michesvistaserena.com

Quedo atento a su respuesta.

François
Vista Serena — Miches, R.D.""",

    "EN": """Hi, thanks for your interest in Vista Serena 🌴

To share personalized information with you, could you tell me:

1. Which country are you contacting us from?
2. What type of project are you interested in (private villa, investment, tourism project)?
3. Do you have an approximate budget in mind?

In the meantime, here's our complete brochure:
📄 {brochure_url}

🌐 www.michesvistaserena.com

Looking forward to your reply.

François
Vista Serena — Miches, R.D.""",

    "FR": """Bonjour, merci de votre intérêt pour Vista Serena 🌴

Pour vous envoyer des informations personnalisées, pourriez-vous m'indiquer :

1. Depuis quel pays nous contactez-vous ?
2. Quel type de projet vous intéresse (villa privée, investissement, projet touristique) ?
3. Avez-vous un budget approximatif en tête ?

En attendant, voici notre brochure complète :
📄 {brochure_url}

🌐 www.michesvistaserena.com

Je reste à votre disposition.

François
Vista Serena — Miches, R.D.""",
}


TEMPLATES_AGENT = {
    "ES": """Hola, gracias por su mensaje.

Vista Serena gestiona directamente la comercialización de sus terrenos sin intermediarios (modelo founder-direct). Actualmente no estamos abiertos a partenariados de reventa o referrals.

Si en el futuro decidimos abrir canales de distribución profesional, le contactaremos con gusto.

Saludos cordiales,

François
Vista Serena — Miches, R.D.""",

    "EN": """Hello, thank you for your message.

Vista Serena handles the commercialization of its lots directly without intermediaries (founder-direct model). We are not currently open to reselling partnerships or referral programs.

If we decide to open professional distribution channels in the future, we will be glad to reach out.

Best regards,

François
Vista Serena — Miches, R.D.""",

    "FR": """Bonjour, merci pour votre message.

Vista Serena gère directement la commercialisation de ses terrains sans intermédiaires (modèle founder-direct). Nous ne sommes pas ouverts pour le moment à des partenariats de revente ou de mise en relation.

Si à l'avenir nous décidons d'ouvrir des canaux de distribution professionnels, nous vous recontacterons avec plaisir.

Cordialement,

François
Vista Serena — Miches, R.D.""",
}


TEMPLATE_PROSPECT_PREFACE = {
    "ES": "Buenos días, gracias por su interés en Vista Serena 🌴\n\n[DRAFT PROSPECT — à personnaliser selon le message reçu]\n\n",
    "EN": "Hi, thanks for your interest in Vista Serena 🌴\n\n[DRAFT PROSPECT — to personalize based on the message received]\n\n",
    "FR": "Bonjour, merci de votre intérêt pour Vista Serena 🌴\n\n[DRAFT PROSPECT — à personnaliser selon le message reçu]\n\n",
}


# ============================================
# Récupération brochure selon langue
# ============================================
def get_brochure_url(language: str, canonical: dict) -> str:
    """Retourne l'URL brochure v3 depuis le canonical."""
    brochures = canonical.get("brochures_v3", {})
    base = brochures.get("base_url", "")
    filename = brochures.get(language.lower(), brochures.get("es", ""))
    return f"{base}{filename}"


# ============================================
# Fonction principale
# ============================================
def generate_draft(
    message: str,
    profile: dict,
    canonical: dict,
    tenant_config: dict,
    lead_context: Optional[dict] = None,
) -> str:
    """
    Génère un draft de réponse à partir du profil détecté.

    V0 : templates statiques.
    V1 : appel LLM Claude avec contexte enrichi.
    """
    profile_type = profile.get("type", "curieux")
    language = profile.get("language", "ES")

    if profile_type == "curieux":
        template = TEMPLATES_CURIEUX.get(language, TEMPLATES_CURIEUX["ES"])
        brochure_url = get_brochure_url(language, canonical)
        return template.format(brochure_url=brochure_url)

    if profile_type == "agent":
        return TEMPLATES_AGENT.get(language, TEMPLATES_AGENT["ES"])

    if profile_type == "prospect":
        # Pour un prospect, on envoie un début de template + note qu'il faut personnaliser
        preface = TEMPLATE_PROSPECT_PREFACE.get(language, TEMPLATE_PROSPECT_PREFACE["ES"])
        brochure_url = get_brochure_url(language, canonical)
        return preface + f"📄 {brochure_url}\n\nFrançois\nVista Serena — Miches, R.D."

    # Fallback
    return TEMPLATES_CURIEUX["ES"].format(brochure_url=get_brochure_url("ES", canonical))
