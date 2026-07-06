# 03 — Déploiement Hilo Service

**Durée estimée :** 4-6 heures
**Prérequis :** Jour 1 + Jour 2 OK

---

## A — Développement local (2h)

### 1. Cloner le POC et installer

```bash
cd poc-hilo-app/hilo-service
python -m venv .venv
source .venv/bin/activate   # ou .venv\Scripts\activate sur Windows
pip install -r requirements.txt
```

### 2. Configurer les variables

```bash
cp .env.example .env
# Éditer .env avec tes vraies valeurs Supabase, Chatwoot, Anthropic
```

### 3. Lancer en local

```bash
uvicorn main:app --reload
```

### 4. Tester avec le script

```bash
python ../scripts/test_webhook.py
```

Tu dois voir :
- `HEALTH: 200`
- 4 drafts générés pour les 4 cas de test (curieux ES, prospect EN, agent ES, red flag CONFOTUR)

---

## B — Déploiement Clever Cloud (2h)

### 1. Créer une nouvelle app Clever Cloud

- Type : **Python** ou **Docker** (préférence Docker pour maîtriser)
- Nom : `hilo-service`
- Région : Paris (proche Chatwoot)

### 2. Variables d'env

Depuis le dashboard Clever Cloud → Environment variables :

Copier toutes les variables du `.env.example` remplies avec les vraies valeurs.

### 3. Deploy

```bash
git add .
git commit -m "hilo-service: POC V0"
git push clever main
```

Clever Cloud build et déploie automatiquement.

### 4. Vérifier

```bash
curl https://hilo-service.cleverapps.io/
# {"service":"Hilo","version":"0.1.0-poc",...}

curl https://hilo-service.cleverapps.io/health
# {"status":"ok",...}
```

---

## C — Connecter Chatwoot à Hilo (1h)

### 1. Créer un Webhook Chatwoot

Dans Chatwoot → Settings → Integrations → Webhooks → Add new webhook :

- **URL** : `https://hilo-service.cleverapps.io/webhook/chatwoot`
- **Événements** :
  - ✅ `Message Created`
  - ✅ `Conversation Created`

### 2. Créer un API token Chatwoot

Dans Chatwoot → Profile → Access Token → Copy

→ Coller cette valeur dans `CHATWOOT_API_TOKEN` de Hilo-service (et redéployer).

### 3. Test end-to-end

- Envoyer un DM Instagram vers `@miches.vistaserena` : `Terreno`
- Aller dans Chatwoot → Conversations
- Dans les 5 secondes, une **note interne** (fond jaune) doit apparaître avec le draft Hilo
- La note contient : le draft + le profil détecté + les RED FLAGS éventuels

---

## D — Modification et envoi (30 min)

### Workflow validé

1. Lire la note interne Hilo dans Chatwoot
2. Copier le contenu utile (juste la réponse, sans les métadonnées Hilo)
3. Coller dans la zone de saisie Chatwoot
4. Modifier si nécessaire
5. Envoyer

**Amélioration V0.1 (optionnelle)** : ajouter un bouton "Use this draft" qui pré-remplit la zone de saisie. Nécessite un plugin Chatwoot custom ou une extension navigateur.

---

## 🚨 Blocages fréquents

### "Hilo ne reçoit pas les webhooks"

→ Vérifier :
- URL webhook Chatwoot exacte (avec `/webhook/chatwoot`)
- Événements cochés
- Logs Clever Cloud de hilo-service

### "Supabase auth error"

→ Vérifier `SUPABASE_SERVICE_ROLE_KEY` (attention : ce n'est PAS l'anon key)

### "Chatwoot POST error 401"

→ `CHATWOOT_API_TOKEN` invalide ou expiré. Regénérer.

---

## ✅ Checklist fin jour 3

- [ ] Hilo-service déployé et accessible
- [ ] Health endpoint OK
- [ ] Test local des 4 profils OK
- [ ] Webhook Chatwoot configuré
- [ ] Un DM Instagram test génère une note interne Hilo dans Chatwoot
- [ ] Le lead correspondant est créé en Supabase (vérifiable dans le dashboard)

---

*Fin jour 3 : Hilo est en ligne, drafte automatiquement. Il reste à valider la persistance complète et la boucle d'amélioration.*
