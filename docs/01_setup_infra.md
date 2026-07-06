# 01 — Setup Infrastructure

**Durée estimée :** 4-6 heures
**Prérequis :** Compte Clever Cloud actif + Compte Supabase gratuit

---

## A — Supabase (30 min)

### 1. Créer un nouveau projet

- Va sur https://supabase.com/dashboard
- Nouveau projet : `hilo-vista-serena`
- Région : **eu-west-1** (RGPD + latence Europe/RD acceptable)
- Mot de passe DB : générer un mot de passe fort (le noter dans un gestionnaire)

### 2. Noter les 3 valeurs critiques

Dans Settings → API :
- `SUPABASE_URL` : `https://xxxxx.supabase.co`
- `SUPABASE_ANON_KEY` : `eyJ...`
- `SUPABASE_SERVICE_ROLE_KEY` : `eyJ...` (à protéger absolument)

### 3. Créer le schéma initial

- SQL Editor → nouveau query
- Copier-coller le contenu de `scripts/init_supabase.sql`
- Run

Résultat attendu :
```
tenants (1 row: vista-serena)
leads (0 rows)
conversations (0 rows)
messages (0 rows)
drafts (0 rows)
audit_log (0 rows)
```

### 4. Activer Row Level Security

Dans SQL Editor :
```sql
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE drafts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_leads ON leads
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
-- (répéter pour les autres tables)
```

---

## B — Clever Cloud pour Chatwoot (2-3 heures)

### 1. Créer une nouvelle application

- Console Clever Cloud → nouvelle app
- Type : **Docker**
- Nom : `chatwoot-hilo`
- Région : Paris (ou Montreal si tu veux proximité RD, à vérifier)

### 2. Base PostgreSQL managée

- Ajouter un **addon PostgreSQL** au moins version 13
- Plan : DEV (gratuit) suffira pour le POC
- Noter les credentials (Clever Cloud les injecte automatiquement)

### 3. Redis addon

- Ajouter un **addon Redis** (obligatoire pour Chatwoot)
- Plan : DEV suffira

### 4. Variables d'environnement Chatwoot

Copier depuis `configs/chatwoot_env.example` et adapter :

```bash
# Base
INSTALLATION_ENV=cleverCloud
NODE_ENV=production
RAILS_ENV=production
SECRET_KEY_BASE=... # générer avec `openssl rand -hex 64`

# DB (Clever Cloud injecte auto)
POSTGRES_HOST=$POSTGRESQL_ADDON_HOST
POSTGRES_PORT=$POSTGRESQL_ADDON_PORT
POSTGRES_DATABASE=$POSTGRESQL_ADDON_DB
POSTGRES_USERNAME=$POSTGRESQL_ADDON_USER
POSTGRES_PASSWORD=$POSTGRESQL_ADDON_PASSWORD

# Redis
REDIS_URL=$REDIS_ADDON_URL

# Frontend
FRONTEND_URL=https://chatwoot-hilo.cleverapps.io

# Mail (à configurer plus tard)
MAILER_SENDER_EMAIL=hilo@vistaserena.com

# Instagram (à remplir jour 2)
FB_APP_ID=
FB_APP_SECRET=
FB_VERIFY_TOKEN=
IG_VERIFY_TOKEN=
```

### 5. Déployer l'image Docker officielle

`Dockerfile` minimaliste (ou tirer directement l'image officielle) :

```dockerfile
FROM chatwoot/chatwoot:v3.10.0-ce
EXPOSE 3000
CMD ["bundle", "exec", "rails", "server", "-b", "0.0.0.0", "-p", "3000"]
```

Sur Clever Cloud :
- Push le repo Git avec Dockerfile
- Clever Cloud build et déploie automatiquement

### 6. Premier accès Chatwoot

- URL : `https://chatwoot-hilo.cleverapps.io`
- Créer le compte super-admin (email + mot de passe)
- Créer un compte "Vista Serena" (représente le tenant)
- Créer une inbox de test (canal API)
- Envoyer un message test → vérifier que ça fonctionne

---

## C — Vérifications finales

- [ ] Chatwoot accessible en HTTPS
- [ ] Login super-admin OK
- [ ] 1 compte "Vista Serena" créé
- [ ] 1 inbox de test créée
- [ ] Supabase accessible depuis dashboard
- [ ] Schéma initial appliqué
- [ ] 1 tenant "vista-serena" créé en DB

---

## 💰 Coûts jour 1 estimés

- Supabase : **0€** (free tier)
- Clever Cloud Chatwoot + PostgreSQL DEV + Redis DEV : ~**15-25€/mois** (à vérifier avec les prix actuels)

---

## 🚨 Blocages possibles

**Chatwoot ne démarre pas :** logs Clever Cloud. Souvent une variable d'env manquante ou une DB pas initialisée.

**Redis addon indisponible :** utiliser un Redis sur upstash.com (free tier) et pointer `REDIS_URL` dessus.

**Coûts trop hauts :** downgrader les addons DEV, ou utiliser un VPS Hetzner CX22 à ~5€/mois avec docker-compose (Chatwoot officiellement supporté).

---

*Fin jour 1 : infra prête pour brancher Instagram le lendemain.*
