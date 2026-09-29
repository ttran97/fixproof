[CmdletBinding()]
param(
    [string]$InputPath = 'docs\coursework\review-2026-09-22\FixProof - Video III - Recording Deck.pptx',
    [string]$OutputPath = 'docs\coursework\review-2026-09-29\FixProof - Video III - Final Recording Deck.pptx',
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$projectRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $projectRoot) {
    throw 'Run this script from inside the FixProof repository.'
}

$source = if ([IO.Path]::IsPathRooted($InputPath)) {
    [IO.Path]::GetFullPath($InputPath)
} else {
    [IO.Path]::GetFullPath((Join-Path $projectRoot $InputPath))
}
$target = if ([IO.Path]::IsPathRooted($OutputPath)) {
    [IO.Path]::GetFullPath($OutputPath)
} else {
    [IO.Path]::GetFullPath((Join-Path $projectRoot $OutputPath))
}
$allowedRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'docs\coursework\review-2026-09-29'))

if (-not $target.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay inside docs/coursework/review-2026-09-29.'
}
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Input deck not found: $source"
}
if ((Test-Path -LiteralPath $target) -and -not $Overwrite) {
    throw "Output already exists; use -Overwrite to replace it: $target"
}

[IO.Directory]::CreateDirectory($allowedRoot) | Out-Null
Copy-Item -LiteralPath $source -Destination $target -Force

function Update-ZipText {
    param(
        [IO.Compression.ZipArchive]$Archive,
        [string]$PartName,
        [string]$Old,
        [string]$New
    )

    $entry = $Archive.GetEntry($PartName)
    if (-not $entry) { throw "Missing PowerPoint package part: $PartName" }
    $reader = [IO.StreamReader]::new($entry.Open(), [Text.Encoding]::UTF8)
    try { $content = $reader.ReadToEnd() } finally { $reader.Dispose() }

    $occurrences = ([regex]::Matches($content, [regex]::Escape($Old))).Count
    if ($occurrences -ne 1) {
        throw "Expected one occurrence in ${PartName} but found ${occurrences}: $Old"
    }
    $updated = $content.Replace($Old, $New)

    $entry.Delete()
    $newEntry = $Archive.CreateEntry($PartName, [IO.Compression.CompressionLevel]::Optimal)
    $writer = [IO.StreamWriter]::new($newEntry.Open(), [Text.UTF8Encoding]::new($false))
    try { $writer.Write($updated) } finally { $writer.Dispose() }
}

$archive = [IO.Compression.ZipFile]::Open($target, [IO.Compression.ZipArchiveMode]::Update)
try {
    Update-ZipText $archive 'ppt/slides/slide8.xml' `
        '- Planned early Report 3 submission: October 1' `
        '- Report 3 submitted: September 28'
    Update-ZipText $archive 'ppt/slides/slide8.xml' `
        '- Official Report 3 deadline: October 4, 11:59 p.m.' `
        '- Official deadline: October 4, 11:59 p.m.'
    Update-ZipText $archive 'ppt/notesSlides/notesSlide8.xml' `
        'Mention that Progress Report 3 is due October 4, Video III posts October 6, and peer feedback is due October 11.' `
        'Mention that Progress Report 3 was submitted September 28 ahead of the October 4 deadline, Video III posts October 6, and peer feedback is due October 11.'
} finally {
    $archive.Dispose()
}

Write-Output "Created final recording deck: $target"

