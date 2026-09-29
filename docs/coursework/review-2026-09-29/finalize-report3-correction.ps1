[CmdletBinding()]
param(
    [string]$InputPath = 'docs\coursework\review-2026-09-28\Progress Report 3 (Tony Tran).docx',
    [string]$OutputPath = 'docs\coursework\review-2026-09-29\Progress Report 3 (Tony Tran) - Corrected.docx',
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
    throw "Input report not found: $source"
}
if ((Test-Path -LiteralPath $target) -and -not $Overwrite) {
    throw "Output already exists; use -Overwrite to replace it: $target"
}

[IO.Directory]::CreateDirectory($allowedRoot) | Out-Null
Copy-Item -LiteralPath $source -Destination $target -Force

$w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
$archive = [IO.Compression.ZipFile]::Open($target, [IO.Compression.ZipArchiveMode]::Update)
try {
    $entry = $archive.GetEntry('word/document.xml')
    if (-not $entry) { throw 'DOCX is missing word/document.xml.' }

    $reader = [IO.StreamReader]::new($entry.Open(), [Text.Encoding]::UTF8)
    try { $xmlText = $reader.ReadToEnd() } finally { $reader.Dispose() }

    $doc = [Xml.XmlDocument]::new()
    $doc.PreserveWhitespace = $true
    $doc.LoadXml($xmlText)
    $ns = [Xml.XmlNamespaceManager]::new($doc.NameTable)
    $ns.AddNamespace('w', $w)

    function Get-NodeText {
        param([Xml.XmlElement]$Node)
        return (($Node.SelectNodes('.//w:t', $ns) | ForEach-Object { $_.InnerText }) -join '')
    }

    function Set-NodeText {
        param([Xml.XmlElement]$Node, [string]$Value)
        $texts = @($Node.SelectNodes('.//w:t', $ns))
        if ($texts.Count -lt 1) {
            throw "Node has no text element: $(Get-NodeText $Node)"
        }
        $texts[0].InnerText = $Value
        $space = $doc.CreateAttribute('xml', 'space', 'http://www.w3.org/XML/1998/namespace')
        $space.Value = 'preserve'
        [void]$texts[0].Attributes.Append($space)
        for ($i = 1; $i -lt $texts.Count; $i++) { $texts[$i].InnerText = '' }
    }

    function Find-ExactParagraph {
        param([string]$Text)
        $matches = @($doc.SelectNodes('//w:p', $ns) | Where-Object {
                (Get-NodeText ([Xml.XmlElement]$_)) -eq $Text
            })
        if ($matches.Count -ne 1) {
            throw "Expected one exact paragraph but found $($matches.Count): $Text"
        }
        return [Xml.XmlElement]$matches[0]
    }

    function Replace-ExactParagraph {
        param([string]$Old, [string]$New)
        Set-NodeText (Find-ExactParagraph $Old) $New
    }

    Replace-ExactParagraph `
        'Reporting checkpoint: September 14-28, 2026, following the September 13 Report 2 submission. I estimate 1.5 hours per day for fourteen days, approximately 42 hours, spent mainly reviewing the file structure and documentation, validating test and saved-evidence results, reviewing candidate patches and code snippets, supplying human-review rationales, preparing the evidence appendix and Video III materials, completing four peer-feedback responses, building the sanitized public evidence reference, and aligning the report with the professor''s feedback. This is my estimate, not a number inferred from commits or automated test time. Earlier reports recorded 31.5 hours plus a separate 13.5-hour September 2-10 period. The documented subtotal is approximately 67.5 hours plus any September 11-13 work not included in Report 2. Reconcile those dates and update this paragraph through the actual Report 3 cutoff before submitting.' `
        'Reporting checkpoint: September 14-28, 2026, following the September 13 Report 2 submission. I estimate 1.5 hours per day for fifteen days, approximately 22.5 hours, spent mainly reviewing the file structure and documentation, validating test and saved-evidence results, reviewing candidate patches and code snippets, supplying human-review rationales, preparing the evidence appendix and Video III materials, completing four peer-feedback responses, building the sanitized public evidence reference, and aligning the report with the professor''s feedback. This is my estimate, not a number inferred from commits or automated test time. Earlier reports recorded 31.5 hours plus a separate 13.5-hour September 2-10 period. The documented subtotal through September 28 is approximately 67.5 hours; it excludes any September 11-13 work not already included in Report 2.'

    Replace-ExactParagraph `
        'Finalize Report 3 for the planned October 1 early submission, ahead of the confirmed October 4 at 11:59 p.m. Canvas deadline: reconcile actual dates and hours, check each metric and cited source, complete the AI-use disclosure, transfer the draft into the course template, and inspect the rendered file before submitting.' `
        'Post Video III by October 6 and complete Peer Feedback Report III by October 11 at 11:59 p.m. Retain both submission receipts and incorporate applicable feedback into the next project report.'

    Replace-ExactParagraph `
        'This is the current plan, not a claim that future work has already occurred. The Progress Report 3 and Video III dates reflect the Canvas schedule confirmed on September 23; later course dates should still be checked in live Canvas. The September 24 draft is a checkpoint for Report 3, not its final reporting cutoff.' `
        'This timeline records completed milestones through the September 28 Progress Report 3 submission and planned work thereafter. The Video III and peer-feedback dates reflect the Canvas schedule confirmed in September; later course dates should still be checked in live Canvas.'

    Replace-ExactParagraph `
        'Verification: the full suite passed 119 automated tests in the September 24 accuracy review. The primary report verified 15/15 attempts and 10/10 original reviews; the supplemental report verified three baselines and 15 saved candidates; and the human-record verifier confirmed 14/14 completed records. The deployed public reference separately loaded 15 primary rows, 15 supplemental rows, ten original reviews, 14 later records, filters, candidate details, the workflow image, and the PDF appendix. Four guided pilot live replays previously matched their recorded decisions. Saved-evidence verification does not repeat model calls or every historical scanner/browser experiment. A clean committed-archive rehearsal remains to be completed before final delivery.' `
        'Verification: primary evidence, supplemental evidence, and all 14 human-record bindings were rechecked on September 28. The complete suite last passed 119 automated tests in the September 24 accuracy review. The primary report verified 15/15 attempts and 10/10 original reviews, and the supplemental report verified three baselines and 15 saved candidates. The deployed public reference separately loaded 15 primary rows, 15 supplemental rows, ten original reviews, 14 later records, filters, candidate details, the workflow image, and the PDF appendix. Four guided pilot live replays previously matched their recorded decisions. Saved-evidence verification does not repeat model calls or every historical scanner/browser experiment. A clean committed-archive rehearsal remains to be completed before final delivery.'

    Replace-ExactParagraph `
        'Generative AI disclosure: OpenAI ChatGPT/Codex assisted planning, implementation, debugging, test orchestration, documentation, evidence organization, and drafting. FixProof separately used the OpenAI API to generate recorded repair candidates. Tony Tran remains responsible for verifying claims and references, reporting actual effort, making human review decisions, and approving submitted text. Reconcile this statement with actual tool use and course disclosure requirements before submission.' `
        'Generative AI disclosure: OpenAI ChatGPT/Codex assisted planning, implementation, debugging, test orchestration, documentation, evidence organization, and drafting. FixProof separately used the OpenAI API to generate recorded repair candidates. Tony Tran remains responsible for verifying claims and references, reporting actual effort, making human review decisions, and approving the submitted text.'

    $timelineRows = @($doc.SelectNodes('//w:tbl/w:tr', $ns) | Where-Object {
            (Get-NodeText ([Xml.XmlElement]$_)) -like '*Planned early Progress Report 3 submission; official deadline October 4 at 11:59 p.m.*'
        })
    if ($timelineRows.Count -ne 1) {
        throw "Expected one Report 3 timeline row but found $($timelineRows.Count)."
    }
    $cells = @($timelineRows[0].SelectNodes('./w:tc', $ns))
    if ($cells.Count -ne 3) {
        throw "Expected three cells in the Report 3 timeline row but found $($cells.Count)."
    }
    Set-NodeText ([Xml.XmlElement]$cells[0]) 'September 28'
    Set-NodeText ([Xml.XmlElement]$cells[1]) 'Submit Progress Report 3; official deadline October 4 at 11:59 p.m.'
    Set-NodeText ([Xml.XmlElement]$cells[2]) 'Completed'

    foreach ($table in $doc.SelectNodes('//w:tbl', $ns)) {
        $rows = @($table.SelectNodes('./w:tr', $ns))
        for ($rowIndex = 0; $rowIndex -lt $rows.Count; $rowIndex++) {
            $row = [Xml.XmlElement]$rows[$rowIndex]
            $properties = $row.SelectSingleNode('./w:trPr', $ns)
            if (-not $properties) {
                $properties = $doc.CreateElement('w', 'trPr', $w)
                [void]$row.PrependChild($properties)
            }
            if (-not $properties.SelectSingleNode('./w:cantSplit', $ns)) {
                [void]$properties.AppendChild($doc.CreateElement('w', 'cantSplit', $w))
            }
            if ($rowIndex -eq 0 -and -not $properties.SelectSingleNode('./w:tblHeader', $ns)) {
                [void]$properties.AppendChild($doc.CreateElement('w', 'tblHeader', $w))
            }
        }
    }

    $finalText = (($doc.SelectNodes('//w:t', $ns) | ForEach-Object { $_.InnerText }) -join ' ')
    foreach ($forbidden in @(
            'approximately 42 hours',
            'planned October 1 early submission',
            'September 24 draft is a checkpoint',
            'Reconcile this statement',
            'Reconcile those dates')) {
        if ($finalText.Contains($forbidden)) {
            throw "Draft-only text remains after update: $forbidden"
        }
    }

    $newXml = $doc.OuterXml
    $entry.Delete()
    $newEntry = $archive.CreateEntry('word/document.xml', [IO.Compression.CompressionLevel]::Optimal)
    $writer = [IO.StreamWriter]::new($newEntry.Open(), [Text.UTF8Encoding]::new($false))
    try { $writer.Write($newXml) } finally { $writer.Dispose() }
} finally {
    $archive.Dispose()
}

Write-Output "Created corrected report: $target"
