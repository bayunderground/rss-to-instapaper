-- feeds table
CREATE TABLE feeds (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    regex_filter TEXT,
);

-- processed_items table
CREATE TABLE processed_items (
    id SERIAL PRIMARY KEY,
    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    item_key TEXT NOT NULL UNIQUE,
    title TEXT,
    attempted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,  -- NULL = pending / not yet sent
);

-- optional index for faster lookups (recommended)
CREATE INDEX idx_processed_items_feed_id
    ON processed_items(feed_id);

