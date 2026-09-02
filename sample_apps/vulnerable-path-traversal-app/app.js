const express = require("express");
const fs = require("fs");
const path = require("path");

const app = express();

const fileRoot = path.join(
    __dirname,
    "public-files"
);

app.get("/file", (req, res) => {
    const name = req.query.name;

    const filePath = path.join(
        fileRoot,
        name
    );

    fs.readFile(
        filePath,
        "utf8",
        (err, data) => {
            if (err) {
                return res.status(404).json({
                    error: "File not found"
                });
            }

            res.type("text/plain").send(data);
        }
    );
});

app.listen(3000, () => {
    console.log(
        "FixProof path traversal test app running on port 3000"
    );
});
