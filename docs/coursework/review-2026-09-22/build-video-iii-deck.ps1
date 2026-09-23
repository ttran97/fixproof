[CmdletBinding()]
param(
    [string]$OutputPath = 'docs\coursework\review-2026-09-22\FixProof - Video III - Recording Deck.pptx',
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'

$projectRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $projectRoot) {
    throw 'Run this script from inside the FixProof repository.'
}

$target = if ([IO.Path]::IsPathRooted($OutputPath)) {
    [IO.Path]::GetFullPath($OutputPath)
} else {
    [IO.Path]::GetFullPath((Join-Path $projectRoot $OutputPath))
}
$allowedRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'docs\coursework\review-2026-09-22'))
if (-not $target.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay inside docs/coursework/review-2026-09-22.'
}
if ((Test-Path -LiteralPath $target) -and -not $Overwrite) {
    throw "Output already exists; use -Overwrite to replace it: $target"
}

$workflowImage = Join-Path $allowedRoot 'fixproof-workflow-slide.png'
if (-not (Test-Path -LiteralPath $workflowImage -PathType Leaf)) {
    throw "Workflow image not found: $workflowImage"
}

$outputDirectory = Split-Path -Parent $target
$pdfPath = [IO.Path]::ChangeExtension($target, '.pdf')
$renderDirectory = Join-Path $outputDirectory 'video-iii-rendered-slides'
if (-not (Test-Path -LiteralPath $renderDirectory)) {
    New-Item -ItemType Directory -Path $renderDirectory | Out-Null
}

