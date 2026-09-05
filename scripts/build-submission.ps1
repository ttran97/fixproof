[CmdletBinding()]
param(
    [string]$ArchiveName = "FixProof-submission.zip"
)

$ErrorActionPreference = "Stop"

if ([IO.Path]::GetFileName($ArchiveName) -ne $ArchiveName -or
    -not $ArchiveName.EndsWith('.zip', [StringComparison]::OrdinalIgnoreCase)) {
    throw "ArchiveName must be a ZIP filename without directory components."
}

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

    $python = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
    & $python -m fixproof.evaluation.primary_report --check
    if ($LASTEXITCODE -ne 0) {
        throw "Primary evidence verification failed."
    }
    $primary = Get-Content -LiteralPath "data\evaluation\primary-report.json" -Raw | ConvertFrom-Json
    $primaryPaths = @("data/evaluation/primary-report.json", "docs/primary-results.md")
    $primaryPaths += @($primary.evidence_bindings | ForEach-Object { $_.path })
    foreach ($row in $primary.experiment_matrix) {
        $primaryPaths += @($row.artifacts.PSObject.Properties | ForEach-Object { $_.Value.path })
    }
    foreach ($path in ($primaryPaths | Sort-Object -Unique)) {
        & git ls-files --error-unmatch -- $path 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Primary evidence or derived report is not tracked: '$path'."
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
