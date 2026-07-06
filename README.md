# POC Hilo App — Semaine 1

**Objectif :** Sortir Hilo du mode conversationnel Claude et valider une chaîne complète :
Instagram DM → Chatwoot → Hilo (draft) → validation humaine → réponse Instagram → Supabase (lead).

**Durée cible :** 5 jours ouvrés.
**Résultat attendu :** Un lead réel Instagram traité de bout en bout dans le nouveau système.

---

## 🎯 Périmètre du POC

### ✅ Inclus

- Chatwoot self-hosted sur Clever Cloud
- Instagram DM connecté à Chatwoot (compte pro `@miches.vistaserena`)
- Hilo-service Python FastAPI (draft automatique)
- Supabase multi-tenant (base leads + conversations)
- Un tenant Vista Serena créé
- Webhook Chatwoot → Hilo pour drafts
- Bouton dans Chatwoot pour envoyer la réponse Hilo au client

### ❌ Exclu (pour V1 ultérieure)

- WhatsApp Business API (Q3 : nouvelle ligne à ouvrir)
- Instagram commentaires publics (V1.1, handoff avec Oye)
- Gmail API (V1.2)
- Communication Mira (V1.1 : snapshot local suffit)
- Communication Veris (V1.2)
- Tenant Talipot (V1.1)
- Apprentissage continu automatique (V1.2)

---

## 📁 Structure du repo

```
poc-hilo-app/
├── README.md                          # Ce fichier
├── docs/
│   ├── 01_setup_infra.md              # Setup Chatwoot Clever Cloud + Supabase
│   ├── 02_setup_instagram.md          # Connexion Instagram Graph API
│   ├── 03_deploy_hilo_service.md      # Déploiement Hilo Python
│   ├── 04_test_end_to_end.md          # Scénario de test complet
│   └── 05_troubleshooting.md          # Erreurs fréquentes
├── hilo-service/
│   ├── main.py                        # FastAPI app (webhook receiver)
│   ├── engine/
│   │   ├── profile_detection.py       # Détection curieux/prospect/agent
│   │   ├── response_generator.py      # Génération draft
│   │   ├── canonical.py               # Lecture snapshot canonical
│   │   └── validators.py              # RED FLAG detection
│   ├── db/
│   │   ├── supabase_client.py         # Client Supabase
│   │   └── schema.sql                 # Schéma initial
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── scripts/
│   ├── init_supabase.sql              # Initialisation DB
│   ├── seed_vista_serena.py           # Config tenant Vista Serena
│   └── test_webhook.py                # Simulation d'un message IG
└── configs/
    ├── chatwoot_env.example           # Variables d'env Chatwoot
    ├── canonical_snapshot.json        # Copie locale canonical v1.1.4
    └── voice_charter_vista_serena.yaml # Règles ton Hilo
```

---

## 🗓️ Planning jour par jour

### Jour 1 — Infra

- [ ] Créer projet Supabase (free tier)
- [ ] Créer app Clever Cloud pour Chatwoot
- [ ] Déployer Chatwoot (image Docker officielle)
- [ ] Créer compte owner + 1 inbox test
- [ ] Vérifier accès web à Chatwoot

### Jour 2 — Instagram

- [ ] Vérifier permissions Meta Business Manager
- [ ] Connecter @miches.vistaserena à Chatwoot (canal Instagram)
- [ ] Tester envoi/réception DM depuis Chatwoot
- [ ] Documenter dans `02_setup_instagram.md`

### Jour 3 — Hilo-service V0

- [ ] Créer app FastAPI minimale
- [ ] Endpoint `POST /webhook/chatwoot` (reçoit nouveau message)
- [ ] Endpoint `GET /draft/{message_id}` (retourne draft)
- [ ] Détection profil simple (curieux par défaut)
- [ ] Génération template Curieux ES
- [ ] Déployer sur Clever Cloud
- [ ] Configurer webhook Chatwoot → Hilo

### Jour 4 — Supabase + lead persistence

- [ ] Créer schéma DB (tenants, leads, conversations, drafts)
- [ ] Écrire client Python Supabase
- [ ] À chaque nouveau message : créer/mettre à jour un lead
- [ ] Row-level security tenant Vista Serena

### Jour 5 — Test bout-en-bout

- [ ] Envoyer un DM Instagram de test vers @miches.vistaserena
- [ ] Vérifier arrivée dans Chatwoot
- [ ] Vérifier draft Hilo apparaît en note interne
- [ ] Modifier + envoyer manuellement
- [ ] Vérifier lead créé en base Supabase
- [ ] Documenter le workflow dans `04_test_end_to_end.md`

---

## 🎯 Critères de succès

À la fin de la semaine, on doit pouvoir dire OUI aux 5 questions :

1. ✅ **Un message Instagram est-il reçu dans Chatwoot automatiquement ?**
2. ✅ **Hilo produit-il un draft de réponse dans les 5 secondes ?**
3. ✅ **Peux-tu envoyer la réponse depuis Chatwoot sans copier-coller ?**
4. ✅ **Le lead est-il persisté en base Supabase avec toutes les métadonnées ?**
5. ✅ **Peux-tu voir le lead + son historique dans Chatwoot ?**

Si **OUI aux 5** → on valide l'approche, on passe à la V1 complète (spec détaillée, autres canaux, Talipot, etc.).

Si **NON à une ou plusieurs** → on ajuste avant d'aller plus loin.

---

## 🚨 Décisions à prendre en cours de POC

Certaines questions ne peuvent être tranchées qu'en faisant :

- **Coût réel Clever Cloud pour Chatwoot** : à mesurer sur 1 semaine
- **Latence webhook Chatwoot → Hilo** : acceptable si < 3 secondes
- **Format des drafts dans Chatwoot** : note interne, message brouillon, ou canvas ? (à tester)
- **Comment gérer les threads longs** : historique complet à Hilo à chaque draft ou juste les 5 derniers messages ?

Ces décisions alimenteront la spec V1.

---

## 📞 Support

En cas de blocage sur un jour :
- Décrire précisément le blocage
- Poster dans notre conversation Claude/Hilo
- Je propose plan B ou solution

---

*Casquette Hilo — POC préparé pour François le 2026-07-05*