function Convert-HexColor {
    param([Parameter(Mandatory)][string]$Hex)
    $value = $Hex.TrimStart('#')
    if ($value.Length -ne 6) { throw "Invalid color: $Hex" }
    $r = [Convert]::ToInt32($value.Substring(0, 2), 16)
    $g = [Convert]::ToInt32($value.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($value.Substring(4, 2), 16)
    return $r + (256 * $g) + (65536 * $b)
}

$C = @{
    Navy = Convert-HexColor '#0B2447'
    Ink = Convert-HexColor '#102A4D'
    Slate = Convert-HexColor '#526C8E'
    Muted = Convert-HexColor '#6B7F99'
    Line = Convert-HexColor '#B9CBE1'
    Background = Convert-HexColor '#F5F7FA'
    White = Convert-HexColor '#FFFFFF'
    Blue = Convert-HexColor '#5878A5'
    BlueLight = Convert-HexColor '#EAF1FA'
    Gold = Convert-HexColor '#D9A64E'
    GoldLight = Convert-HexColor '#FFF3DE'
    Green = Convert-HexColor '#68A89A'
    GreenLight = Convert-HexColor '#E8F5F1'
    Purple = Convert-HexColor '#8D79B4'
    PurpleLight = Convert-HexColor '#EFEAFA'
    Red = Convert-HexColor '#B35D5B'
    RedLight = Convert-HexColor '#FBECEA'
    GrayLight = Convert-HexColor '#EDF1F6'
}

$ppLayoutBlank = 12
$ppSaveAsOpenXMLPresentation = 24
$ppSaveAsPDF = 32
$msoTextOrientationHorizontal = 1
$msoShapeRectangle = 1
$msoShapeRoundedRectangle = 5
$msoShapeOval = 9
$msoFalse = 0
$msoTrue = -1

function Add-TextBox {
    param(
        $Slide,
        [double]$Left,
        [double]$Top,
        [double]$Width,
        [double]$Height,
        [string]$Text,
        [double]$FontSize = 18,
        [int]$Color = $C.Ink,
        [switch]$Bold,
        [string]$FontName = 'Aptos',
        [int]$Align = 1,
        [int]$VerticalAnchor = 1,
        [double]$Margin = 0
    )
    $shape = $Slide.Shapes.AddTextbox(
        $msoTextOrientationHorizontal, $Left, $Top, $Width, $Height)
    $shape.TextFrame.MarginLeft = $Margin
    $shape.TextFrame.MarginRight = $Margin
    $shape.TextFrame.MarginTop = $Margin
    $shape.TextFrame.MarginBottom = $Margin
    $shape.TextFrame.WordWrap = $msoTrue
    $shape.TextFrame.AutoSize = 0
    $shape.TextFrame2.VerticalAnchor = $VerticalAnchor
    $range = $shape.TextFrame.TextRange
    $range.Text = $Text
    $range.Font.Name = $FontName
    $range.Font.Size = $FontSize
    $range.Font.Bold = if ($Bold) { $msoTrue } else { $msoFalse }
    $range.Font.Color.RGB = $Color
    $range.ParagraphFormat.Alignment = $Align
    $range.ParagraphFormat.SpaceAfter = 0
    return $shape
}

function Add-Box {
    param(
        $Slide,
        [double]$Left,
        [double]$Top,
        [double]$Width,
        [double]$Height,
        [int]$Fill,
        [int]$Line = $C.Line,
        [double]$Radius = 5,
        [double]$LineWeight = 1.25
    )
    $kind = if ($Radius -gt 0) { $msoShapeRoundedRectangle } else { $msoShapeRectangle }
    $shape = $Slide.Shapes.AddShape($kind, $Left, $Top, $Width, $Height)
    $shape.Fill.ForeColor.RGB = $Fill
    $shape.Fill.Transparency = 0
    $shape.Line.ForeColor.RGB = $Line
    $shape.Line.Weight = $LineWeight
    return $shape
}

function Add-Pill {
    param($Slide, [double]$Left, [double]$Top, [double]$Width,
        [string]$Text, [int]$Fill, [int]$TextColor = $C.Navy)
    $null = Add-Box $Slide $Left $Top $Width 24 $Fill $Fill 5 0.5
    $null = Add-TextBox $Slide ($Left + 5) ($Top + 2) ($Width - 10) 19 $Text 11 $TextColor -Bold -Align 2 -VerticalAnchor 3
}

function Add-Title {
    param($Slide, [string]$Title, [string]$Subtitle = '')
    $null = Add-TextBox $Slide 42 24 850 45 $Title 28 $C.Navy -Bold
    if ($Subtitle) {
        $null = Add-TextBox $Slide 44 65 850 28 $Subtitle 13 $C.Slate
    }
    $line = $Slide.Shapes.AddLine(42, 92, 918, 92)
    $line.Line.ForeColor.RGB = $C.Line
    $line.Line.Weight = 1.25
}

function Add-Footer {
    param($Slide, [int]$Number, [string]$Label = 'CS6727 | FixProof Video III')
    $null = Add-TextBox $Slide 42 515 720 16 $Label 9.5 $C.Muted
    $null = Add-TextBox $Slide 875 514 42 16 ([string]$Number) 10 $C.Muted -Bold -Align 3
}

function New-DeckSlide {
    param($Presentation)
    $slide = $Presentation.Slides.Add($Presentation.Slides.Count + 1, $ppLayoutBlank)
    $slide.FollowMasterBackground = $msoFalse
    $slide.Background.Fill.ForeColor.RGB = $C.Background
    return $slide
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
        } catch {
            continue
        }
    }
    throw "Speaker notes placeholder not found for slide $($Slide.SlideIndex)."
}

function Add-MetricCard {
    param($Slide, [double]$Left, [double]$Top, [double]$Width,
        [string]$Value, [string]$Label, [int]$Fill, [int]$Accent)
    $null = Add-Box $Slide $Left $Top $Width 86 $Fill $Accent 5 1.4
    $null = Add-TextBox $Slide ($Left + 12) ($Top + 10) ($Width - 24) 38 $Value 25 $C.Navy -Bold -Align 2 -VerticalAnchor 3
    $null = Add-TextBox $Slide ($Left + 10) ($Top + 50) ($Width - 20) 23 $Label 10.5 $C.Slate -Align 2 -VerticalAnchor 3
}

