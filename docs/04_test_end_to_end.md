# 04 — Test bout-en-bout

**Durée estimée :** 4-6 heures (jours 4 et 5)

---

## 🎯 Objectif

Un lead réel entre par Instagram → drafté par Hilo → envoyé après validation → persisté dans Supabase.

---

## A — Scénario de test canonique

### Scénario 1 : Curieux ES

**Entrée** : DM Instagram vers `@miches.vistaserena` avec le message :
```
Hola, quisiera información sobre los terrenos
```

**Attendus** :

1. Dans Chatwoot, une nouvelle conversation s'ouvre
2. Dans les 5 secondes, une **note interne** apparaît :
   ```
   🌴 **Draft Hilo**

   Hola, gracias por su interés en Vista Serena 🌴
   [...template curieux ES...]

   ---
   📊 Profil détecté: **curieux** (ES)
   ```
3. Dans Supabase → table `leads` : nouvelle ligne
   - `lead_id` : `L-2026-XXX`
   - `qualification` : `cold`
   - `source` : `instagram`
   - `language` : `ES`
   - `is_attributable_ig` : `true`

**Action manuelle** : copier le draft, ajuster si besoin, envoyer.

**Post-envoi (V0.2)** : mise à jour du champ `sent_version` dans `drafts` avec un endpoint dédié.

---

### Scénario 2 : Prospect EN riche

**Entrée** :
```
Hi François, I'm interested in Lot B1 or B3 for a single villa with 180° ocean view. My budget is around 300K USD.
```

**Attendus** :

1. Draft généré avec préface prospect + brochure EN
2. Note interne indique `Profil détecté: prospect (EN)`
3. Lead créé avec `qualification: warm`

**Action manuelle** : personnaliser le draft avec les infos B1/B3 spécifiques (le POC V0 ne fait que le préface, la personnalisation reste manuelle en V0).

---

### Scénario 3 : RED FLAG CONFOTUR

**Entrée** :
```
Buenos días, ¿sus terrenos tienen clasificación CONFOTUR?
```

**Attendus** :

1. Draft généré (curieux ES par défaut)
2. RED FLAG affiché dans la note interne :
   ```
   🚩 CONFOTUR mentionné par le lead — répondre uniquement avec la formulation validée
   (Talipot en instruction, décision décembre 2026). NE PAS confirmer pour Vista Serena.
   ```
3. L'agent voit le RED FLAG et adapte la réponse

---

### Scénario 4 : Agent immo

**Entrée** :
```
Hola, soy de una inmobiliaria y tengo clientes interesados.
```

**Attendus** :

1. Draft = template agent (refus poli founder-direct)
2. Lead créé avec `qualification: perdu`
3. `is_attributable_ig: false`

---

## B — Vérifications DB Supabase

Ouvrir le SQL Editor Supabase et exécuter :

```sql
-- Voir tous les leads du POC
SELECT
  lead_id, name, source, language, contact_type, qualification, is_attributable_ig, created_at
FROM leads
WHERE tenant_id = (SELECT id FROM tenants WHERE slug = 'vista-serena')
ORDER BY created_at DESC;

-- Voir les drafts générés
SELECT
  d.id, d.status, d.original_draft, d.hilo_analysis, l.lead_id
FROM drafts d
JOIN conversations c ON c.id = d.conversation_id
LEFT JOIN leads l ON l.id = c.lead_id
WHERE d.tenant_id = (SELECT id FROM tenants WHERE slug = 'vista-serena')
ORDER BY d.created_at DESC;

-- Voir l'audit log
SELECT
  actor, action, entity_type, created_at
FROM audit_log
WHERE tenant_id = (SELECT id FROM tenants WHERE slug = 'vista-serena')
ORDER BY created_at DESC
LIMIT 20;
```

---

## C — Critères de validation POC

| Critère | Attendu | Vérifié ? |
|---|---|---|
| DM Instagram → arrive dans Chatwoot | < 5 sec | ⬜ |
| Chatwoot → webhook Hilo | < 2 sec | ⬜ |
| Hilo génère draft | < 3 sec | ⬜ |
| Draft posté comme note interne | Visible dans Chatwoot | ⬜ |
| Lead créé en Supabase | Ligne présente | ⬜ |
| `lead_id` auto-généré au bon format | `L-2026-XXX` | ⬜ |
| Profil détecté correctement | curieux/prospect/agent selon cas | ⬜ |
| Langue détectée correctement | ES/EN/FR selon cas | ⬜ |
| `is_attributable_ig` correct | true si IG | ⬜ |
| Brochure langue correcte | ES → brochure ES, EN → EN | ⬜ |
| RED FLAG CONFOTUR détecté | Affiché en note interne | ⬜ |
| Agent → template refus | Template correct | ⬜ |
| Audit log entrée présente | Ligne créée | ⬜ |

---

## D — Métriques à mesurer

Sur 3 jours d'usage réel avec de vrais leads :

- **Nombre de messages entrants** : X
- **Nombre de drafts générés** : X
- **Nombre de drafts utilisés tels quels (0 modification)** : X %
- **Nombre de drafts modifiés avant envoi** : X %
- **Nombre de drafts jetés (réponse écrite from scratch)** : X %
- **Temps moyen entre message entrant et réponse envoyée** : X min (avant : X min via conversation Claude)

Ces métriques valideront ou non l'approche.

---

## E — Ce qui vient après le POC (V1)

Si POC validé :

1. **Personnalisation prospect** : appel Claude API dans `response_generator.py` avec system prompt Hilo complet + contexte lead
2. **Récupération diff draft ↔ envoyé** : bouton "Marquer comme envoyé" qui enregistre la version finale dans `drafts.sent_version`
3. **Apprentissage** : agrégation des diffs → amélioration périodique des templates
4. **Onboarding Talipot** : 2e tenant, config à part
5. **WhatsApp Business API** : quand la nouvelle ligne est ouverte
6. **Instagram comments handoff** : quand Oye sera prêt

---

## 📊 Rapport de fin de POC

À rédiger à la fin de la semaine :

- **Ce qui marche** : lister
- **Ce qui coince** : lister
- **Décisions à prendre pour V1** : lister
- **Coût réel infra** : mesuré
- **Coût de dev en temps** : mesuré
- **GO/NO-GO V1** : décision

---

*Fin POC : décision GO/NO-GO pour la V1 complète.*
