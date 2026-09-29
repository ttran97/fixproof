[CmdletBinding()]
param(
    [string]$InputPath = 'docs\coursework\review-2026-09-29\FixProof - Video III - Final Recording Deck.pptx',
    [string]$OutputPath = 'docs\coursework\review-2026-09-29\FixProof - Video III - Reviewed Recording Deck.pptx',
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'

$projectRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $projectRoot) {
    throw 'Run this script from inside the FixProof repository.'
}

function Resolve-ProjectPath {
    param([string]$Path)
    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }
    return [IO.Path]::GetFullPath((Join-Path $projectRoot $Path))
}

$source = Resolve-ProjectPath $InputPath
$target = Resolve-ProjectPath $OutputPath
$allowedRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'docs\coursework\review-2026-09-29'))
$workflowSvg = [IO.Path]::GetFullPath((Join-Path $projectRoot 'docs\coursework\review-2026-09-22\fixproof-workflow-slide.svg'))
$pdfPath = [IO.Path]::ChangeExtension($target, '.pdf')
$renderDirectory = Join-Path $allowedRoot 'video-iii-reviewed-rendered-slides'

if (-not $target.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay inside docs/coursework/review-2026-09-29.'
}
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Input deck not found: $source"
}
if (-not (Test-Path -LiteralPath $workflowSvg -PathType Leaf)) {
    throw "Workflow diagram not found: $workflowSvg"
}
if ((Test-Path -LiteralPath $target) -and -not $Overwrite) {
    throw "Output already exists; use -Overwrite to replace it: $target"
}

if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Force }
if (Test-Path -LiteralPath $pdfPath) { Remove-Item -LiteralPath $pdfPath -Force }
if (Test-Path -LiteralPath $renderDirectory) {
    Remove-Item -LiteralPath $renderDirectory -Recurse -Force
}
[IO.Directory]::CreateDirectory($renderDirectory) | Out-Null
[IO.File]::Copy($source, $target, $true)

$msoFalse = 0
$msoTrue = -1
$ppSaveAsOpenXMLPresentation = 24
$ppSaveAsPDF = 32

function Get-ShapeText {
    param($Shape)
    try {
        if ($Shape.HasTextFrame -eq $msoTrue -and $Shape.TextFrame.HasText -eq $msoTrue) {
            return [string]$Shape.TextFrame.TextRange.Text
        }
    } catch { }
    return $null
}

function Set-ShapeTextContaining {
    param($Slide, [string]$Anchor, [string]$NewText)
    $matches = @()
    for ($i = 1; $i -le $Slide.Shapes.Count; $i++) {
        $shape = $Slide.Shapes.Item($i)
        $text = Get-ShapeText $shape
        if ($null -ne $text -and $text.Contains($Anchor)) {
            $matches += $shape
        }
    }
    if ($matches.Count -ne 1) {
        throw "Slide $($Slide.SlideIndex): expected one text shape containing '$Anchor'; found $($matches.Count)."
    }
    $matches[0].TextFrame.TextRange.Text = $NewText
}

function Replace-ShapeText {
    param($Slide, [string]$Old, [string]$New)
    $matches = 0
    for ($i = 1; $i -le $Slide.Shapes.Count; $i++) {
        $shape = $Slide.Shapes.Item($i)
        $text = Get-ShapeText $shape
        if ($null -ne $text -and $text.Contains($Old)) {
            $shape.TextFrame.TextRange.Text = $text.Replace($Old, $New)
            $matches++
        }
    }
    if ($matches -ne 1) {
        throw "Slide $($Slide.SlideIndex): expected one occurrence of '$Old'; found $matches."
    }
}

function Set-SpeakerNotes {
    param($Slide, [string]$Notes)
    $notesPage = $Slide.NotesPage
    for ($i = 1; $i -le $notesPage.Shapes.Count; $i++) {
        $shape = $notesPage.Shapes.Item($i)
        try {
            if ($shape.Type -eq 14 -and $shape.PlaceholderFormat.Type -eq 2) {
                $shape.TextFrame.TextRange.Text = $Notes
                $shape.TextFrame.TextRange.Font.Name = 'Aptos'
                $shape.TextFrame.TextRange.Font.Size = 12
                return
            }
        } catch { }
    }
    throw "Speaker notes placeholder not found for slide $($Slide.SlideIndex)."
}