function Add-TableGrid {
    param($Slide, [double]$Left, [double]$Top, [double[]]$Widths,
        [object[]]$Rows, [double]$RowHeight = 37, [double]$FontSize = 11.5)
    for ($rowIndex = 0; $rowIndex -lt $Rows.Count; $rowIndex++) {
        $x = $Left
        for ($columnIndex = 0; $columnIndex -lt $Widths.Count; $columnIndex++) {
            $fill = if ($rowIndex -eq 0) { $C.Navy } elseif ($rowIndex % 2 -eq 0) { $C.BlueLight } else { $C.White }
            $textColor = if ($rowIndex -eq 0) { $C.White } else { $C.Ink }
            $null = Add-Box $Slide $x ($Top + ($rowIndex * $RowHeight)) $Widths[$columnIndex] $RowHeight $fill $C.Line 0 0.75
            $null = Add-TextBox $Slide ($x + 5) ($Top + ($rowIndex * $RowHeight) + 3) ($Widths[$columnIndex] - 10) ($RowHeight - 6) ([string]$Rows[$rowIndex][$columnIndex]) $FontSize $textColor -Bold:($rowIndex -eq 0) -VerticalAnchor 3
            $x += $Widths[$columnIndex]
        }
    }
}

$powerPoint = $null
$presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.Visible = $msoTrue
    $presentation = $powerPoint.Presentations.Add()
    $presentation.PageSetup.SlideWidth = 960
    $presentation.PageSetup.SlideHeight = 540

    # Slide 1: title
    $slide = New-DeckSlide $presentation
    $band = $slide.Shapes.AddShape($msoShapeRectangle, 0, 0, 22, 540)
    $band.Fill.ForeColor.RGB = $C.Navy
    $band.Line.Visible = $msoFalse
    $null = Add-Pill $slide 62 76 180 'POST VIDEO III | OCT 6' $C.BlueLight $C.Navy
    $null = Add-TextBox $slide 60 124 800 66 'FIXPROOF' 43 $C.Navy -Bold
    $null = Add-TextBox $slide 60 190 820 60 'Evidence that changed the review' 29 $C.Slate
    $null = Add-TextBox $slide 62 276 720 76 'A frozen primary study, later supplemental evidence, and bounded human decisions' 21 $C.Ink
    $null = Add-Box $slide 62 382 660 70 $C.White $C.Line 5 1.2
    $null = Add-TextBox $slide 80 397 625 42 'Python orchestrator | JavaScript/Express fixtures | XSS, SQLi, traversal' 15 $C.Navy -Bold -VerticalAnchor 3
    $null = Add-TextBox $slide 62 476 620 24 'Tony Tran | CS6727 Cyber Security Practicum | Fall 2026' 12 $C.Muted
    $null = Add-TextBox $slide 820 462 90 46 "VIDEO`nIII" 15 $C.Navy -Bold -Align 2 -VerticalAnchor 3
    Set-SpeakerNotes $slide @'
