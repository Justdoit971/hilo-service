# 02 — Connexion Instagram DM à Chatwoot

**Durée estimée :** 2-3 heures
**Prérequis :** Compte Instagram Pro `@miches.vistaserena` + accès à un Meta Business Manager

---

## A — Vérifications Meta Business Manager (30 min)

### 1. Compte Instagram Pro

`@miches.vistaserena` doit être :
- ✅ Configuré en **compte Pro** ou **compte Créateur**
- ✅ Lié à une **Page Facebook** (obligatoire pour la Graph API)

Si pas encore lié à une page Facebook :
- Créer une page FB (peut être simple, elle sert juste de conteneur)
- Instagram → Paramètres → Compte → Comptes liés → Facebook

### 2. Meta Business Manager

- Aller sur https://business.facebook.com
- Ajouter (ou créer) un Business Manager
- Ajouter la Page Facebook au Business Manager
- Ajouter le compte Instagram au Business Manager

### 3. Créer une App Meta pour Chatwoot

- Aller sur https://developers.facebook.com/apps
- Créer une app → Type : **Business**
- Nom : `Hilo Chatwoot Vista Serena`
- Ajouter les produits :
  - **Facebook Login for Business**
  - **Messenger** (pour l'API)
  - **Instagram Messaging API**

### 4. Permissions à demander

Dans App Review → Permissions and Features :
- `instagram_basic` ✅
- `instagram_manage_messages` ✅
- `pages_messaging` ✅
- `pages_show_list` ✅
- `pages_manage_metadata` ✅

Ces permissions doivent être approuvées par Meta (peut prendre 24-72h pour un review si elles ne sont pas déjà accordées).

---

## B — Configuration côté Chatwoot (30 min)

### 1. Récupérer les identifiants App

Dans l'App Meta :
- `App ID` (Settings → Basic)
- `App Secret` (Settings → Basic)

### 2. Configurer dans Chatwoot

Aller dans les variables d'environnement Clever Cloud de l'app Chatwoot :

```bash
FB_APP_ID=<App ID>
FB_APP_SECRET=<App Secret>
FB_VERIFY_TOKEN=<chaîne aléatoire, ex: 'hilo-vista-serena-token-2026'>
IG_VERIFY_TOKEN=<même chaîne aléatoire ou différente>
```

Redéployer l'app Chatwoot après ajout des variables.

### 3. Configurer le Webhook Meta

Dans l'App Meta → Messenger → Configuration :
- **Callback URL** : `https://chatwoot-hilo.cleverapps.io/webhooks/facebook`
- **Verify Token** : la même chaîne que `FB_VERIFY_TOKEN`
- Cocher les événements :
  - `messages`
  - `messaging_postbacks`
  - `message_reads`
  - `messaging_optins`

Idem pour Instagram Messaging → Configuration Webhook :
- **Callback URL** : `https://chatwoot-hilo.cleverapps.io/webhooks/instagram`
- **Verify Token** : `IG_VERIFY_TOKEN`
- Événements : `messages`, `messaging_postbacks`

---

## C — Créer l'inbox Instagram dans Chatwoot (15 min)

### 1. Nouvelle inbox

Dans Chatwoot → Settings → Inboxes → Add Inbox → **Instagram**

- Se connecter avec le compte Facebook lié à `@miches.vistaserena`
- Autoriser les permissions
- Sélectionner la Page Facebook liée
- Sélectionner le compte Instagram
- Nom de l'inbox : `Instagram DM - Vista Serena`

### 2. Assigner l'agent

- Ajouter toi-même en agent de cette inbox
- Sauvegarder

---

## D — Test bout-en-bout (30 min)

### 1. Envoyer un DM test

- Depuis un autre compte Instagram, envoyer un DM à `@miches.vistaserena` avec le message : `Test Hilo POC`

### 2. Vérifier réception dans Chatwoot

- Dans Chatwoot → Conversations → Instagram DM
- Le message `Test Hilo POC` doit apparaître dans une nouvelle conversation

### 3. Répondre depuis Chatwoot

- Écrire : `Test reçu, merci !` dans Chatwoot
- Vérifier que le message arrive dans le DM Instagram

Si les 3 étapes fonctionnent : ✅ Instagram est branché.

---

## 🚨 Blocages fréquents

### "Webhook verification failed"

→ Vérifier que `FB_VERIFY_TOKEN` dans Chatwoot = valeur exacte du champ Verify Token dans le Callback URL

### "Insufficient permissions"

→ App Meta pas encore approuvée en mode "Live". Passer l'app en Live mode ou ajouter ton compte perso en **Tester** dans App Roles.

### "Instagram account not found"

→ Le compte IG n'est pas en Pro/Créateur, ou pas lié à une Page FB.

### Les DM n'arrivent pas dans Chatwoot

→ Vérifier dans Meta Business Manager que la Page FB est bien connectée à l'inbox Chatwoot.

---

## ✅ Checklist fin jour 2

- [ ] Compte IG en Pro/Créateur, lié à une page FB
- [ ] App Meta créée avec les permissions
- [ ] Webhook configuré et validé
- [ ] Inbox Instagram créée dans Chatwoot
- [ ] Test DM entrant OK
- [ ] Test DM sortant OK

---

*Fin jour 2 : Instagram entre et sort par Chatwoot. Reste à brancher Hilo pour drafts automatiques.*
