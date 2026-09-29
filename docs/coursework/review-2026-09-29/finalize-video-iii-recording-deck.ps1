[CmdletBinding()]
param(
    [string]$InputPath = 'docs\coursework\review-2026-09-29\FixProof - Video III - Reviewed Recording Deck.pptx',
    [string]$OutputPath = 'docs\coursework\review-2026-09-29\FixProof - Video III - Final Validated Recording Deck.pptx',
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
$projectRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $projectRoot) {
    throw 'Run this script from inside the FixProof repository.'
}

function Resolve-ProjectPath {
    param([string]$Path)
    if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
    return [IO.Path]::GetFullPath((Join-Path $projectRoot $Path))
}

$source = Resolve-ProjectPath $InputPath
$target = Resolve-ProjectPath $OutputPath
$allowedRoot = Resolve-ProjectPath 'docs\coursework\review-2026-09-29'
$workflowSvg = Resolve-ProjectPath 'docs\coursework\review-2026-09-22\fixproof-workflow-slide.svg'
$pdfPath = [IO.Path]::ChangeExtension($target, '.pdf')
$renderDirectory = Join-Path $allowedRoot 'video-iii-final-validated-rendered-slides'

if (-not $target.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay inside docs/coursework/review-2026-09-29.'
}
foreach ($required in @($source, $workflowSvg)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required source not found: $required"
    }
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
        if ($null -ne $text -and $text.Contains($Anchor)) { $matches += $shape }
    }
    if ($matches.Count -ne 1) {
        throw "Slide $($Slide.SlideIndex): expected one shape containing '$Anchor'; found $($matches.Count)."
    }
    $matches[0].TextFrame.TextRange.Text = $NewText
}

function Set-SpeakerNotes {
    param($Slide, [string]$Notes)
    # Windows PowerShell 5.1 can reinterpret an em dash saved as UTF-8.
    # Normalize that three-character artifact before writing notes into the deck.
    $badUtf8Dash = -join @([char]0x00E2, [char]0x20AC, [char]0x201D)
    $Notes = $Notes.Replace($badUtf8Dash, ': ')
    for ($i = 1; $i -le $Slide.NotesPage.Shapes.Count; $i++) {
        $shape = $Slide.NotesPage.Shapes.Item($i)
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

    # Slide 2: state the research question, controls, and role boundaries plainly.
    $slide = $presentation.Slides.Item(2)
    Set-ShapeTextContaining $slide 'What this bench measures' 'What this benchmark measures and what it does not.'
    Set-ShapeTextContaining $slide 'Can separately recorded static' 'Can FixProof identify failed or behavior-changing patches that SAST alone could classify as successful?'
    Set-ShapeTextContaining $slide 'Controlled model setup' 'Controlled model setup'
    Set-ShapeTextContaining $slide 'gpt-5.2' @'
gpt-5.2
Prompt template v1.0
Model could not run tools/tests
5 initial model calls per fixture (15 total)
'@
    Set-ShapeTextContaining $slide 'Separated roles' 'Separated roles'
    Set-ShapeTextContaining $slide 'Model proposes' @'
Model proposes code
Validators record evidence
Policy routes the result
Humans review selected cases
'@
    Set-ShapeTextContaining $slide 'One fixture per CWE' 'The 15 calls are repeated repairs of three applications, not 15 independent applications.'
    Set-SpeakerNotes $slide @'
FixProof asks whether multi-stage evidence can identify failed or behavior-changing patches that a SAST-only decision could classify as successful. The benchmark is intentionally small: one Express application for each of three CWEs, with five scheduled initial calls per application. I held the model, prompt template, tool setting, and call schedule constant. The model could not run a terminal, browser, scanner, application, or tests; it only proposed code from the frozen prompt. FixProof validated each saved candidate separately. Sampling used provider defaults and no seed, so generated outputs were not deterministic. The results describe these three applications and do not estimate production performance.
'@

    # Slide 3: use the corrected architecture source with explicit branch labels.
    $slide = $presentation.Slides.Item(3)
    while ($slide.Shapes.Count -gt 0) { $slide.Shapes.Item(1).Delete() }
    $null = $slide.Shapes.AddPicture($workflowSvg, $msoFalse, $msoTrue, 0, 0, 960, 540)
    Set-SpeakerNotes $slide @'
Walk left to right through primary-v1: controlled fixtures, a focused repair prompt, a copied workspace, separate validators, and deterministic policy. Every automated outcome is preserved in the primary record. Cases selected for review branch from policy to human review, and the verdict and rationale return to that record. Supplemental-v1 later reused the saved baseline and 15 candidates, made no new model calls, and ran cases frozen in the project's internal registry. Separate outcomes and the original primary evidence inform a later human follow-up. That follow-up qualifies the result without rewriting primary-v1. Copied workspaces preserve study inputs; they are not security sandboxes.
'@

    # Slide 8: synchronize the visible Report 4 plan with the recording notes.
    $slide = $presentation.Slides.Item(8)
    Set-ShapeTextContaining $slide 'NEXT COURSE MILESTONES' 'PROGRESS REPORT 4 NEXT STEPS'
    Set-SpeakerNotes $slide @'
The ten original reviews and fourteen later records remain separate evidence layers. The later records include five rejections, five bounded SQLi acceptances, and four traversal requests for more testing; no primary result was overwritten. For Progress Report 4, I will summarize Video III feedback, freeze any new test plan before execution, attempt PATH-S06 in a symlink-capable environment, and verify controls, failure handling, and reproduction. My feedback question is: which next step would increase confidence more—testing FixProof on another vulnerable application or completing the path-traversal test that Windows could not run? Progress Report 4 is due October 18 according to the supplied schedule; I will confirm the live Canvas assignment. Codex and ChatGPT assisted implementation, analysis, documentation, and presentation preparation; separate saved OpenAI API calls proposed experimental repairs. I made the recorded human decisions and remain responsible for the claims.
'@

    $presentation.SaveAs($target, $ppSaveAsOpenXMLPresentation)
    $presentation.SaveAs($pdfPath, $ppSaveAsPDF)
    $presentation.Export($renderDirectory, 'PNG', 1600, 900)
    $presentation.Close()
    $presentation = $null
} finally {
    if ($presentation) { try { $presentation.Close() } catch { } }
    if ($powerPoint) {
        if (-not $usedExistingPowerPoint) { try { $powerPoint.Quit() } catch { } }
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
    pptx_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    package_structure = 'pass'
    recording_status = 'pending visual and evidence validation'
}
$verificationPath = Join-Path $allowedRoot 'Video-III-final-validated-deck-verification.json'
$verification | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $verificationPath -Encoding utf8

Write-Output "Created: $target"
Write-Output "Created: $pdfPath"
Write-Output "Rendered slides: $renderDirectory"