Opening: FixProof is an evidence-first workflow for evaluating AI-generated vulnerability repairs. This update focuses on evidence that changed later human review. The study uses three controlled Express fixtures, so the results support the workflow design rather than a production repair-success rate.
'@

    # Slide 2: research question and scope
    $slide = New-DeckSlide $presentation
    Add-Title $slide '1. Research question and bounded scope' 'What can this controlled benchmark establish - and what can it not establish?'
    $null = Add-Box $slide 42 116 560 116 $C.White $C.Blue 5 1.5
    $null = Add-TextBox $slide 60 132 525 24 'RESEARCH QUESTION' 11 $C.Blue -Bold
    $null = Add-TextBox $slide 60 160 520 56 'Can separately recorded static, runtime, behavioral, policy, and human evidence support a defensible patch decision?' 20 $C.Navy -Bold
    $null = Add-Box $slide 626 116 292 116 $C.GoldLight $C.Gold 5 1.5
    $null = Add-TextBox $slide 643 132 258 24 'CLAIM BOUNDARY' 11 $C.Gold -Bold
    $null = Add-TextBox $slide 643 162 258 52 'Workflow evidence - not a production success-rate estimate.' 17 $C.Navy -Bold

    $scope = @(
        @{ x = 42; title = 'Three fixtures'; body = "Reflected XSS`nSQL injection`nPath traversal"; fill = $C.BlueLight; accent = $C.Blue },
        @{ x = 338; title = 'Fixed generation'; body = "gpt-5.2`nPrompt v1.0`nNo model tools"; fill = $C.GoldLight; accent = $C.Gold },
        @{ x = 634; title = 'Separate authority'; body = "Model proposes`nValidators measure`nHuman decides"; fill = $C.PurpleLight; accent = $C.Purple }
    )
    foreach ($item in $scope) {
        $null = Add-Box $slide $item.x 266 284 178 $item.fill $item.accent 5 1.4
        $null = Add-TextBox $slide ($item.x + 18) 284 248 27 $item.title 17 $C.Navy -Bold
        $null = Add-TextBox $slide ($item.x + 18) 324 248 98 $item.body 16 $C.Ink -VerticalAnchor 3
    }
    $null = Add-TextBox $slide 50 468 858 26 'One fixture per CWE and repeated repairs support descriptive evidence, not population-level generalization.' 12.5 $C.Slate -Align 2
    Add-Footer $slide 2
    Set-SpeakerNotes $slide @'
FixProof asks whether separate evidence channels improve a patch decision. The benchmark is intentionally small: one XSS, one SQLi, and one traversal fixture, with five initial calls per fixture. The generator and prompt are fixed. This lets me preserve a complete evidence chain, but it does not represent production repositories or broad application diversity.
'@

    # Slide 3: workflow image
    $slide = New-DeckSlide $presentation
    $picture = $slide.Shapes.AddPicture($workflowImage, $msoFalse, $msoTrue, 0, 0, 960, 540)
    Set-SpeakerNotes $slide @'
Walk left to right through primary-v1: controlled fixtures, focused repair prompt, copied workspace, separate validators, deterministic policy, and human review for selected cases. Then point to supplemental-v1: the later protocol reused saved inputs and candidates, made no new model calls, and stored later qualifications without rewriting the primary record. The cases were predefined and frozen in the project's internal registry before candidate execution; do not imply an external public preregistration. Copied workspaces preserve study inputs; they are not security sandboxes.
'@

    # Slide 4: primary study
    $slide = New-DeckSlide $presentation
    Add-Title $slide '2. Frozen primary-v1 study' 'Five initial calls per CWE; complete all 15; do not stop early based on outcomes'
    Add-MetricCard $slide 42 108 196 '15' 'scheduled model calls' $C.BlueLight $C.Blue
    Add-MetricCard $slide 256 108 196 '5 / 15' 'target SAST resolved' $C.GoldLight $C.Gold
    Add-MetricCard $slide 470 108 196 '15 / 15' 'primary security suites' $C.GreenLight $C.Green
    Add-MetricCard $slide 684 108 234 '10 / 15' 'SAST/runtime disagreements' $C.PurpleLight $C.Purple
    $primaryRows = @(
        ,@('Primary case', 'Calls', 'SAST resolved', 'Security', 'Functional', 'Automated state')
        ,@('Reflected XSS', '5', '0 / 5', '5 / 5', '5 / 5', 'Needs adjudication')
        ,@('SQL injection', '5', '5 / 5', '5 / 5', '5 / 5', 'Ready for review')
        ,@('Path traversal', '5', '0 / 5', '5 / 5', '5 / 5', 'Needs adjudication')
        ,@('Total', '15', '5 / 15', '15 / 15', '15 / 15', '5 ready | 10 adjudicate')
    )
    Add-TableGrid $slide 42 222 @(155, 70, 120, 105, 105, 248) $primaryRows 39 11
    $null = Add-Box $slide 42 434 876 58 $C.GoldLight $C.Gold 5 1.2
    $null = Add-TextBox $slide 58 444 844 40 '0 / 5 resolved means the target scanner finding persisted - not that zero candidates blocked the tested attacks.' 14 $C.Navy -Bold -VerticalAnchor 3
    Add-Footer $slide 4
    Set-SpeakerNotes $slide @'
