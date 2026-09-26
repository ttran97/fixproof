[CmdletBinding()]
param(
    [string]$InputPath = 'docs\coursework\review-2026-09-21\Progress Report 3 (Tony Tran) - Working Draft September 23 - Professor Feedback Aligned.docx',
    [string]$OutputPath = 'docs\coursework\review-2026-09-21\Progress Report 3 (Tony Tran) - Working Draft September 24 - Website and Feedback Aligned.docx',
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
$allowedRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'docs\coursework\review-2026-09-21'))
if (-not $target.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay inside docs/coursework/review-2026-09-21.'
}
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Input report not found: $source"
}
if ((Test-Path -LiteralPath $target) -and -not $Overwrite) {
    throw "Output already exists; use -Overwrite to replace it: $target"
}

Copy-Item -LiteralPath $source -Destination $target -Force

$w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
$archive = [IO.Compression.ZipFile]::Open($target, [System.IO.Compression.ZipArchiveMode]::Update)
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

    function Get-ParagraphText {
        param([Xml.XmlElement]$Paragraph)
        return (($Paragraph.SelectNodes('.//w:t', $ns) | ForEach-Object { $_.InnerText }) -join '')
    }

    function Set-ParagraphText {
        param([Xml.XmlElement]$Paragraph, [string]$Value)
        $texts = @($Paragraph.SelectNodes('.//w:t', $ns))
        if ($texts.Count -lt 1) {
            throw "Paragraph has no text node: $(Get-ParagraphText $Paragraph)"
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
                (Get-ParagraphText ([Xml.XmlElement]$_)) -eq $Text
            })
        if ($matches.Count -ne 1) {
            throw "Expected one exact paragraph but found $($matches.Count): $Text"
        }
        return [Xml.XmlElement]$matches[0]
    }

    function Replace-ExactParagraph {
        param([string]$Old, [string]$New)
        $paragraph = Find-ExactParagraph $Old
        Set-ParagraphText $paragraph $New
    }

    Replace-ExactParagraph `
        'Progress Report 3 - working draft; evidence verified through September 23, 2026' `
        'Progress Report 3 - working draft; evidence verified through September 24, 2026'

    Replace-ExactParagraph `
        'Submission checkpoint: Update actual dates and hours through the submission date, reconcile September 11-13 work, check the live Canvas template and deadline, and personally verify the AI-use disclosure before submitting.' `
        'Submission checkpoint: Update actual dates and hours through the planned October 1 submission, reconcile September 11-13 work, complete template-specific fields, and personally verify the AI-use disclosure. The confirmed Canvas deadline is October 4 at 11:59 p.m.'

    $oldCompleted = 'Reviewed repository structure, documentation, test-code snippets and saved results, and supplied human rationales. Video II was posted; Video II peer feedback remains in progress and is separate from this project evaluation.'
    $completedParagraph = Find-ExactParagraph $oldCompleted
    Set-ParagraphText $completedParagraph 'Reviewed repository structure, documentation, test-code snippets and saved results, and supplied human rationales. Video II was posted, and I completed the required Video II peer-feedback activity by submitting four feedback responses. Peer feedback remains a separate course deliverable rather than a FixProof evaluation outcome.'
    $websiteParagraph = [Xml.XmlElement]$completedParagraph.CloneNode($true)
    Set-ParagraphText $websiteParagraph 'Built, privacy-checked, and browser-validated a sanitized static evidence reference at https://fixproof.netlify.app/. It presents all 15 primary and supplemental candidate rows, ten original reviews, 14 later records, rationales, patch excerpts, the workflow figure, and the PDF appendix. It performs no model calls, scans, application execution, approval, or deployment and does not change any experimental denominator or result.'
    [void]$completedParagraph.ParentNode.InsertAfter($websiteParagraph, $completedParagraph)

    Replace-ExactParagraph `
        'Reporting checkpoint: September 14-23, 2026, following the September 13 Report 2 submission. I estimate 1.5 hours per day for ten days, approximately 15 hours, spent mainly reviewing the file structure and documentation, validating test and saved-evidence results, reviewing candidate patches and code snippets, supplying human-review rationales, and aligning the report with the professor''s feedback. This is my estimate, not a number inferred from commits or automated test time. Earlier reports recorded 31.5 hours plus a separate 13.5-hour September 2-10 period. The documented subtotal is approximately 60 hours plus any September 11-13 work not included in Report 2. Reconcile those dates and update this paragraph through the actual Report 3 cutoff before submitting.' `
        'Reporting checkpoint: September 14-24, 2026, following the September 13 Report 2 submission. I estimate 1.5 hours per day for eleven days, approximately 16.5 hours, spent mainly reviewing the file structure and documentation, validating test and saved-evidence results, reviewing candidate patches and code snippets, supplying human-review rationales, preparing the evidence appendix and Video III materials, completing four peer-feedback responses, building the sanitized public evidence reference, and aligning the report with the professor''s feedback. This is my estimate, not a number inferred from commits or automated test time. Earlier reports recorded 31.5 hours plus a separate 13.5-hour September 2-10 period. The documented subtotal is approximately 61.5 hours plus any September 11-13 work not included in Report 2. Reconcile those dates and update this paragraph through the actual Report 3 cutoff before submitting.'

    Replace-ExactParagraph `
        'Complete the Video II peer-feedback assignment by September 27, separately from Report 3, and retain the submission receipt.' `
        'Summarize applicable themes from the four submitted Video II feedback responses and incorporate them when they materially improve Video III or the final report. Retain the submission receipt separately from the FixProof evidence.'

    Replace-ExactParagraph `
        'Finalize Report 3 for the planned October 1 submission: reconcile actual dates and hours, confirm the live Canvas deadline, check each metric and cited source, complete the AI-use disclosure, transfer the draft into the course template, and inspect the rendered file before submitting.' `
        'Finalize Report 3 for the planned October 1 early submission, ahead of the confirmed October 4 at 11:59 p.m. Canvas deadline: reconcile actual dates and hours, check each metric and cited source, complete the AI-use disclosure, transfer the draft into the course template, and inspect the rendered file before submitting.'

    Replace-ExactParagraph `
        'Prepare Video III using one saved primary candidate and its supplemental comparison. Explain XSS 03 versus XSS 04 or the later XSS 01-02 qualifications, then rehearse a bounded pilot replay without calling it a rerun of the primary study.' `
        'Prepare Video III around XSS 03 versus XSS 04. Use the read-only public evidence reference to show the patch, independent evidence channels, XSS-P01 parity result, and separate human boundary. Keep raw saved artifacts as technical backup, and do not call the website or a pilot replay a rerun of the frozen primary study.'

    Replace-ExactParagraph `
        'This is the current plan, not a claim that future work has already occurred. The Progress Report 3 and Video III dates reflect the Canvas schedule confirmed on September 23; later course dates should still be checked in live Canvas. The September 23 draft is a checkpoint for Report 3, not its final reporting cutoff.' `
        'This is the current plan, not a claim that future work has already occurred. The Progress Report 3 and Video III dates reflect the Canvas schedule confirmed on September 23; later course dates should still be checked in live Canvas. The September 24 draft is a checkpoint for Report 3, not its final reporting cutoff.'

    Replace-ExactParagraph `
        'Pearce et al. (2022) motivate treating generated code as untrusted. Pearce et al. (2023) study multi-model zero-shot repair and reports functional-correctness challenges. Kulsum et al. (2024) use external compiler, sanitizer, and test feedback for iterative repair; FixProof does not claim validation feedback is new. Its bounded contribution is the auditable combination of stage-level evidence, deterministic disposition, and preserved human qualifications for three Express weaknesses. Datasets and success definitions differ, so cross-study success rates are not directly comparable.' `
        'Pearce et al. (2022) motivate treating generated code as untrusted. Pearce et al. (2023) study multi-model zero-shot repair and report functional-correctness challenges. Kulsum et al. (2024) use external compiler, sanitizer, and test feedback for iterative repair; FixProof does not claim validation feedback is new. Its bounded contribution is the auditable combination of stage-level evidence, deterministic disposition, and preserved human qualifications for three Express weaknesses. Datasets and success definitions differ, so cross-study success rates are not directly comparable.'

    Replace-ExactParagraph `
        'Evidence index: docs/study-protocol-v1.md and benchmarks/primary/v1/ define the frozen primary study; data/primary_trials/v1/ and data/primary_reviews/v1/ preserve candidates and original reviews; data/evaluation/primary-report.json provides the verified primary report. docs/supplemental-protocol-v1.md, data/supplemental/v1/, and docs/supplemental-results-v1.md preserve the later protocol, observations, and 14 recorded human results. The September 22 review worksheet links the evidence used for the nine newest records. docs/README.md separates current references from historical drafts.' `
        'Evidence index: docs/study-protocol-v1.md and benchmarks/primary/v1/ define the frozen primary study; data/primary_trials/v1/ and data/primary_reviews/v1/ preserve candidates and original reviews; data/evaluation/primary-report.json provides the verified primary report. docs/supplemental-protocol-v1.md, data/supplemental/v1/, and docs/supplemental-results-v1.md preserve the later protocol, observations, and 14 recorded human results. The September 22 review worksheet links the evidence used for the nine newest records. fixproof-public/ contains the sanitized static reference deployed at https://fixproof.netlify.app/; it is a presentation artifact, not experimental evidence. docs/README.md separates current references from historical drafts.'

    Replace-ExactParagraph `
        'Verification: the full suite passed 119 automated tests in the September 23 accuracy review. The primary report verified 15/15 attempts and 10/10 original reviews; the supplemental report verified three baselines and 15 saved candidates; and the human-record verifier confirmed 14/14 completed records. Four guided pilot live replays previously matched their recorded decisions. Saved-evidence verification does not repeat model calls or every historical scanner/browser experiment. A clean committed-archive rehearsal remains to be completed before final delivery.' `
        'Verification: the full suite passed 119 automated tests in the September 24 accuracy review. The primary report verified 15/15 attempts and 10/10 original reviews; the supplemental report verified three baselines and 15 saved candidates; and the human-record verifier confirmed 14/14 completed records. The deployed public reference separately loaded 15 primary rows, 15 supplemental rows, ten original reviews, 14 later records, filters, candidate details, the workflow image, and the PDF appendix. Four guided pilot live replays previously matched their recorded decisions. Saved-evidence verification does not repeat model calls or every historical scanner/browser experiment. A clean committed-archive rehearsal remains to be completed before final delivery.'

    Replace-ExactParagraph 'September 27' 'September 24'
    Replace-ExactParagraph `
        'Submit Video II peer feedback' `
        'Submit four Video II feedback responses and deploy sanitized public evidence reference'
    Replace-ExactParagraph 'In progress' 'Completed'
    Replace-ExactParagraph `
        'Planned Progress Report 3 submission with actual effort and verified claims; confirm live Canvas deadline' `
        'Planned early Progress Report 3 submission; official deadline October 4 at 11:59 p.m.'
    Replace-ExactParagraph `
        'Post Video III and submit peer feedback' `
        'Post Video III on October 6; submit Peer Feedback Report III by October 11 at 11:59 p.m.'

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

    $newXml = $doc.OuterXml
    $entry.Delete()
    $newEntry = $archive.CreateEntry('word/document.xml', [IO.Compression.CompressionLevel]::Optimal)
    $writer = [IO.StreamWriter]::new($newEntry.Open(), [Text.UTF8Encoding]::new($false))
    try { $writer.Write($newXml) } finally { $writer.Dispose() }
} finally {
    $archive.Dispose()
}

Write-Output "Created: $target"
