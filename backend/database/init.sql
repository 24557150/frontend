CREATE TABLE IF NOT EXISTS wardrobe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    category TEXT NOT NULL
);
