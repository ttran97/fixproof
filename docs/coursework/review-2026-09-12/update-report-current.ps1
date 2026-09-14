param([string]$Source = 'C:/Users/tonyt/OneDrive/Documents/Progress Report 2 (Tony Tran) - Updated Draft (1).docx')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$destination = Join-Path $PSScriptRoot 'Progress Report 2 (Tony Tran) - Current Verified September 12.docx'
$sourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
$primaryReportPath = Join-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent) 'data/evaluation/primary-report.json'
$primaryReport = Get-Content -Raw -LiteralPath $primaryReportPath | ConvertFrom-Json
if ($primaryReport.attempt_count -ne 15) { throw 'Expected 15 verified primary attempts' }
if ($primaryReport.adjudication_summary.completed -ne 10 -or $primaryReport.adjudication_summary.pending -ne 0) {
    throw 'Primary human conflict reviews are not 10/10 complete'
}

Copy-Item -LiteralPath $Source -Destination $destination -Force
$zip = [IO.Compression.ZipFile]::Open($destination, [IO.Compression.ZipArchiveMode]::Update)
try {
    $entry = $zip.GetEntry('word/document.xml')
    $reader = [IO.StreamReader]::new($entry.Open())
    $xml = [xml]::new()
    $xml.PreserveWhitespace = $true
    $xml.LoadXml($reader.ReadToEnd())
    $reader.Dispose()
    $paragraphs = @($xml.SelectNodes('//*[local-name()="p"]'))
    $tableCount = $xml.SelectNodes('//*[local-name()="tbl"]').Count
    $rowCount = $xml.SelectNodes('//*[local-name()="tr"]').Count
    $edits = Get-Content (Join-Path $PSScriptRoot 'report-edits-current.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($edit in $edits) {
        $found = @($paragraphs | Where-Object {
            $value = ($_.SelectNodes('.//*[local-name()="t"]') | ForEach-Object InnerText) -join ''
            $value.StartsWith($edit.prefix, [StringComparison]::Ordinal)
        })
        if ($found.Count -ne 1) { throw "Expected one paragraph matching '$($edit.prefix)', got $($found.Count)" }
        $texts = @($found[0].SelectNodes('.//*[local-name()="t"]'))
        $texts[0].InnerText = $edit.text
        $texts[0].SetAttribute('xml:space', 'preserve')
        for ($i = 1; $i -lt $texts.Count; $i++) { $texts[$i].InnerText = '' }
    }
    $entry.Delete()
    $entry = $zip.CreateEntry('word/document.xml')
    $writer = [IO.StreamWriter]::new($entry.Open(), [Text.UTF8Encoding]::new($false))
    $writer.Write($xml.OuterXml)
    $writer.Dispose()
}
finally {
    $zip.Dispose()
}

$zip = [IO.Compression.ZipFile]::OpenRead($destination)
try {
    foreach ($entry in $zip.Entries) {
        if ($entry.FullName -match '\.xml$|\.rels$') {
            $reader = [IO.StreamReader]::new($entry.Open())
            try { $part = [xml]$reader.ReadToEnd() } finally { $reader.Dispose() }
        }
    }
    $reader = [IO.StreamReader]::new($zip.GetEntry('word/document.xml').Open())
    try { $checked = [xml]$reader.ReadToEnd() } finally { $reader.Dispose() }
    if ($checked.SelectNodes('//*[local-name()="tbl"]').Count -ne $tableCount -or
        $checked.SelectNodes('//*[local-name()="tr"]').Count -ne $rowCount) {
        throw 'Table structure changed'
    }
    $text = ($checked.SelectNodes('//*[local-name()="p"]') | ForEach-Object {
        ($_.SelectNodes('.//*[local-name()="t"]') | ForEach-Object InnerText) -join ''
    }) -join "`r`n`r`n"
    if ($text -match '2/10|3/10|remaining eight|remaining seven|eight conflict reviews|seven conflict reviews') {
        throw 'Outdated review count remains'
    }
    if (-not $text.Contains('10/10') -or -not $text.Contains('seven accepts') -or
        -not $text.Contains('three requests for additional testing')) {
        throw 'Current review summary is missing'
    }
    if (-not $text.Contains('13.5 hours') -or -not $text.Contains('September 2-10')) {
        throw 'Source effort statement was lost'
    }
    $text | Set-Content (Join-Path $PSScriptRoot 'progress-report-2-current-text.txt') -Encoding UTF8
}
finally {
    $zip.Dispose()
}

if ((Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash -ne $sourceHash) {
    throw 'Original source changed'
}

[ordered]@{
    source = $Source
    source_sha256 = $sourceHash
    output = $destination
    output_sha256 = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
    replacements = $edits.Count
    tables = $tableCount
    rows = $rowCount
    verified_primary_attempts = $primaryReport.attempt_count
    verified_conflict_reviews = $primaryReport.adjudication_summary.completed
    xml_parts_parse = 'pass'
    original_unchanged = $true
    visual_layout_checked = $false
} | ConvertTo-Json | Set-Content (Join-Path $PSScriptRoot 'document-verification-current.json') -Encoding UTF8

Write-Output "Created and structurally checked: $destination"
Write-Output "Preserved $tableCount tables and $rowCount rows; $($edits.Count) paragraphs updated; original unchanged."
