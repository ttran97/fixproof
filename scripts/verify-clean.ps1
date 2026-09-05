[CmdletBinding()]
param(
    [switch]$InstallDependencies,
    [switch]$RunDemoSuite,
    [switch]$KeepTemporaryFiles
)

$ErrorActionPreference = "Stop"

$originalLocation = Get-Location
$originalPythonPath = $env:PYTHONPATH
$repositoryRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $repositoryRoot) {
    throw "Run this script from inside the FixProof Git repository."
}

$changes = @(& git -C $repositoryRoot status --porcelain)
if ($changes.Count -gt 0) {
    throw (
        "The working tree is not clean. Commit the intended snapshot before " +
        "testing a clean extraction."
    )
}

if ($RunDemoSuite -and -not $InstallDependencies) {
    throw "-RunDemoSuite requires -InstallDependencies in the clean copy."
}

$temporaryBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$runDirectory = Join-Path `
    $temporaryBase `
    ("fixproof-clean-" + [Guid]::NewGuid().ToString("N"))
$archivePath = Join-Path $runDirectory "snapshot.zip"
$extractedRoot = Join-Path $runDirectory "repository"

New-Item -ItemType Directory -Path $runDirectory | Out-Null
New-Item -ItemType Directory -Path $extractedRoot | Out-Null

try {
    & git -C $repositoryRoot archive --format=zip --output=$archivePath HEAD
    if ($LASTEXITCODE -ne 0) {
        throw "Git could not export the clean snapshot."
    }
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractedRoot

    if ($InstallDependencies) {
        $projectPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
        if (Test-Path -LiteralPath $projectPython) {
            & $projectPython -m venv (Join-Path $extractedRoot ".venv")
        }
        else {
            & py -3.11 -m venv (Join-Path $extractedRoot ".venv")
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create the clean Python environment."
        }
        $python = Join-Path $extractedRoot ".venv\Scripts\python.exe"
    }
    else {
        $python = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
        if (-not (Test-Path -LiteralPath $python)) {
            throw "Current project interpreter not found; use -InstallDependencies."
        }
    }

    Push-Location -LiteralPath $extractedRoot
    try {
        if ($InstallDependencies) {
            & $python -m pip install --upgrade pip
            if ($LASTEXITCODE -ne 0) {
                throw "Could not upgrade pip in the clean environment."
            }
            & $python -m pip install -e .
            if ($LASTEXITCODE -ne 0) {
                throw "Could not install FixProof dependencies."
            }

            & $python -m playwright install chromium
            if ($LASTEXITCODE -ne 0) {
                throw "Could not install the Chromium runtime oracle."
            }

            foreach ($application in @(
                "sample_apps\vulnerable-js-app",
                "sample_apps\vulnerable-sqli-app",
                "sample_apps\vulnerable-path-traversal-app",
                "benchmarks\primary\v1\xss",
                "benchmarks\primary\v1\sqli",
                "benchmarks\primary\v1\path-traversal"
            )) {
                Push-Location -LiteralPath $application
                try {
                    & npm.cmd ci
                    if ($LASTEXITCODE -ne 0) {
                        throw "npm ci failed for '$application'."
                    }
                }
                finally {
                    Pop-Location
                }
            }
        }

        $env:PYTHONPATH = Join-Path $extractedRoot "src"
        & $python -m fixproof.reproduce --verify
        if ($LASTEXITCODE -ne 0) {
            throw "Recorded-evidence verification failed in the clean copy."
        }

        if ($RunDemoSuite) {
            & powershell.exe -ExecutionPolicy Bypass -File .\demo-test.ps1 -Suite
            if ($LASTEXITCODE -ne 0) {
                throw "The controlled demo suite failed in the clean copy."
            }
        }
    }
    finally {
        Pop-Location
    }

    Write-Output "Clean-extraction verification passed: $extractedRoot"
}
finally {
    $env:PYTHONPATH = $originalPythonPath
    Set-Location -LiteralPath $originalLocation

    if ($KeepTemporaryFiles) {
        Write-Output "Temporary verification files retained: $runDirectory"
    }
    else {
        $resolvedRunDirectory = [IO.Path]::GetFullPath($runDirectory)
        $expectedPrefix = Join-Path $temporaryBase "fixproof-clean-"
        if (-not $resolvedRunDirectory.StartsWith(
            $expectedPrefix,
            [StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Refusing to remove an unexpected temporary path."
        }
        Remove-Item -LiteralPath $resolvedRunDirectory -Recurse -Force
    }
}
