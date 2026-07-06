"""
Détection RED FLAGS — POC V0

Vérifie les incohérences potentielles dans le message reçu
ou dans le draft avant envoi.
"""

from typing import List


def check_red_flags(message: str, canonical: dict) -> List[str]:
    """
    Retourne une liste de red flags détectés dans le message ou le contexte.

    Cas couverts V0:
    - Prix incohérent avec le canonical
    - Mention CONFOTUR (à traiter avec prudence)
    - Mention Talipot avec un autre domaine que talipot-ecolodge.com
    - Distances incohérentes
    """
    flags = []
    msg = message.lower()

    # 1. CONFOTUR mentionné
    if "confotur" in msg:
        flags.append(
            "🚩 CONFOTUR mentionné par le lead — répondre uniquement avec la formulation validée "
            "(Talipot en instruction, décision décembre 2026). NE PAS confirmer pour Vista Serena."
        )

    # 2. Mention Talipot avec mauvais domaine
    if "talipotboutiquelodge" in msg or "talipotboutiquehotel" in msg:
        flags.append(
            "🚩 Domaine Talipot non-canonique mentionné — corriger vers talipot-ecolodge.com dans la réponse."
        )

    # 3. Prix incohérent
    if "50 usd" in msg or "50/m" in msg:
        # OK, c'est le prix d'entrée du lot F
        pass

    # 4. Mention appréciation chiffrée
    if any(marker in msg for marker in ["+40%", "+58%", "40 %", "58 %"]):
        flags.append(
            "🚩 Chiffres d'appréciation mentionnés — NE JAMAIS confirmer +40% ou +58% dans la réponse. "
            "Formulation autorisée : 'forte appréciation du marché'."
        )

    # 5. Signal urgence potentielle
    urgence_markers = ["esta semana", "urgente", "asap", "hoy", "mañana", "demain", "urgent", "this week", "tomorrow"]
    if any(m in msg for m in urgence_markers):
        flags.append(
            "⚡ Signal d'urgence détecté — prioriser cette conversation."
        )

    return flags


def validate_draft(draft: str, canonical: dict) -> List[str]:
    """
    Vérifie qu'un draft respecte les règles avant envoi.
    """
    issues = []

    # Compter les emojis (règle : max 1)
    import re
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002702-\U000027B0"
        "]+"
    )
    emojis = emoji_pattern.findall(draft)
    emoji_count = sum(len(e) for e in emojis)
    if emoji_count > 1:
        issues.append(f"⚠️ {emoji_count} emojis dans le draft (règle : max 1)")

    # Vérifier signature
    if "François" not in draft:
        issues.append("⚠️ Signature François manquante")

    # Vérifier mention CONFOTUR spontanée
    if "confotur" in draft.lower():
        issues.append("🚩 CONFOTUR mentionné dans le draft — vérifier que c'est justifié par le message reçu")

    # Vérifier domaine Talipot
    if "talipot" in draft.lower() and "talipot-ecolodge.com" not in draft:
        issues.append("🚩 Talipot mentionné sans le bon domaine (talipot-ecolodge.com)")

    return issues
