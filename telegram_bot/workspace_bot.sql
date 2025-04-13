CREATE DATABASE workspace_bot;

\c workspace_bot;

CREATE TABLE workspace_bot (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'free',
    booked_by INTEGER,
    booking_time TIMESTAMP
);
CREATE TABLE users1 (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT
);


INSERT INTO workspace_bot (name, status) VALUES ('Место 1', 'free');
INSERT INTO workspace_bot (name, status) VALUES ('Место 2', 'free');
INSERT INTO workspace_bot (name, status) VALUES ('Место 3', 'booked');


INSERT INTO users1 (user_id, username, first_name, last_name) 
VALUES (123456789, 'test_user', 'John', 'Doe');

SELECT * FROM workspace_bot;
SELECT * FROM users1;