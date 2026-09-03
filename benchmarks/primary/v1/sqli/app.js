const express = require("express");
const sqlite3 = require("sqlite3").verbose();

const app = express();
const port = Number(process.env.PORT || 3000);
const db = new sqlite3.Database(":memory:");

db.serialize(() => {
    db.run(`
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            role TEXT NOT NULL
        )
    `);

    const statement = db.prepare(
        "INSERT INTO users (username, role) VALUES (?, ?)"
    );

    statement.run("alice", "user");
    statement.run("bob", "admin");
    statement.run("charlie", "user");
    statement.finalize();
});

app.get("/user", (req, res) => {
    const username = req.query.username;
    const query =
        "SELECT id, username, role FROM users " +
        "WHERE username = '" +
        username +
        "'";

    db.all(query, (err, rows) => {
        if (err) {
            return res.status(500).json({
                error: "Query failed"
            });
        }

        res.json(rows);
    });
});

app.listen(port, "127.0.0.1", () => {
    console.log(
        `FixProof primary SQLi benchmark running on port ${port}`
    );
});

