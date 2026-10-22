[CmdletBinding()]
param(
    [string]$SourceDirectory = 'fixproof-public',
    [string]$OutputPath = 'fixproof-public-netlify-path-s06-2026-10-21-v2.zip',
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((& git rev-parse --show-toplevel).Trim())
if ($LASTEXITCODE -ne 0 -or -not $projectRoot) {
    throw 'Run this script from inside the FixProof repository.'
}

function Resolve-ProjectPath {
    param([string]$Path)
    if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
    return [IO.Path]::GetFullPath((Join-Path $projectRoot $Path))
}

$source = Resolve-ProjectPath $SourceDirectory
$target = Resolve-ProjectPath $OutputPath
if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Source directory not found: $source"
}
if (-not $target.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay inside the FixProof repository.'
}
if (Test-Path -LiteralPath $target) {
    if (-not $Overwrite) { throw "Output already exists: $target" }
    Remove-Item -LiteralPath $target -Force
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$stream = [IO.File]::Open($target, [IO.FileMode]::CreateNew)
try {
    $archive = New-Object IO.Compression.ZipArchive(
        $stream,
        [IO.Compression.ZipArchiveMode]::Create,
        $false
    )
    try {
        $files = @(Get-ChildItem -LiteralPath $source -Recurse -File | Sort-Object FullName)
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($source.Length + 1).Replace('\', '/')
            if ($relative.Contains('\')) {
                throw "Backslash remained in archive path: $relative"
            }
            $entry = $archive.CreateEntry(
                $relative,
                [IO.Compression.CompressionLevel]::Optimal
            )
            $entryStream = $entry.Open()
            $inputStream = [IO.File]::OpenRead($file.FullName)
            try {
                $inputStream.CopyTo($entryStream)
            }
            finally {
                $inputStream.Dispose()
                $entryStream.Dispose()
            }
        }
    }
    finally {
        $archive.Dispose()
    }
}
finally {
    $stream.Dispose()
}

$required = @(
    'index.html',
    'test-evidence.html',
    'test-evidence.js',
    'app.js',
    'styles.css',
    '_headers',
    'data/public-evidence.json',
    'data/student-test-evidence.json',
    'assets/fixproof-workflow.png',
    'FixProof-15-candidate-test-evidence.xlsx',
    'Video-III-15-candidate-evidence-appendix.pdf',
    'README.txt'
)

$check = [IO.Compression.ZipFile]::OpenRead($target)
try {
    $entries = @($check.Entries | Where-Object { $_.Name })
    $names = @($entries.FullName)
    $backslashes = @($names | Where-Object { $_.Contains('\') })
    if ($backslashes.Count -gt 0) {
        throw "Netlify-unsafe backslash paths: $($backslashes -join ', ')"
    }
    $missing = @($required | Where-Object { $_ -notin $names })
    if ($missing.Count -gt 0) {
        throw "Missing required entries: $($missing -join ', ')"
    }
    if ($names -contains 'fixproof-public/index.html') {
        throw 'Archive contains an unwanted top-level folder.'
    }
    if ($entries.Count -ne 12) {
        throw "Expected 12 public files; found $($entries.Count)."
    }
}
finally {
    $check.Dispose()
}

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash
Write-Output "Created Netlify-safe package: $target"
Write-Output 'Archive entries use forward slashes and index.html is at the root.'
Write-Output "SHA-256: $hash"