$powerPoint = $null
$presentation = $null
$usedExistingPowerPoint = $false
try {
    try {
        $powerPoint = [Runtime.InteropServices.Marshal]::GetActiveObject('PowerPoint.Application')
        $usedExistingPowerPoint = $true
    } catch {
        $powerPoint = New-Object -ComObject PowerPoint.Application
    }

    $presentation = $powerPoint.Presentations.Open($target, $msoFalse, $msoFalse, $msoFalse)

    # Slide 3: replace the raster diagram with the corrected source SVG.
    $slide = $presentation.Slides.Item(3)
    while ($slide.Shapes.Count -gt 0) { $slide.Shapes.Item(1).Delete() }
    $null = $slide.Shapes.AddPicture($workflowSvg, $msoFalse, $msoTrue, 0, 0, 960, 540)
    Set-SpeakerNotes $slide @'
Walk left to right through primary-v1: controlled fixtures, focused repair prompt, copied workspace, separate validators, deterministic policy, and human review for selected cases. Supplemental-v1 later reused saved inputs and candidates, made no new model calls, and stored later qualifications without rewriting the primary record. The supplemental cases were predefined and frozen in the project's internal registry before candidate execution; this was not an external public preregistration. Copied workspaces preserve study inputs; they are not security sandboxes.
'@

    # Slide 5: state the status of the supplemental registry precisely.
    $slide = $presentation.Slides.Item(5)
    Replace-ShapeText $slide 'registered case definitions' 'frozen case definitions'
    Set-SpeakerNotes $slide @'
The supplement first characterized each vulnerable baseline, then applied the same relevant cases to the five saved candidates for that CWE. The 28 case definitions were recorded and frozen in the project's internal registry before candidate execution. The 140 observations are case-level outcomes, not 140 patches. Security, parity, and robustness answer different questions, so I report their denominators separately. Five traversal symlink observations remain inconclusive, not passed.
'@

    # Slide 6: replace tool-like arrows and vague paths with the actual evidence chain.
    $slide = $presentation.Slides.Item(6)
    Replace-ShapeText $slide 'Use the public reference first; open a raw saved artifact only if time allows' 'Open the public evidence first; keep raw artifacts as technical backup'
    Set-ShapeTextContaining $slide 'trial-plan.json ->' 'Five calls per CWE; all 15 completed'
    Set-ShapeTextContaining $slide 'primary dashboard/report ->' 'Target SAST finding persisted; runtime suites passed'
    Set-ShapeTextContaining $slide 'XSS 03 String(value)' 'String(value) vs String(value ?? "")'
    Replace-ShapeText $slide 'Registered result' 'Frozen case result'
    Set-ShapeTextContaining $slide 'XSS-P01 ->' 'XSS-P01: undefined (pass) vs blank (fail)'
    Replace-ShapeText $slide 'Human record' 'Later decision'
    Set-ShapeTextContaining $slide 'XSS 04 ->' 'XSS 04: reject candidate for parity'
    Set-ShapeTextContaining $slide 'fixproof.netlify.app' @'
fixproof.netlify.app
  filter: Reflected XSS
  open: XSS 04

Where tests ran:
  saved candidate app/app.js
  localhost (127.0.0.1)
  disposable workspace copy

Raw evidence backup:
  candidate.patch
  supplemental result.json
  follow-up result.json
'@
    Set-SpeakerNotes $slide @'
Switch to https://fixproof.netlify.app/. Explain that this is a sanitized, read-only presentation layer over the saved evidence. Filter to Reflected XSS and open XSS 04. Point to the frozen primary result, the XSS-P01 parity failure, the original and later human records, and the patch excerpt. If asked where the application ran, explain that validators launched the saved candidate app/app.js on 127.0.0.1 inside a disposable workspace copy. The website displays results; it does not execute the app, replay tests, or call the model.
'@

    # Slide 7: remove the ambiguity that the attacks themselves "passed."
    $slide = $presentation.Slides.Item(7)
    Replace-ShapeText $slide 'Both passed the registered attacks; one changed missing-input behavior' 'Both blocked the registered XSS attacks; one changed missing-input behavior'
    Set-ShapeTextContaining $slide 'Supplement: 9 pass' 'Registered supplement: 9 pass | parity 5/5'
    Set-ShapeTextContaining $slide 'Supplement: 8 pass' 'Registered supplement: 8 pass | 1 parity fail'
    Set-ShapeTextContaining $slide 'Both security: 3/3 pass.' 'Both supplemental security: 3/3 pass. XSS 04 was later rejected for parity, not continued exploitability.'
    Set-SpeakerNotes $slide @'
This is the central comparison. Both candidates encode HTML and blocked all three registered supplemental XSS attacks. XSS 03 uses String(value), so an omitted name remains the text undefined and passes all five parity cases. XSS 04 uses nullish coalescing to replace a missing name with an empty string, so XSS-P01 fails exact parity. The later rejection is bounded to the frozen parity criterion; it does not mean the registered XSS attacks still worked.
'@

    # Slide 8: keep only current, concrete milestones.
    $slide = $presentation.Slides.Item(8)
    Set-ShapeTextContaining $slide '- Report 3 submitted:' @'
- Report 3 submitted: September 28
- Video III / peer feedback: October 6 / 11
- Progress Report 4: October 18, 11:59 p.m.
- Report 4 focus: controls, related work, reproducibility
'@
    Set-ShapeTextContaining $slide 'Student reference:' 'Student reference: fixproof.netlify.app | Report 4 feedback: second fixture or symlink-capable PATH-S06 rerun?'
    Set-SpeakerNotes $slide @'
The original ten reviews and the later fourteen records are separate evidence layers. The later decisions include five rejections, five bounded SQLi acceptances, and four traversal requests for more testing. Tell students that https://fixproof.netlify.app/ is a read-only reference for all 15 candidates, tests, and rationales. State the limits explicitly. Then ask which bounded extension would strengthen confidence more for Report 4: adding a second fixture for an existing CWE or resolving PATH-S06 in a symlink-capable environment. Progress Report 4 is due October 18 and will focus on control and failure-handling evidence, related-work comparison, limitations, and reproducibility. Close with the course AI-use disclosure: Codex and ChatGPT assisted implementation, analysis, documentation, and presentation preparation; separate saved OpenAI API calls proposed experimental repairs; I made the recorded human decisions and remain responsible for the claims.
'@

    # Slide 9: clarify that each candidate passed both complete primary suites.
    $slide = $presentation.Slides.Item(9)
    $primarySummaryOld = 'Primary security + functional: 5/5 candidates pass'
    $primarySummaryNew = 'Primary security and functional suites: all 5 candidates passed'
    $summaryMatches = 0
    for ($i = 1; $i -le $slide.Shapes.Count; $i++) {
        $shape = $slide.Shapes.Item($i)
        $text = Get-ShapeText $shape
        if ($null -ne $text -and $text.Contains($primarySummaryOld)) {
            $shape.TextFrame.TextRange.Text = $text.Replace($primarySummaryOld, $primarySummaryNew)
            $summaryMatches++
        }
    }
    if ($summaryMatches -ne 2) {
        throw "Slide 9: expected two primary-suite summaries; found $summaryMatches."
    }

    $presentation.SaveAs($target, $ppSaveAsOpenXMLPresentation)
    $presentation.SaveAs($pdfPath, $ppSaveAsPDF)
    $presentation.Export($renderDirectory, 'PNG', 1600, 900)
    $presentation.Close()
    $presentation = $null
} finally {
    if ($presentation) {
        try { $presentation.Close() } catch { }
    }
    if ($powerPoint) {
        if (-not $usedExistingPowerPoint) {
            try { $powerPoint.Quit() } catch { }
        }
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint)
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($target)
try {
    $slideCount = @($archive.Entries | Where-Object { $_.FullName -match '^ppt/slides/slide\d+\.xml$' }).Count
    $notesCount = @($archive.Entries | Where-Object { $_.FullName -match '^ppt/notesSlides/notesSlide\d+\.xml$' }).Count
} finally {
    $archive.Dispose()
}
if ($slideCount -ne 9 -or $notesCount -ne 9) {
    throw "Unexpected deck structure: $slideCount slides, $notesCount notes."
}

$verification = [ordered]@{
    generated_on = (Get-Date).ToString('o')
    source = $source
    output = $target
    pdf = $pdfPath
    rendered_slides = $renderDirectory
    slides = $slideCount
    speaker_notes = $notesCount
    changes = @(
        'Clarified internal frozen case registry; no claim of public preregistration.'
        'Changed ambiguous attack wording to blocked registered attacks.'
        'Added exact app.js execution context and simplified the evidence chain.'
        'Separated supplemental category counts on the XSS comparison slide.'
        'Replaced the repeated second-reviewer question with a Report 4 scope question.'
        'Made the October 18 Report 4 scope and deadline explicit.'
    )
    pptx_bytes = (Get-Item -LiteralPath $target).Length
    pdf_bytes = (Get-Item -LiteralPath $pdfPath).Length
    pptx_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    package_structure = 'pass'
}
$verificationPath = Join-Path $allowedRoot 'Video-III-reviewed-deck-verification.json'
$verification | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $verificationPath -Encoding utf8

Write-Output "Created: $target"
Write-Output "Created: $pdfPath"
Write-Output "Rendered slides: $renderDirectory"
