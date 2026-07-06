# hilo-service

SORIYA - Casquette Hilo : CRM conversationnel (POC V0).
Webhooks Chatwoot -> detection profil/langue/RED FLAGS -> draft -> note interne
Chatwoot -> persistance Supabase (schema `hilo`, projet soriya-dev).

Adaptations vs POC d'origine (decisions 2026-07-05) :
- Projet Supabase existant `soriya-dev`, schema dedie `hilo` (Exposed schemas !)
- `tenant_id` TEXT ('vista-serena'), convention SORIYA
- Deploiement Clever pattern maison : app Python + `scripts/run.sh` (port 9000),
  pas de Docker pour ce service (Chatwoot, lui, reste en Docker officiel)

## Demarrage local
    pip install -r requirements.txt
    cp .env.example .env   # remplir
    uvicorn main:app --reload --port 9000
    python scripts/test_webhook.py

## Deploiement Clever
    App Python, CC_RUN_COMMAND = bash scripts/run.sh
    Variables d'env = contenu du .env

Docs jour par jour : `docs/01..04_*.md`. Schema DB : `scripts/init_supabase.sql`
(deja installe dans soriya-dev le 2026-07-05).
