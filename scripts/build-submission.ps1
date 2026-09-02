[CmdletBinding()]
param(
    [string]$ArchiveName = "FixProof-submission.zip"
)

$ErrorActionPreference = "Stop"

$originalLocation = Get-Location
$repositoryRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $repositoryRoot) {
    throw "Run this script from inside the FixProof Git repository."
}

try {
    Set-Location -LiteralPath $repositoryRoot

    $changes = @(& git status --porcelain)
    if ($changes.Count -gt 0) {
        throw (
            "The working tree is not clean. Review and commit the intended " +
            "submission snapshot before building an archive."
        )
    }

    & git ls-files --error-unmatch -- .env 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        throw "Refusing to package a repository that tracks .env."
    }

    $secretFiles = @(
        & git grep -I -l -E "sk-[A-Za-z0-9_-]{16,}" -- . 2>$null
    )
    if ($secretFiles.Count -gt 0) {
        throw (
            "Possible API-key material appears in tracked files: " +
            ($secretFiles -join ", ")
        )
    }

    $manifest = Get-Content `
        -LiteralPath "data\evaluation\experiment-manifest.json" `
        -Raw | ConvertFrom-Json
    $entries = @($manifest.attempts) + @($manifest.controls)
    foreach ($entry in $entries) {
        foreach ($artifact in $entry.artifacts.PSObject.Properties) {
            $path = [string]$artifact.Value
            & git ls-files --error-unmatch -- $path 2>$null | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw (
                    "Selected evidence is not tracked: '$path'. Add the " +
                    "curated artifact before packaging."
                )
            }
        }
    }

    $distribution = Join-Path $repositoryRoot "dist"
    New-Item -ItemType Directory -Path $distribution -Force | Out-Null
    $archivePath = Join-Path $distribution $ArchiveName
    if (Test-Path -LiteralPath $archivePath) {
        throw "Archive already exists: '$archivePath'. Move or rename it first."
    }

    & git archive --format=zip --output=$archivePath HEAD
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $archivePath)) {
        throw "Git could not create the submission archive."
    }

    Write-Output "Created sanitized tracked-file archive: $archivePath"
}
finally {
    Set-Location -LiteralPath $originalLocation
}