The primary protocol scheduled five calls for each fixture and required all 15. Every candidate passed its complete frozen primary security and functional suite. Only the five SQLi targets disappeared from SAST. XSS and traversal retained their findings while runtime checks passed, producing ten SAST/runtime disagreements and human adjudication. The pass columns count candidates, not individual test cases.
'@

    # Slide 5: supplemental study
    $slide = New-DeckSlide $presentation
    Add-Title $slide '3. Supplemental-v1: later, predefined evidence' 'Same saved candidates | baseline gates first | no new model calls | primary metrics stay frozen'
    Add-MetricCard $slide 42 108 196 '28' 'registered case definitions' $C.BlueLight $C.Blue
    Add-MetricCard $slide 256 108 196 '3' 'baseline characterizations' $C.GoldLight $C.Gold
    Add-MetricCard $slide 470 108 196 '15' 'saved primary candidates' $C.GreenLight $C.Green
    Add-MetricCard $slide 684 108 234 '140' 'candidate-case observations' $C.PurpleLight $C.Purple
    $suppRows = @(
        ,@('Category', 'Observations', 'Pass', 'Fail', 'Inconclusive', 'Interpretation')
        ,@('Security', '60', '55', '0', '5', 'Symlink unavailable')
        ,@('Behavioral parity', '45', '40', '5', '0', 'Observable changes')
        ,@('Robustness', '35', '25', '10', '0', 'New input contracts')
        ,@('Total', '140', '120', '15', '5', 'Mixed categories')
    )
    Add-TableGrid $slide 42 222 @(185, 110, 80, 70, 115, 223) $suppRows 39 11
    $null = Add-TextBox $slide 48 432 858 22 'Denominators: 12 security x 5 = 60  |  9 parity x 5 = 45  |  7 robustness x 5 = 35' 12 $C.Slate -Align 2
    $null = Add-Box $slide 210 462 540 38 $C.RedLight $C.Red 5 1.2
    $null = Add-TextBox $slide 226 469 508 24 'Do not pool these into one "security success rate."' 13.5 $C.Red -Bold -Align 2 -VerticalAnchor 3
    Add-Footer $slide 5
    Set-SpeakerNotes $slide @'
The supplement first characterized each vulnerable baseline, then applied the same relevant cases to the five saved candidates for that CWE. Its 140 observations are case-level outcomes, not 140 patches. Security, parity, and robustness answer different questions, so I report their denominators separately. Five traversal symlink observations remain inconclusive, not passed.
'@

    # Slide 6: backend demo handoff
    $slide = New-DeckSlide $presentation
    Add-Title $slide '4. Backend demo: follow one evidence chain' 'Show saved artifacts at high zoom; do not run a new model experiment'
    $steps = @(
        @{ n = '1'; title = 'Frozen plan'; detail = 'trial-plan.json -> 5 per CWE, 15 total, complete all' },
        @{ n = '2'; title = 'Primary result'; detail = 'primary dashboard/report -> persistent SAST + passing runtime' },
        @{ n = '3'; title = 'Candidate patches'; detail = 'XSS 03 String(value) vs XSS 04 String(value ?? "")' },
        @{ n = '4'; title = 'Registered result'; detail = 'XSS-P01 -> Hello undefined (pass) vs Hello [blank] (fail)' },
        @{ n = '5'; title = 'Human record'; detail = 'XSS 04 -> FOLLOW_UP_REJECT_CANDIDATE' }
    )
    $y = 112
    foreach ($step in $steps) {
        $circle = $slide.Shapes.AddShape($msoShapeOval, 48, $y, 34, 34)
        $circle.Fill.ForeColor.RGB = $C.Navy
        $circle.Line.Visible = $msoFalse
        $null = Add-TextBox $slide 48 ($y + 1) 34 30 $step.n 14 $C.White -Bold -Align 2 -VerticalAnchor 3
        $null = Add-TextBox $slide 96 ($y - 2) 180 24 $step.title 15 $C.Navy -Bold
        $null = Add-TextBox $slide 276 ($y - 2) 370 36 $step.detail 12.5 $C.Ink
        if ($step.n -ne '5') {
            $line = $slide.Shapes.AddLine(65, ($y + 35), 65, ($y + 54))
            $line.Line.ForeColor.RGB = $C.Line
            $line.Line.Weight = 2
        }
        $y += 68
    }
    $null = Add-Box $slide 670 112 248 338 $C.White $C.Line 5 1.2
    $null = Add-TextBox $slide 688 128 212 24 'OPEN BEFORE RECORDING' 11 $C.Blue -Bold
    $paths = @'
