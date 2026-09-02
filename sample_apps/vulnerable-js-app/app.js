const express = require("express");
const fs = require("fs");
const app = express();

app.use(express.urlencoded({ extended: true }));

const API_SECRET_KEY = "sk_live_fixproof_test_998877665544";

app.get("/hello", (req, res) => {
    const name = req.query.name;
    res.send("<h1>Hello " + name + "</h1>");
});

app.get("/user", (req, res) => {
    const username = req.query.username;

    const query =
        "SELECT * FROM users WHERE username = '" +
        username +
        "'";

    console.log("Executing query:", query);
    res.send(query);
});

app.get("/file", (req, res) => {
    const filename = req.query.filename;

    fs.readFile("./uploads/" + filename, "utf8", (err, data) => {
        if (err) {
            return res.status(404).send("File not found");
        }

        res.send(data);
    });
});

app.listen(3000, () => {
    console.log("FixProof vulnerable test app running on port 3000");
});