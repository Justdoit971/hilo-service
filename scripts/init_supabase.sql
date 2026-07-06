-- ============================================================================
-- SORIYA / HILO - Schema initial (POC V0, adapte aux patterns maison)
-- Fichier : scripts/init_supabase.sql (repo hilo-service)
-- Cree le 2026-07-05 (J19) a partir du POC de la casquette Hilo.
-- Adaptations vs POC d'origine (decisions Francois 2026-07-05) :
--   1. Projet soriya-dev existant, schema dedie "hilo" (pas de nouveau projet)
--   2. tenant_id TEXT (slug 'vista-serena'), convention maison - PAS d'UUID
--      de tenant ni de FK vers une table tenants a UUID
--   3. RLS activee SANS policies (fail-closed, comme oye.notas_ig) : le
--      hilo-service accede via service_role (bypass) ; les autres roles ne
--      voient rien. V1 : bascule vers un role hilo_app NOBYPASSRLS +
--      app.current_tenant, comme Veris/Oye.
-- Idempotent : re-executable sans danger.
-- ============================================================================

create schema if not exists hilo;

-- ----------------------------------------------------------------------------
-- 1. Tenants (config runtime par tenant ; la source de verite editoriale
--    reste config/tenants/{tenant_id}/ dans le repo soriya)
-- ----------------------------------------------------------------------------
create table if not exists hilo.tenants (
  tenant_id         text primary key,
  name              text not null,
  config            jsonb not null default '{}',
  canonical_version text,
  created_at        timestamptz default now(),
  updated_at        timestamptz default now()
);

-- ----------------------------------------------------------------------------
-- 2. Leads
-- ----------------------------------------------------------------------------
create table if not exists hilo.leads (
  id                 uuid primary key default gen_random_uuid(),
  tenant_id          text not null,
  lead_id            text not null,  -- format L-YYYY-NNN (contrat Veris)
  name               text,
  country            text,
  source             text not null,
  language           text,
  contact_type       text,
  produit_interet    text,
  lot_specifique     text,
  qualification      text not null default 'cold',
  budget_indicatif   text,
  next_step          text default 'Suivi',
  is_attributable_ig boolean not null default false,
  notes              text,
  first_contact_at    timestamptz default now(),
  last_interaction_at timestamptz default now(),
  external_ids       jsonb default '{}',
  created_at         timestamptz default now(),
  updated_at         timestamptz default now(),
  unique (tenant_id, lead_id)
);

create index if not exists idx_hilo_leads_tenant on hilo.leads(tenant_id);
create index if not exists idx_hilo_leads_qualif on hilo.leads(tenant_id, qualification);
create index if not exists idx_hilo_leads_ext on hilo.leads using gin (external_ids);

-- ----------------------------------------------------------------------------
-- 3. Conversations
-- ----------------------------------------------------------------------------
create table if not exists hilo.conversations (
  id                       uuid primary key default gen_random_uuid(),
  tenant_id                text not null,
  lead_id                  uuid references hilo.leads(id) on delete set null,
  channel                  text not null,  -- instagram_dm | whatsapp | email | ig_comment
  chatwoot_conversation_id bigint,
  status                   text default 'open',  -- open | resolved | pending
  created_at               timestamptz default now(),
  updated_at               timestamptz default now()
);

create index if not exists idx_hilo_conv_tenant on hilo.conversations(tenant_id);
create index if not exists idx_hilo_conv_chatwoot on hilo.conversations(chatwoot_conversation_id);

-- ----------------------------------------------------------------------------
-- 4. Messages
-- ----------------------------------------------------------------------------
create table if not exists hilo.messages (
  id                  uuid primary key default gen_random_uuid(),
  tenant_id           text not null,
  conversation_id     uuid not null references hilo.conversations(id) on delete cascade,
  direction           text not null,  -- inbound | outbound
  sender_type         text not null,  -- lead | agent | hilo
  content             text not null,
  chatwoot_message_id bigint,
  metadata            jsonb default '{}',
  created_at          timestamptz default now()
);

create index if not exists idx_hilo_msg_conv on hilo.messages(conversation_id);
create index if not exists idx_hilo_msg_tenant on hilo.messages(tenant_id, created_at);

