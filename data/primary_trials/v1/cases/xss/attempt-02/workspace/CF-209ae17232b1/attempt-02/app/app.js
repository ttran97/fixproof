const express = require("express");

const app = express();
const port = Number(process.env.PORT || 3000);

app.get("/hello", (req, res) => {
    const name = req.query.name;
    const safeName = String(name ?? "").replace(/[&<>"']/g, (c) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    })[c]);
    res.send("<h1>Hello " + safeName + "</h1>");
});

app.listen(port, "127.0.0.1", () => {
    console.log(
        `FixProof primary XSS benchmark running on port ${port}`
    );
});

