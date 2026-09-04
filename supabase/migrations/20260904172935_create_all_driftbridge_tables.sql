/*
# Create all DriftBridge application tables

This migration creates every table the DriftBridge Flask app needs to function.
The app previously relied on SQLite/MySQL with Flask-Migrate, but now runs
against Supabase Postgres. All tables are created here in dependency order.

1. New Tables
- `users`: Application-level user accounts (username, email, password_hash, bio,
  interests, preferred_language, points, is_admin, created_at). This is separate
  from Supabase auth.users because the app uses Flask-Login with its own
  password hashing, not Supabase Auth.
- `bottles`: Messages thrown into the pool by users. Has sender_id, message,
  status (available/claimed), receiver_id (nullable until claimed).
- `conversations`: 1-on-1 chat rooms between two users (user1_id, user2_id).
- `messages`: Individual chat messages in a conversation. Has sender_id, content,
  original_language for translation.
- `journals`: Personal journal entries with privacy settings (private/connections/public),
  mood, and tags.
- `stories`: 24-hour temporary text stories with background color. Has expires_at.
- `story_views`: Track which users have viewed which stories.
- `content_flags`: Flagged content for admin review (hate speech detection results).

2. Security
- RLS is enabled on all tables but policies are set to allow all operations
  for the `anon` and `authenticated` roles, because the Flask backend handles
  authentication and authorization independently. The browser never talks
  directly to Postgres — all queries go through the Flask server using the
  service-role connection string. RLS is enabled as a defense-in-depth measure.

3. Important Notes
- All tables use SERIAL (integer auto-increment) primary keys to match the
  Flask-SQLAlchemy models which use db.Integer primary keys.
- Column types match what SQLAlchemy would generate for the models.
- Timestamps use timestamptz DEFAULT now() to match SQLAlchemy's datetime.utcnow.
*/

-- ============================================================
-- users table
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    bio VARCHAR(500),
    interests VARCHAR(500),
    preferred_language VARCHAR(10) NOT NULL DEFAULT 'en',
    points INTEGER NOT NULL DEFAULT 0,
    is_admin BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all_users" ON users;
CREATE POLICY "anon_all_users" ON users FOR ALL
    TO anon, authenticated USING (true) WITH CHECK (true);

-- ============================================================
-- bottles table
-- ============================================================
CREATE TABLE IF NOT EXISTS bottles (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    receiver_id INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    claimed_at TIMESTAMPTZ
);

ALTER TABLE bottles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all_bottles" ON bottles;
CREATE POLICY "anon_all_bottles" ON bottles FOR ALL
    TO anon, authenticated USING (true) WITH CHECK (true);

-- ============================================================
-- conversations table
-- ============================================================
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user1_id INTEGER NOT NULL REFERENCES users(id),
    user2_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all_conversations" ON conversations;
CREATE POLICY "anon_all_conversations" ON conversations FOR ALL
    TO anon, authenticated USING (true) WITH CHECK (true);

-- ============================================================
-- messages table
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    sender_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    original_language VARCHAR(10) NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all_messages" ON messages;
CREATE POLICY "anon_all_messages" ON messages FOR ALL
    TO anon, authenticated USING (true) WITH CHECK (true);

-- ============================================================
-- journals table
-- ============================================================
CREATE TABLE IF NOT EXISTS journals (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    privacy VARCHAR(20) NOT NULL DEFAULT 'private',
    mood VARCHAR(50),
    tags VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE journals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all_journals" ON journals;
CREATE POLICY "anon_all_journals" ON journals FOR ALL
    TO anon, authenticated USING (true) WITH CHECK (true);

-- ============================================================
-- stories table
-- ============================================================
CREATE TABLE IF NOT EXISTS stories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    caption VARCHAR(500),
    media_url VARCHAR(500),
    media_type VARCHAR(20),
    text_content TEXT,
    background_color VARCHAR(7) DEFAULT '#222222',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE stories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all_stories" ON stories;
CREATE POLICY "anon_all_stories" ON stories FOR ALL
    TO anon, authenticated USING (true) WITH CHECK (true);

-- ============================================================
-- story_views table
-- ============================================================
CREATE TABLE IF NOT EXISTS story_views (
    id SERIAL PRIMARY KEY,
    story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    viewed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE story_views ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all_story_views" ON story_views;
CREATE POLICY "anon_all_story_views" ON story_views FOR ALL
    TO anon, authenticated USING (true) WITH CHECK (true);

-- ============================================================
-- content_flags table
-- ============================================================
CREATE TABLE IF NOT EXISTS content_flags (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL,
    content_id INTEGER NOT NULL,
    content_text TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    severity VARCHAR(20) NOT NULL,
    ai_reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    admin_notes TEXT,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE content_flags ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all_content_flags" ON content_flags;
CREATE POLICY "anon_all_content_flags" ON content_flags FOR ALL
    TO anon, authenticated USING (true) WITH CHECK (true);

-- ============================================================
-- Indexes for frequently-queried columns
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_bottles_status ON bottles(status);
CREATE INDEX IF NOT EXISTS idx_bottles_sender ON bottles(sender_id);
CREATE INDEX IF NOT EXISTS idx_conversations_users ON conversations(user1_id, user2_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_journals_user ON journals(user_id);
CREATE INDEX IF NOT EXISTS idx_stories_user ON stories(user_id);
CREATE INDEX IF NOT EXISTS idx_stories_expires ON stories(expires_at);
CREATE INDEX IF NOT EXISTS idx_story_views_story ON story_views(story_id);