-- ----------------------------------------------------------------------------
-- 5. Drafts (proposes par Hilo ; edit_diff = matiere de l'apprentissage V1)
-- ----------------------------------------------------------------------------
create table if not exists hilo.drafts (
  id                      uuid primary key default gen_random_uuid(),
  tenant_id               text not null,
  conversation_id         uuid not null references hilo.conversations(id) on delete cascade,
  triggered_by_message_id uuid references hilo.messages(id),
  original_draft          text not null,
  sent_version            text,
  status                  text default 'pending',  -- pending | edited | sent | discarded
  hilo_analysis           jsonb default '{}',
  edit_diff               text,
  created_at              timestamptz default now(),
  sent_at                 timestamptz
);

create index if not exists idx_hilo_drafts_conv on hilo.drafts(conversation_id);
create index if not exists idx_hilo_drafts_status on hilo.drafts(tenant_id, status);

-- ----------------------------------------------------------------------------
-- 6. Audit log (RGPD + tracabilite)
-- ----------------------------------------------------------------------------
create table if not exists hilo.audit_log (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   text not null,
  actor       text not null,
  action      text not null,
  entity_type text,
  entity_id   uuid,
  before_data jsonb,
  after_data  jsonb,
  ip_address  inet,
  created_at  timestamptz default now()
);

create index if not exists idx_hilo_audit_tenant on hilo.audit_log(tenant_id, created_at desc);

-- ----------------------------------------------------------------------------
-- 7. Row Level Security : activee, ZERO policy (fail-closed, design voulu).
--    Acces uniquement via service_role (hilo-service) tant que le role
--    hilo_app NOBYPASSRLS n'est pas cree (V1). NE PAS ajouter de policy
--    permissive sans decision d'architecture.
-- ----------------------------------------------------------------------------
alter table hilo.tenants       enable row level security;
alter table hilo.leads         enable row level security;
alter table hilo.conversations enable row level security;
alter table hilo.messages      enable row level security;
alter table hilo.drafts        enable row level security;
alter table hilo.audit_log     enable row level security;

-- ----------------------------------------------------------------------------
-- 7bis. Privileges API : un schema custom n'herite d'AUCUN grant (contrairement
--       a public). Sans ces GRANT, PostgREST repond 42501 permission denied
--       meme avec la service_role key (vecu POC 2026-07-06).
--       Volontairement RIEN pour anon/authenticated : fail-closed conserve.
-- ----------------------------------------------------------------------------
grant usage on schema hilo to service_role;
grant all privileges on all tables in schema hilo to service_role;
grant all privileges on all sequences in schema hilo to service_role;
alter default privileges in schema hilo grant all on tables to service_role;
alter default privileges in schema hilo grant all on sequences to service_role;

-- ----------------------------------------------------------------------------
-- 8. Trigger updated_at (idempotent)
-- ----------------------------------------------------------------------------
create or replace function hilo.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_updated_at_tenants on hilo.tenants;
create trigger trg_updated_at_tenants before update on hilo.tenants
  for each row execute function hilo.set_updated_at();

drop trigger if exists trg_updated_at_leads on hilo.leads;
create trigger trg_updated_at_leads before update on hilo.leads
  for each row execute function hilo.set_updated_at();

drop trigger if exists trg_updated_at_conversations on hilo.conversations;
create trigger trg_updated_at_conversations before update on hilo.conversations
  for each row execute function hilo.set_updated_at();

-- ----------------------------------------------------------------------------
-- 9. Seed : tenant vista-serena (accents en echappements JSON \uXXXX,
--    decodes par le parseur jsonb - le fichier reste ASCII)
-- ----------------------------------------------------------------------------
insert into hilo.tenants (tenant_id, name, config, canonical_version)
values (
  'vista-serena',
  'Vista Serena Miches',
  '{
    "langues_supportees": ["ES", "EN", "FR"],
    "voice_charter": {
      "max_emojis": 1,
      "default_formality": "vouvoiement",
      "signature": "Fran\u00e7ois\nVista Serena \u2014 Miches, R.D."
    },
    "sources_canoniques": ["instagram", "whatsapp", "google_ads", "seo_organic", "referral", "email", "direct"],
    "qualifications": ["cold", "warm", "hot", "vendu", "perdu"],
    "produits_interet": ["vista-serena-terrain", "talipot-vefa", "les-deux", "autre"]
  }',
  '1.1.4'
) on conflict (tenant_id) do nothing;

-- ============================================================================
-- Fin de init_supabase.sql (schema hilo)
-- ============================================================================
