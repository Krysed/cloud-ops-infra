CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    user_type TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS postings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    post_description TEXT NOT NULL,
    category TEXT NOT NULL,
    views INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    posting_id INTEGER REFERENCES postings(id) ON DELETE CASCADE,
    message TEXT,
    cover_letter TEXT,
    applied_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending',
    reviewed_at TIMESTAMP,
    reviewer_notes TEXT
);

CREATE TABLE IF NOT EXISTS posting_views (
    id SERIAL PRIMARY KEY,
    posting_id INTEGER REFERENCES postings(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    viewed_at TIMESTAMP DEFAULT NOW(),
    session_id TEXT,
    is_unique_view BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS posting_metrics (
    id SERIAL PRIMARY KEY,
    posting_id INTEGER REFERENCES postings(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    views_count INTEGER DEFAULT 0,
    unique_views_count INTEGER DEFAULT 0,
    applications_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(posting_id, date)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_posting_views_posting_id ON posting_views(posting_id);
CREATE INDEX IF NOT EXISTS idx_posting_views_user_id ON posting_views(user_id);
CREATE INDEX IF NOT EXISTS idx_posting_views_viewed_at ON posting_views(viewed_at);
CREATE INDEX IF NOT EXISTS idx_posting_metrics_posting_date ON posting_metrics(posting_id, date);
CREATE INDEX IF NOT EXISTS idx_applications_posting_id ON applications(posting_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
