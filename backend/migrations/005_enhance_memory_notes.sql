-- Migration: enhance memory notes with metadata and review fields

ALTER TABLE memory_notes
ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION NOT NULL DEFAULT 0.8,
ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'manual',
ADD COLUMN IF NOT EXISTS review_status TEXT NOT NULL DEFAULT 'active',
ADD COLUMN IF NOT EXISTS last_reviewed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_memory_notes_review_status
ON memory_notes(user_id, review_status);
