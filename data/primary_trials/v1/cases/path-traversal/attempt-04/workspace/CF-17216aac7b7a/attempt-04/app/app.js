const express = require("express");
const fs = require("fs");
const path = require("path");

const app = express();
const port = Number(process.env.PORT || 3000);
const fileRoot = path.join(__dirname, "public-files");

app.get("/file", (req, res) => {
    const name = req.query.name;
    if (typeof name !== "string" || name.length === 0) {
        return res.status(400).json({
            error: "Invalid file name"
        });
    }

    const rootPath = path.resolve(fileRoot);
    const filePath = path.resolve(rootPath, name);

    // Ensure the resolved path stays within the intended root directory
    if (filePath !== rootPath && !filePath.startsWith(rootPath + path.sep)) {
        return res.status(400).json({
            error: "Invalid file name"
        });
    }

    fs.readFile(filePath, "utf8", (err, data) => {
        if (err) {
            return res.status(404).json({
                error: "File not found"
            });
        }

        res.type("text/plain").send(data);
    });
});

app.listen(port, "127.0.0.1", () => {
    console.log(
        `FixProof primary path-traversal benchmark running on port ${port}`
    );
});

