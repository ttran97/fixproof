const express = require("express");

const app = express();
const port = Number(process.env.PORT || 3000);

app.get("/hello", (req, res) => {
    const name = req.query.name;
    const escapeHtml = (value) => String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;")
        .replace(/\//g, "&#x2F;");

    res.send("<h1>Hello " + escapeHtml(name) + "</h1>");
});

app.listen(port, "127.0.0.1", () => {
    console.log(
        `FixProof primary XSS benchmark running on port ${port}`
    );
});

