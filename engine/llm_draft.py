"""Drafts par LLM via Llave (llm-proxy) - Hilo V1 (18/07/2026).

Convention identique a faro-service (faro_generate.appeler_llave) :
POST {LLAVE_URL}/v1/generate, header x-llave-token, corps
{tenant_id, model, max_tokens, system, messages}.
Env requis : LLAVE_URL (base seule), LLAVE_AUTH_TOKEN.
FAIL-OPEN au niveau appelant : toute exception -> fallback template V0.
"""

import json
import os

import httpx

MODELE = os.getenv("HILO_LLM_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.getenv("HILO_LLM_MAX_TOKENS", "1000"))


def _config_llave():
    url = (os.environ.get("LLAVE_URL") or "").strip().rstrip("/")
    if url.endswith("/v1/generate"):
        # Normalisation defensive (incident J22 : chemin double -> 404)
        url = url[: -len("/v1/generate")]
    token = (os.environ.get("LLAVE_AUTH_TOKEN") or "").strip()
    if not url or not token:
        raise RuntimeError("LLAVE_URL/LLAVE_AUTH_TOKEN non configures")
    return url, token


def appeler_llave(tenant_id, system, message_utilisateur):
    """POST /v1/generate ; retourne le texte brut de la reponse."""
    url, token = _config_llave()
    corps = {"tenant_id": tenant_id, "model": MODELE,
             "max_tokens": MAX_TOKENS, "system": system,
             "messages": [{"role": "user", "content": message_utilisateur}]}
    r = httpx.post(url + "/v1/generate", json=corps,
                   headers={"x-llave-token": token}, timeout=60.0)
    if r.status_code >= 400:
        raise RuntimeError("Llave %d: %s" % (r.status_code, r.text[:300]))
    donnees = r.json()
    if isinstance(donnees.get("content"), list):
        return "".join(b.get("text", "") for b in donnees["content"]
                       if isinstance(b, dict))
    for cle in ("text", "completion", "output"):
        if isinstance(donnees.get(cle), str):
            return donnees[cle]
    raise RuntimeError("reponse Llave sans texte exploitable")


def construire_system(profile, canonical, tenant_config):
    langue = profile.get("language", "ES")
    voice = (tenant_config or {}).get("voice_charter", {}) or {}
    signature = voice.get(
        "signature", "Fran\u00e7ois\nVista Serena \u2014 Miches, R.D.")
    faits = json.dumps(canonical, ensure_ascii=True)[:8000]
    return (
        "Tu es Hilo, l'assistant commercial de Vista Serena (terrains et "
        "projets immobiliers a Miches, Republique Dominicaine). Tu rediges "
        "un BROUILLON de reponse a un message prive Instagram recu par "
        "@miches.vistaserena. Un agent humain relira et enverra ce "
        "brouillon ; ne mentionne jamais que tu es une IA.\n\n"
        "REGLES ABSOLUES :\n"
        "- Reponds UNIQUEMENT avec le texte du message (aucun commentaire, "
        "aucune balise, aucun prefixe).\n"
        "- Langue de la reponse : " + langue + ".\n"
        "- Vouvoiement (usted en espagnol), ton chaleureux et professionnel.\n"
        "- MAXIMUM 1 emoji dans tout le message.\n"
        "- Termine par la signature EXACTE :\n" + signature + "\n"
        "- N'invente AUCUN fait (prix, surface, distance, disponibilite) : "
        "utilise exclusivement les FAITS ci-dessous ; si une info manque, "
        "propose d'en parler directement plutot que d'inventer.\n"
        "- Ne JAMAIS confirmer une classification CONFOTUR pour Vista Serena.\n"
        "- Ne JAMAIS citer de chiffres d'appreciation (+40%, +58%) ; au plus "
        "'forte appreciation du marche'.\n"
        "- Si Talipot est mentionne, seul domaine valide : "
        "talipot-ecolodge.com.\n"
        "- Le lien brochure est dans les FAITS (brochures_v3 : base_url + "
        "fichier selon la langue).\n"
        "- Profil detecte : " + str(profile.get("type", "curieux"))
        + " (qualification " + str(profile.get("qualification", "cold"))
        + "). Curieux : reponse courte + 2-3 questions de qualification "
        "(pays, type de projet, budget) + brochure. Prospect : repondre "
        "precisement a ses questions avec les faits, puis proposer un "
        "appel ou WhatsApp. Agent immobilier : refus poli (modele "
        "founder-direct, pas de partenariats de revente).\n\n"
        "REGLES ANTI-ROBOT (sonner humain, jamais chatbot) :\n"
        "- Jamais de formules de chatbot : Excelente pregunta, No dudes "
        "en contactarnos, Espero que esto le ayude, Por supuesto.\n"
        "- Ne jamais feliciter ni valider le message recu ; repondre.\n"
        "- Pas de remplissage : a fin de -> para ; debido al hecho de "
        "que -> porque.\n"
        "- Un seul conditionnel maximum ; prendre position.\n"
        "- Jamais de conclusion creuse (el futuro es prometedor) : finir "
        "sur un fait ou une prochaine etape concrete.\n"
        "- Pas de no solo X sino tambien Y ; dire directement.\n"
        "- Preferer es / tiene a se posiciona como / destaca por.\n"
        "- Varier la longueur des phrases (courtes et longues) ; aucun "
        "gras, aucune liste a etiquettes, pas de tirets cadratins.\n"
        "- Bannir le vocabulaire promo creux : paisaje, crucial, "
        "fomentar, revolucionario, impresionante.\n\n"

        "FAITS (source de verite, JSON) :\n" + faits + "\n"
    )


def generer_draft_llm(message, profile, canonical, tenant_config,
                      lead_context=None):
    """Genere le draft par Llave. Leve une exception si indisponible ou
    reponse suspecte -> l'appelant retombe sur le template V0."""
    if not (message or "").strip():
        raise RuntimeError("message vide")
    system = construire_system(profile, canonical, tenant_config)
    tenant_id = (canonical.get("_meta", {}) or {}).get("tenant",
                                                       "vista-serena")
    texte = (appeler_llave(tenant_id, system, message) or "").strip()
    if len(texte) < 40:
        raise RuntimeError("reponse LLM trop courte (%d)" % len(texte))
    return texte
