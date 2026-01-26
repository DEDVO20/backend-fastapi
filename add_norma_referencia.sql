-- Migración: Agregar columna norma_referencia a la tabla auditorias
-- Fecha: 2026-01-26

ALTER TABLE auditorias 
ADD COLUMN IF NOT EXISTS norma_referencia VARCHAR(200);

-- Verificar que la columna se agregó correctamente
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'auditorias' AND column_name = 'norma_referencia';
