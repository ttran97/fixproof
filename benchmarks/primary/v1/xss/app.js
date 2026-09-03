const express = require("express");

const app = express();
const port = Number(process.env.PORT || 3000);

app.get("/hello", (req, res) => {
    const name = req.query.name;
    res.send("<h1>Hello " + name + "</h1>");
});

app.listen(port, "127.0.0.1", () => {
    console.log(
        `FixProof primary XSS benchmark running on port ${port}`
    );
});

