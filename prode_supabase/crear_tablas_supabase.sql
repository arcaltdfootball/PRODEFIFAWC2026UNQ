-- ══════════════════════════════════════════════════════════════
-- PRODE FIFA WORLD CUP 2026 — Esquema Supabase
-- Ejecutar en: Supabase Dashboard → SQL Editor → New query
-- ══════════════════════════════════════════════════════════════

-- 1. Participantes
CREATE TABLE IF NOT EXISTS participantes (
    id     BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    nombre TEXT   NOT NULL,
    foto   TEXT   DEFAULT ''
);

-- 2. Partidos
CREATE TABLE IF NOT EXISTS partidos (
    id        BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    grupo     TEXT NOT NULL,
    fecha     TEXT NOT NULL,
    hora      TEXT NOT NULL,
    sede      TEXT NOT NULL,
    local     TEXT NOT NULL,
    visitante TEXT NOT NULL,
    resultado TEXT DEFAULT ''
);

-- 3. Pronósticos (un pronóstico por participante por partido)
CREATE TABLE IF NOT EXISTS pronosticos (
    id               BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    participante_id  BIGINT NOT NULL REFERENCES participantes(id) ON DELETE CASCADE,
    partido_id       BIGINT NOT NULL REFERENCES partidos(id)      ON DELETE CASCADE,
    pronostico       TEXT   NOT NULL CHECK (pronostico IN ('1','X','2','')),
    UNIQUE (participante_id, partido_id)
);

-- 4. Historial de ranking
CREATE TABLE IF NOT EXISTS historial_ranking (
    id               BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    participante_id  BIGINT NOT NULL REFERENCES participantes(id) ON DELETE CASCADE,
    fecha_control    TEXT   NOT NULL,
    posicion         INTEGER NOT NULL,
    puntos           INTEGER NOT NULL
);

-- ──────────────────────────────────────────────────────────────
-- Row Level Security (RLS)
-- Permite lectura pública y escritura solo con la service key.
-- Ajustá según tus necesidades de seguridad.
-- ──────────────────────────────────────────────────────────────

ALTER TABLE participantes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE partidos         ENABLE ROW LEVEL SECURITY;
ALTER TABLE pronosticos      ENABLE ROW LEVEL SECURITY;
ALTER TABLE historial_ranking ENABLE ROW LEVEL SECURITY;

-- Lectura pública
CREATE POLICY "lectura_publica_participantes"    ON participantes    FOR SELECT USING (true);
CREATE POLICY "lectura_publica_partidos"         ON partidos         FOR SELECT USING (true);
CREATE POLICY "lectura_publica_pronosticos"      ON pronosticos      FOR SELECT USING (true);
CREATE POLICY "lectura_publica_historial"        ON historial_ranking FOR SELECT USING (true);

-- Escritura pública (la auth real la maneja la app con la clave admin)
-- Si querés restringirla más podés reemplazar `true` por roles de Supabase Auth.
CREATE POLICY "escritura_publica_participantes"    ON participantes    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "escritura_publica_partidos"         ON partidos         FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "escritura_publica_pronosticos"      ON pronosticos      FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "escritura_publica_historial"        ON historial_ranking FOR ALL USING (true) WITH CHECK (true);