data/evaluation/
  trial-plan.json

ui/primary.html

XSS attempt-03/
  candidate.patch
  result.json

XSS attempt-04/
  candidate.patch
  result.json
  follow-up result.json
'@
    $null = Add-TextBox $slide 688 160 212 248 $paths 11 $C.Ink -FontName 'Consolas'
    $null = Add-Box $slide 42 466 876 38 $C.BlueLight $C.Blue 5 1.0
    $null = Add-TextBox $slide 56 473 850 24 'Label the dashboard and JSON as saved evidence. Verification checks bindings; it does not replay historical model calls.' 12.5 $C.Navy -Bold -Align 2 -VerticalAnchor 3
    Add-Footer $slide 6
    Set-SpeakerNotes $slide @'
Switch from slides to the backend. First show the frozen trial plan fields. Then show the primary dashboard or primary report for XSS 03 and 04. Open the two candidate patches side by side and highlight only String(value) versus String(value ?? ""). Finally, show XSS-P01 in the two saved supplemental result files and the later XSS 04 follow-up verdict. Keep each file on screen only long enough to point to the relevant lines.
'@

    # Slide 7: XSS comparison summary
    $slide = New-DeckSlide $presentation
    Add-Title $slide '5. XSS 03 versus XSS 04' 'Both passed the registered attacks; one changed missing-input behavior'
    $null = Add-Box $slide 42 112 414 326 $C.GreenLight $C.Green 5 1.5
    $null = Add-Pill $slide 60 128 94 'XSS 03' $C.Green $C.White
    $null = Add-TextBox $slide 60 166 376 20 'PATCH' 10.5 $C.Green -Bold
    $null = Add-Box $slide 60 190 376 60 $C.White $C.Line 3 1.0
    $null = Add-TextBox $slide 74 205 348 30 'String(value)' 20 $C.Navy -Bold -FontName 'Consolas' -VerticalAnchor 3
    $null = Add-TextBox $slide 60 270 376 20 'SAVED XSS-P01 OBSERVATION' 10.5 $C.Green -Bold
    $null = Add-Box $slide 60 294 376 76 $C.White $C.Line 3 1.0
    $null = Add-TextBox $slide 74 304 348 52 "`"body`": `"<h1>Hello undefined</h1>`"`n`"status`": `"pass`"" 12.5 $C.Ink -FontName 'Consolas'
    $null = Add-TextBox $slide 60 390 376 30 'Supplement: 9 pass | 0 fail | parity 5/5' 13 $C.Navy -Bold -Align 2

    $null = Add-Box $slide 504 112 414 326 $C.RedLight $C.Red 5 1.5
    $null = Add-Pill $slide 522 128 94 'XSS 04' $C.Red $C.White
    $null = Add-TextBox $slide 522 166 376 20 'PATCH' 10.5 $C.Red -Bold
    $null = Add-Box $slide 522 190 376 60 $C.White $C.Line 3 1.0
    $null = Add-TextBox $slide 536 205 348 30 'String(value ?? "")' 20 $C.Navy -Bold -FontName 'Consolas' -VerticalAnchor 3
    $null = Add-TextBox $slide 522 270 376 20 'SAVED XSS-P01 OBSERVATION' 10.5 $C.Red -Bold
    $null = Add-Box $slide 522 294 376 76 $C.White $C.Line 3 1.0
    $null = Add-TextBox $slide 536 304 348 52 "`"body`": `"<h1>Hello </h1>`"`n`"status`": `"fail`"" 12.5 $C.Ink -FontName 'Consolas'
    $null = Add-TextBox $slide 522 390 376 30 'Supplement: 8 pass | 1 fail | parity 4/5' 13 $C.Navy -Bold -Align 2

    $null = Add-Box $slide 120 456 720 44 $C.PurpleLight $C.Purple 5 1.2
    $null = Add-TextBox $slide 138 463 684 28 'Both security: 3/3 pass. XSS 04 follow-up: reject for parity - not because XSS remained exploitable.' 13.5 $C.Navy -Bold -Align 2 -VerticalAnchor 3
    Add-Footer $slide 7
    Set-SpeakerNotes $slide @'
