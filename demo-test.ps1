[CmdletBinding()]
param(
    [ValidateSet("sqli", "xss", "path-traversal")]
    [string]$Case = "sqli",

    [ValidateRange(1, 99)]
    [int]$Attempt = 1,

    [switch]$UseLatestAttempt,
    [switch]$Suite,
    [switch]$SkipVerification,
    [switch]$FreshSast,
    [switch]$Serve
)

$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$previousPythonPath = $env:PYTHONPATH

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "FixProof virtual-environment Python was not found: $python"
}

if ($Suite -and $Serve) {
    throw "-Serve is available for one selected case, not for -Suite."
}

if ($Suite -and $FreshSast) {
    throw "-FreshSast is intentionally limited to one selected case."
}

Push-Location $projectRoot

try {
    $env:PYTHONPATH = Join-Path $projectRoot "src"

    Write-Host "============================================================"
    Write-Host "FixProof Guided Demo Test"
    Write-Host "============================================================"

    if ($Suite) {
        Write-Host "Mode: all controlled test sets"
    }
    else {
        Write-Host "Case: $Case"
    }

    Write-Host "Project: $projectRoot"
    Write-Host ""

    Write-Host "Evidence mode"
    Write-Host "- RECORDED: AI-generated candidate and baseline SAST evidence"

    if ($FreshSast) {
        Write-Host "- LIVE: candidate syntax check and fresh Semgrep rescan"
    }
    else {
        Write-Host "- RECORDED: candidate SAST evidence"
    }

    Write-Host "- LIVE: runtime security, functional, and decision stages"
    Write-Host "- DISPOSABLE: new demo outputs under Windows TEMP"

    if ($Serve) {
        Write-Host "- RECORDED: authoritative read-only dashboard"
    }

    Write-Host ""

    if ($Suite) {
        $testSets = @(
            [PSCustomObject]@{
                Id = "TS-02"
                Name = "SQLi validated candidate"
                Case = "sqli"
                Attempt = 1
                Expected = "READY_FOR_HUMAN_REVIEW"
            },
            [PSCustomObject]@{
                Id = "TS-03"
                Name = "XSS functional regression"
                Case = "xss"
                Attempt = 1
                Expected = "REJECT"
            },
            [PSCustomObject]@{
                Id = "TS-04"
                Name = "XSS evidence disagreement"
                Case = "xss"
                Attempt = 2
                Expected = "NEEDS_HUMAN_ADJUDICATION"
            },
            [PSCustomObject]@{
                Id = "TS-05"
                Name = "Path-traversal evidence disagreement"
                Case = "path-traversal"
                Attempt = 1
                Expected = "NEEDS_HUMAN_ADJUDICATION"
            }
        )
    }
    else {
        $selectedAttempt = $Attempt
        $expectedDecision = "manifest-selected decision"

        if ($UseLatestAttempt) {
            $selectedAttempt = $null
        }

        if ($Case -eq "sqli") {
            $expectedDecision = "READY_FOR_HUMAN_REVIEW"
        }
        elseif ($Case -eq "xss" -and $selectedAttempt -eq 1) {
            $expectedDecision = "REJECT"
        }
        elseif ($Case -eq "xss") {
            $expectedDecision = "NEEDS_HUMAN_ADJUDICATION"
        }
        elseif ($Case -eq "path-traversal") {
            $expectedDecision = "NEEDS_HUMAN_ADJUDICATION"
        }

        $testSets = @(
            [PSCustomObject]@{
                Id = "selected"
                Name = "$Case controlled validation"
                Case = $Case
                Attempt = $selectedAttempt
                Expected = $expectedDecision
            }
        )
    }

    $verificationStepCount = 0

    if (-not $SkipVerification) {
        $verificationStepCount = 1
    }

    $totalSteps = $verificationStepCount + $testSets.Count
    $currentStep = 0

    if (-not $SkipVerification) {
        $currentStep += 1
        Write-Host "[$currentStep/$totalSteps] TS-01: Verifying reproducibility and experiment readiness..."
        & $python -m fixproof.reproduce --verify

        if ($LASTEXITCODE -ne 0) {
            throw "FixProof reproducibility verification failed."
        }

        Write-Host ""
    }

    foreach ($testSet in $testSets) {
        $currentStep += 1
        Write-Host "[$currentStep/$totalSteps] $($testSet.Id): $($testSet.Name)"
        Write-Host "Expected decision: $($testSet.Expected)"

        $demoArguments = @(
            "-m",
            "fixproof.demo",
            "--case",
            $testSet.Case,
            "--validate"
        )

        if ($null -ne $testSet.Attempt) {
            $demoArguments += @("--attempt", [string]$testSet.Attempt)
        }

        if ($FreshSast) {
            $demoArguments += "--fresh-sast"
        }

        if ($Serve) {
            $demoArguments += "--serve"
        }

        if ($Suite) {
            $demoOutput = @()
            & $python @demoArguments 2>&1 |
                Tee-Object -Variable demoOutput |
                Out-Host
            $demoExitCode = $LASTEXITCODE
        }
        else {
            & $python @demoArguments
            $demoExitCode = $LASTEXITCODE
        }

        if ($demoExitCode -ne 0) {
            throw "FixProof controlled test set $($testSet.Id) failed."
        }

        if ($Suite) {
            $demoText = (
                $demoOutput |
                    ForEach-Object { [string]$_ }
            ) -join "`n"
            $expectedPattern = (
                "(?m)^Decision: " +
                [regex]::Escape($testSet.Expected) +
                "\r?$"
            )

            if ($demoText -notmatch $expectedPattern) {
                $decisionError = (
                    "FixProof controlled test set {0} did not produce " +
                    "the expected decision {1}."
                ) -f
                    $testSet.Id,
                    $testSet.Expected
                throw $decisionError
            }
        }

        Write-Host ""
    }

    if (-not $Serve) {
        Write-Host "============================================================"
        Write-Host "FixProof Controlled Test-Set Summary"
        Write-Host "============================================================"
        $testSets |
            Select-Object Id, Name, Case, Attempt, Expected |
            Format-Table -AutoSize |
            Out-Host

        $summaryMessage = (
            "All {0} controlled candidate test set(s) matched " +
            "their authoritative recorded decisions."
        ) -f $testSets.Count
        Write-Host $summaryMessage

        if ($SkipVerification) {
            Write-Host "TS-01 was skipped for this run."
        }
        else {
            Write-Host "TS-01 also verified the separated false-success control."
        }

        if (-not $Suite) {
            if ($FreshSast) {
                Write-Host "This run used a fresh candidate Semgrep rescan."
            }
            else {
                Write-Host "This run reused the recorded candidate SAST result."
            }

            Write-Host "Add -Serve to open the dashboard."
        }
    }
}
finally {
    Pop-Location

    if ($null -eq $previousPythonPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = $previousPythonPath
    }
}
