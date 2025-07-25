CREATE EXTENSION IF NOT EXISTS "pgcrypto";


CREATE TYPE gender_type AS ENUM ('male', 'female');
CREATE TABLE users (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	name text UNIQUE NOT NULL,
	email text NOT NULL CHECK (email ~ '^[^\s@]+@[^\s@]+\.[^\s@]+$'),
	created_at timestamptz NOT NULL DEFAULT now(),
	age int CHECK (age >= 0),
	gender gender_type
);


CREATE TABLE follows (
	user_from uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	user_to uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	created_at timestamptz NOT NULL DEFAULT now(),
	PRIMARY KEY (user_from, user_to),
	CHECK (user_from <> user_to)
);
CREATE INDEX idx_follows_user_from ON follows(user_from);
CREATE INDEX idx_follows_user_to ON follows(user_to);


CREATE TABLE posts (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	caption text,
	created_by uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_posts_created_by ON posts(created_by);


CREATE TYPE media_type AS ENUM ('image', 'video');
CREATE TABLE media (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	posted_on uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
	url text NOT NULL CHECK (url ~ '^(https?://[^\s/$.?#].[^\s]*)$'),
	media_type media_type NOT NULL
);


CREATE TABLE comments (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	created_by uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	commented_on uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
	replied_on uuid REFERENCES comments(id) ON DELETE SET NULL,
	contents text NOT NULL,
	created_at timestamptz NOT NULL DEFAULT now(),
	deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_comments_commented_on ON comments(commented_on);
CREATE INDEX idx_comments_replied_on ON comments(replied_on);


CREATE OR REPLACE FUNCTION prevent_comment_hard_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM comments c WHERE c.replied_on = OLD.id AND c.deleted_at IS NULL) THEN
        RAISE EXCEPTION 'Cannot hard delete comment with active replies';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER no_hard_delete
BEFORE DELETE ON comments
FOR EACH ROW EXECUTE FUNCTION prevent_comment_hard_delete();


CREATE TABLE likes (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id uuid REFERENCES posts(id) ON DELETE CASCADE,
    comment_id uuid REFERENCES comments(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL))
);