This is the central comparison. Both candidates encode HTML and pass all three supplemental XSS security cases. XSS 03 uses String(value), so an omitted name remains the text undefined and passes all five parity cases. XSS 04 uses nullish coalescing to replace a missing name with an empty string, so XSS-P01 fails exact parity. The later rejection is bounded to the frozen parity criterion; it does not mean the registered XSS attacks still worked.
'@

    # Slide 8: interpretation and close
    $slide = New-DeckSlide $presentation
    Add-Title $slide '6. Human judgment, limits, and next steps' 'Later records qualify the evidence; they never overwrite primary-v1'
    Add-MetricCard $slide 42 108 264 '10 original reviews' '7 accept | 3 request more testing' $C.BlueLight $C.Blue
    Add-MetricCard $slide 348 108 264 '14 later records' '5 reject | 5 bounded accept | 4 request' $C.PurpleLight $C.Purple
    Add-MetricCard $slide 654 108 264 '0 overwritten' 'primary records and metrics stay frozen' $C.GreenLight $C.Green

    $null = Add-Box $slide 42 222 422 188 $C.White $C.Line 5 1.2
    $null = Add-TextBox $slide 60 238 386 24 'LIMITS TO SAY OUT LOUD' 11 $C.Red -Bold
    $limits = @'
- One application per CWE
- 15 calls are not 15 unique patches; SQLi has one source
- PATH-S06 remains inconclusive on Windows
- SQLi target comparison used a labeled controlled rule
- No production-readiness or broad success-rate claim
'@
    $null = Add-TextBox $slide 60 270 386 126 $limits 13 $C.Ink

    $null = Add-Box $slide 496 222 422 188 $C.White $C.Line 5 1.2
    $null = Add-TextBox $slide 514 238 386 24 'NEXT COURSE MILESTONES' 11 $C.Blue -Bold
    $next = @'
- Planned early Report 3 submission: October 1
- Official Report 3 deadline: October 4, 11:59 p.m.
- Post Video III: October 6
- Peer Feedback Report 3: October 11, 11:59 p.m.
- Continue related work and clean-package rehearsal
'@
    $null = Add-TextBox $slide 514 270 386 126 $next 13 $C.Ink

    $null = Add-Box $slide 88 438 784 62 $C.GoldLight $C.Gold 5 1.4
    $null = Add-TextBox $slide 108 447 744 42 'Feedback: Would a second reviewer improve confidence more than adding another CWE - or should I prioritize a symlink-capable rerun?' 14 $C.Navy -Bold -Align 2 -VerticalAnchor 3
    Add-Footer $slide 8
    Set-SpeakerNotes $slide @'
The original ten reviews and the later fourteen records are separate evidence layers. The later decisions include five rejections, five bounded SQLi acceptances, and four traversal requests for more testing. End by stating the limits explicitly and asking one focused design question. Mention that Progress Report 3 is due October 4, Video III posts October 6, and peer feedback is due October 11. Close with the course AI-use disclosure: Codex and ChatGPT assisted implementation, analysis, and presentation preparation; separate saved OpenAI API calls proposed experimental repairs; I made the recorded human decisions and remain responsible for the claims.
'@

    # Slide 9: optional backup
    $slide = New-DeckSlide $presentation
    Add-Title $slide 'BACKUP | If asked about SQLi or traversal' 'Skip during the main recording unless the course format allows extra detail'
    $null = Add-Box $slide 42 116 420 334 $C.BlueLight $C.Blue 5 1.5
    $null = Add-Pill $slide 60 132 160 'SQLi 01-05' $C.Blue $C.White
    $sql = @'
Primary target SAST: 5/5 resolved
Primary security + functional: 5/5 candidates pass

Supplement per candidate:
- Security 3/3
- Parity 2/2
- Robustness 2/3

SQL-R01: repeated usernames returned HTTP 200 [] instead of registered HTTP 400.

Human result: bounded accept; failure remains recorded.
'@
    $null = Add-TextBox $slide 60 174 384 246 $sql 13 $C.Ink

    $null = Add-Box $slide 498 116 420 334 $C.GoldLight $C.Gold 5 1.5
    $null = Add-Pill $slide 516 132 186 'Traversal 02-05' $C.Gold $C.White
    $path = @'
Primary target SAST: 0/5 resolved
Primary security + functional: 5/5 candidates pass

Supplement:
- Five executable security cases pass per candidate
- PATH-S06 symlink case remains inconclusive
- Traversal 03 fails R01-R03
- Traversal 05 fails R03

Human result: request more testing; no symlink-safety claim.
'@
    $null = Add-TextBox $slide 516 174 384 246 $path 13 $C.Ink
    $null = Add-Box $slide 145 470 670 34 $C.White $C.Line 5 1.0
    $null = Add-TextBox $slide 160 476 640 22 'Full matrices and rationales: Video-III-15-candidate-evidence-appendix.pdf' 11.5 $C.Navy -Bold -Align 2
    Add-Footer $slide 9 'BACKUP | CS6727 | FixProof Video III'
    Set-SpeakerNotes $slide @'
Backup only. Use this slide if someone asks why SQLi was accepted despite SQL-R01 or why traversal requests more testing. Keep security, parity, and robustness interpretations separate. SQL-R01 is a low-impact robustness failure under Tony's bounded criterion. PATH-S06 is inconclusive and prevents a complete symlink-safety claim.
'@

    if ((Test-Path -LiteralPath $target) -and $Overwrite) {
        Remove-Item -LiteralPath $target -Force
    }
    if ((Test-Path -LiteralPath $pdfPath) -and $Overwrite) {
        Remove-Item -LiteralPath $pdfPath -Force
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
        try { $powerPoint.Quit() } catch { }
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint)
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($target)
try {
    $badEntry = $archive.Entries | Where-Object { $_.Length -lt 0 } | Select-Object -First 1
    if ($badEntry) { throw "Invalid PPTX entry: $($badEntry.FullName)" }
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
    output = $target
    pdf = $pdfPath
    rendered_slides = $renderDirectory
    slides = $slideCount
    speaker_notes = $notesCount
    pptx_bytes = (Get-Item -LiteralPath $target).Length
    pdf_bytes = (Get-Item -LiteralPath $pdfPath).Length
    pptx_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    package_structure = 'pass'
    evidence_scope = 'saved primary and supplemental artifacts; no new model calls'
}
$verificationPath = Join-Path $outputDirectory 'Video-III-deck-verification.json'
$verification | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $verificationPath -Encoding utf8

Write-Output "Created: $target"
Write-Output "Created: $pdfPath"
Write-Output "Rendered slides: $renderDirectory"
Write-Output "Verification: $verificationPath"
