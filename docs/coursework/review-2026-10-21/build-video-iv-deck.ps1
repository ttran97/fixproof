[CmdletBinding()]
param(
    [string]$OutputPath = 'docs\coursework\review-2026-10-21\FixProof - Video IV - PATH-S06 Recording Deck.pptx',
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
trap {
    $detail = 'Deck generation failed at line {0}: {1}' -f `
        $_.InvocationInfo.ScriptLineNumber, $_.Exception.Message
    Write-Error $detail
    exit 1
}
$projectRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $projectRoot) {
    throw 'Run this script from inside the FixProof repository.'
}

function Resolve-ProjectPath {
    param([string]$Path)
    if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
    return [IO.Path]::GetFullPath((Join-Path $projectRoot $Path))
}

$target = Resolve-ProjectPath $OutputPath
$allowedRoot = Resolve-ProjectPath 'docs\coursework\review-2026-10-21'
$pdfPath = [IO.Path]::ChangeExtension($target, '.pdf')
$renderDirectory = Join-Path $allowedRoot 'video-iv-rendered-slides'
$contactSheet = Join-Path $allowedRoot 'Video-IV-contact-sheet.png'
$verificationPath = Join-Path $allowedRoot 'Video-IV-deck-verification.json'

if (-not $target.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay inside docs/coursework/review-2026-10-21.'
}
if ((Test-Path -LiteralPath $target) -and -not $Overwrite) {
    throw "Output already exists; use -Overwrite to replace it: $target"
}

foreach ($path in @($target, $pdfPath, $contactSheet, $verificationPath)) {
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
}
if (Test-Path -LiteralPath $renderDirectory) {
    Remove-Item -LiteralPath $renderDirectory -Recurse -Force
}
[IO.Directory]::CreateDirectory($renderDirectory) | Out-Null

$msoFalse = 0
$msoTrue = -1
$ppLayoutBlank = 12
$ppSaveAsOpenXMLPresentation = 24
$ppSaveAsPDF = 32
$msoTextOrientationHorizontal = 1
$msoShapeRectangle = 1
$msoShapeRoundedRectangle = 5
$msoShapeOval = 9
$msoArrowheadTriangle = 3
$msoLineDash = 4

function RGB {
    param([int]$R, [int]$G, [int]$B)
    return $R + (256 * $G) + (65536 * $B)
}

$navy = RGB 16 38 70
$blue = RGB 73 111 168
$blueDark = RGB 42 73 116
$blueLight = RGB 232 240 250
$orange = RGB 224 150 48
$orangeLight = RGB 255 244 224
$purple = RGB 117 93 155
$purpleLight = RGB 242 237 250
$green = RGB 61 137 116
$greenLight = RGB 230 245 240
$red = RGB 176 62 62
$redLight = RGB 252 235 235
$ink = RGB 25 45 75
$muted = RGB 84 105 135
$line = RGB 190 207 228
$paper = RGB 247 249 252
$white = RGB 255 255 255
$codeBg = RGB 25 33 48
$codeText = RGB 222 235 249

function Set-SlideBackground {
    param($Slide, [int]$Color)
    $Slide.FollowMasterBackground = $msoFalse
    $Slide.Background.Fill.Solid()
    $Slide.Background.Fill.ForeColor.RGB = $Color
}

function Add-Text {
    param(
        $Slide,
        [string]$Text,
        [float]$X,
        [float]$Y,
        [float]$W,
        [float]$H,
        [float]$Size = 18,
        [int]$Color = $ink,
        [bool]$Bold = $false,
        [string]$Font = 'Aptos',
        [int]$Align = 1,
        [int]$Vertical = 1
    )
    $shape = $Slide.Shapes.AddTextbox($msoTextOrientationHorizontal, $X, $Y, $W, $H)
    $shape.TextFrame.MarginLeft = 0
    $shape.TextFrame.MarginRight = 0
    $shape.TextFrame.MarginTop = 0
    $shape.TextFrame.MarginBottom = 0
    $shape.TextFrame.WordWrap = $msoTrue
    $shape.TextFrame.AutoSize = 0
    $range = $shape.TextFrame.TextRange
    $range.Text = $Text
    $range.Font.Name = $Font
    $range.Font.Size = $Size
    $range.Font.Bold = $(if ($Bold) { $msoTrue } else { $msoFalse })
    $range.Font.Color.RGB = $Color
    $range.ParagraphFormat.Alignment = $Align
    return $shape
}

function Add-Box {
    param(
        $Slide,
        [float]$X,
        [float]$Y,
        [float]$W,
        [float]$H,
        [int]$Fill,
        [int]$Stroke = $line,
        [float]$Radius = 1.0
    )
    $shapeType = $(if ($Radius -gt 0) { $msoShapeRoundedRectangle } else { $msoShapeRectangle })
    $shape = $Slide.Shapes.AddShape($shapeType, $X, $Y, $W, $H)
    $shape.Fill.Solid()
    $shape.Fill.ForeColor.RGB = $Fill
    $shape.Line.ForeColor.RGB = $Stroke
    $shape.Line.Weight = 1.2
    return $shape
}

function Add-Line {
    param(
        $Slide,
        [float]$X1,
        [float]$Y1,
        [float]$X2,
        [float]$Y2,
        [int]$Color = $blueDark,
        [float]$Weight = 2.0,
        [bool]$Arrow = $false,
        [bool]$Dashed = $false
    )
    $shape = $Slide.Shapes.AddLine($X1, $Y1, $X2, $Y2)
    $shape.Line.ForeColor.RGB = $Color
    $shape.Line.Weight = $Weight
    if ($Arrow) { $shape.Line.EndArrowheadStyle = $msoArrowheadTriangle }
    if ($Dashed) { $shape.Line.DashStyle = $msoLineDash }
    return $shape
}

function Add-Pill {
    param($Slide, [string]$Text, [float]$X, [float]$Y, [float]$W, [int]$Fill, [int]$TextColor)
    $null = Add-Box $Slide $X $Y $W 30 $Fill $Fill 1
    $null = Add-Text $Slide $Text $X ($Y + 4) $W 22 13 $TextColor $true 'Aptos' 2 3
}

function Add-Header {
    param($Slide, [string]$Title, [string]$Kicker, [int]$SlideNumber)
    $null = Add-Text $Slide $Kicker 48 24 720 22 12 $blue $true
    $null = Add-Text $Slide $Title 48 48 850 48 27 $navy $true
    $null = Add-Line $Slide 48 105 912 105 $line 1 $false $false
    $null = Add-Text $Slide 'CS6727 | FixProof Video IV' 48 510 300 16 10 $muted $false
    $null = Add-Text $Slide ([string]$SlideNumber) 885 510 27 16 10 $muted $false 'Aptos' 3
}

function Add-CheckItem {
    param(
        $Slide,
        [string]$Text,
        [float]$X,
        [float]$Y,
        [float]$W,
        [int]$Accent = $green,
        [int]$TextColor = $ink
    )
    $circle = $Slide.Shapes.AddShape($msoShapeOval, $X, ($Y + 1), 22, 22)
    $circle.Fill.Solid()
    $circle.Fill.ForeColor.RGB = $Accent
    $circle.Line.Visible = $msoFalse
    $null = Add-Text $Slide 'OK' ($X + 2) ($Y + 6) 18 12 7 $white $true 'Arial' 2 3
    $null = Add-Text $Slide $Text ($X + 32) $Y ($W - 32) 38 15 $TextColor $false
}

function Add-Notes {
    param($Slide, [string]$Notes)
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
    $powerPoint.Visible = $msoTrue
    $presentation = $powerPoint.Presentations.Add()
    $presentation.PageSetup.SlideWidth = 960
    $presentation.PageSetup.SlideHeight = 540

    # Slide 1 - Title
    $slide = $presentation.Slides.Add(1, $ppLayoutBlank)
    Set-SlideBackground $slide $navy
    $null = Add-Pill $slide 'POST VIDEO IV' 58 52 144 $orange $navy
    $null = Add-Text $slide 'FIXPROOF' 58 112 310 58 38 $white $true
    $null = Add-Text $slide 'Resolving a recorded path-traversal uncertainty' 58 176 760 82 31 $white $true
    $null = Add-Text $slide 'PATH-S06 symbolic-link extension | Evidence preserved across study layers' 58 270 790 30 17 (RGB 190 210 235) $false
    $null = Add-Pill $slide '1 REGISTERED CASE' 58 350 190 $blue $white
    $null = Add-Pill $slide '5 SAVED CANDIDATES' 264 350 210 $purple $white
    $null = Add-Pill $slide '0 OF 5 PASSED' 490 350 170 $red $white
    $null = Add-Text $slide 'Tony Tran | CS6727 Cyber Security Practicum | October 2026' 58 492 700 18 11 (RGB 180 202 230) $false
    $null = Add-Text $slide '1' 885 492 27 18 11 (RGB 180 202 230) $false 'Aptos' 3
    Add-Notes $slide @'
Hi everyone. Since Video III, I focused on the unresolved PATH-S06 symbolic-link case. It could not run in Windows, so FixProof recorded it as inconclusive. I later evaluated it through a separately registered WSL2 extension.
'@

    # Slide 2 - Why the original result was inconclusive
    $slide = $presentation.Slides.Add(2, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Why the original result was inconclusive' '1. THE EVIDENCE GAP' 2
    $null = Add-Box $slide 48 132 260 126 $greenLight $green 1
    $null = Add-Text $slide 'DIRECT TRAVERSAL' 68 150 220 20 12 $green $true
    $null = Add-Text $slide '../../outside-zone/outside-secret.txt' 68 180 220 38 15 $ink $true 'Consolas'
    $null = Add-Text $slide 'HTTP 400 - desired rejection' 68 226 220 22 14 $green $true

    $null = Add-Box $slide 336 132 260 126 $redLight $red 1
    $null = Add-Text $slide 'SYMBOLIC-LINK TRAVERSAL' 356 150 220 20 12 $red $true
    $null = Add-Text $slide 'link/outside-secret.txt' 356 180 220 24 15 $ink $true 'Consolas'
    $null = Add-Text $slide 'Needed a link-capable environment' 356 218 220 36 14 $red $true

    $null = Add-Box $slide 624 132 288 126 $orangeLight $orange 1
    $null = Add-Text $slide 'ORIGINAL OUTCOME' 644 150 248 20 12 $orange $true
    $null = Add-Text $slide 'PATH-S06' 644 181 248 24 18 $navy $true
    $null = Add-Text $slide 'INCONCLUSIVE' 644 207 248 24 18 $navy $true
    $null = Add-Text $slide 'Windows could not create the registered fixture; it was not counted as pass.' 644 233 248 26 11 $muted $false

    $null = Add-Box $slide 72 304 530 150 $white $line 1
    $null = Add-Text $slide 'Allowed root: public-files/' 92 324 280 22 15 $navy $true 'Consolas'
    $null = Add-Box $slide 96 360 160 54 $blueLight $blue 1
    $null = Add-Text $slide 'link' 96 375 160 20 16 $blueDark $true 'Consolas' 2
    $null = Add-Line $slide 256 387 410 387 $red 3 $true $true
    $null = Add-Box $slide 410 350 166 76 $redLight $red 1
    $null = Add-Text $slide 'outside-zone/' 424 364 140 20 14 $red $true 'Consolas' 2
    $null = Add-Text $slide 'outside-secret.txt' 424 391 140 20 12 $ink $false 'Consolas' 2
    $null = Add-Text $slide 'An in-root name can still resolve to an outside filesystem target.' 632 330 250 70 22 $navy $true
    $null = Add-Text $slide 'A lexical path check and a resolved-target check answer different questions.' 632 414 250 42 14 $muted $false
    Add-Notes $slide @'
Traversal 02 returned HTTP 400 for a direct parent-directory request, which is the desired rejection. But that lexical check does not prove the final filesystem target stays inside the allowed directory. An in-root symbolic link can point outside. Windows could not create that fixture, so the original result remained inconclusive rather than passing.
'@

    # Slide 3 - Frozen extension design
    $slide = $presentation.Slides.Add(3, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Frozen before execution' '2. PATH-S06 EXTENSION DESIGN' 3
    $steps = @(
        @{x=48; title='1. Register'; text='One case, payload, oracle, environment'; fill=$blueLight; stroke=$blue},
        @{x=270; title='2. Gate'; text='Baseline must disclose the controlled marker'; fill=$orangeLight; stroke=$orange},
        @{x=492; title='3. Evaluate'; text='Reuse five saved traversal candidates'; fill=$purpleLight; stroke=$purple},
        @{x=714; title='4. Qualify'; text='Record later human decisions separately'; fill=$greenLight; stroke=$green}
    )
    foreach ($step in $steps) {
        $null = Add-Box $slide $step.x 136 198 102 $step.fill $step.stroke 1
        $null = Add-Text $slide $step.title ($step.x + 16) 151 166 22 16 $navy $true
        $null = Add-Text $slide $step.text ($step.x + 16) 181 166 48 13 $muted $false
    }
    $null = Add-Line $slide 246 187 270 187 $blueDark 2 $true $false
    $null = Add-Line $slide 468 187 492 187 $blueDark 2 $true $false
    $null = Add-Line $slide 690 187 714 187 $blueDark 2 $true $false

    $null = Add-Box $slide 48 278 410 182 $white $line 1
    $null = Add-Text $slide 'REGISTERED ORACLE' 68 298 360 20 12 $blue $true
    $null = Add-Text $slide 'Environment' 68 333 116 20 14 $muted $true
    $null = Add-Text $slide 'WSL2 Ubuntu; Linux-native symlink' 190 333 238 20 14 $ink $false
    $null = Add-Text $slide 'Candidate pass' 68 367 116 20 14 $muted $true
    $null = Add-Text $slide 'Marker absent AND HTTP 400, 403, or 404' 190 367 238 38 14 $green $true
    $null = Add-Text $slide 'Candidate fail' 68 416 116 20 14 $muted $true
    $null = Add-Text $slide 'Controlled outside marker disclosed' 190 416 238 24 14 $red $true

    $null = Add-Box $slide 482 278 430 182 $navy $navy 1
    $null = Add-Text $slide 'BOUNDARY CONDITIONS' 504 298 386 20 12 (RGB 146 180 224) $true
    Add-CheckItem $slide 'No new model calls' 504 334 365 $green $white
    Add-CheckItem $slide 'No SAST reruns' 504 370 365 $green $white
    Add-CheckItem $slide 'Disposable candidate copies' 504 406 365 $green $white
    $null = Add-Text $slide 'Primary-v1 and supplemental-v1 fingerprints remained unchanged.' 504 442 365 26 13 (RGB 205 219 239) $false
    Add-Notes $slide @'
Before execution, I documented the case, payload, environment, and oracle. The baseline first had to disclose the controlled marker. A candidate passed only if the marker was absent and the response was 400, 403, or 404. I reused the five saved candidates with no new model calls or SAST reruns.
'@

    # Slide 4 - Results
    $slide = $presentation.Slides.Add(4, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'All five saved candidates disclosed the marker' '3. MEASURED RESULT' 4
    $null = Add-Box $slide 48 132 232 330 $navy $navy 1
    $null = Add-Text $slide '0 / 5' 66 170 196 76 50 $white $true 'Aptos Display' 2 3
    $null = Add-Text $slide 'candidates passed' 66 247 196 28 18 (RGB 202 218 239) $true 'Aptos' 2
    $null = Add-Line $slide 78 300 250 300 (RGB 95 127 169) 1 $false $false
    $null = Add-Text $slide 'Every candidate returned HTTP 200 and the exact controlled outside-file marker.' 72 326 184 92 17 $white $false 'Aptos' 2 2
    $null = Add-Text $slide 'Baseline gate is not part of the 5-candidate denominator.' 72 426 184 28 11 (RGB 174 198 228) $false 'Aptos' 2

    $tableX = 310
    $col = @(190, 105, 135, 130)
    $headers = @('Target', 'HTTP', 'Marker', 'Outcome')
    $x = $tableX
    for ($i=0; $i -lt 4; $i++) {
        $null = Add-Box $slide $x 132 $col[$i] 38 $blueDark $blueDark 0
        $null = Add-Text $slide $headers[$i] ($x + 8) 142 ($col[$i] - 16) 18 13 $white $true $(if ($i -eq 0) {'Aptos'} else {'Aptos'}) $(if ($i -eq 0) {1} else {2}) 3
        $x += $col[$i]
    }
    $rows = @(
        @('Vulnerable baseline','200','Disclosed','Gate passed'),
        @('Traversal 01','200','Disclosed','FAIL'),
        @('Traversal 02','200','Disclosed','FAIL'),
        @('Traversal 03','200','Disclosed','FAIL'),
        @('Traversal 04','200','Disclosed','FAIL'),
        @('Traversal 05','200','Disclosed','FAIL')
    )
    for ($r=0; $r -lt $rows.Count; $r++) {
        $y = 170 + ($r * 48)
        $rowFill = $(if ($r -eq 0) { $orangeLight } elseif (($r % 2) -eq 0) { $paper } else { $white })
        $x = $tableX
        for ($c=0; $c -lt 4; $c++) {
            $null = Add-Box $slide $x $y $col[$c] 48 $rowFill $line 0
            $color = $(if ($r -eq 0 -and $c -eq 3) { $orange } elseif ($r -gt 0 -and $c -eq 3) { $red } else { $ink })
            $bold = ($c -eq 0 -or $c -eq 3)
            $null = Add-Text $slide $rows[$r][$c] ($x + 8) ($y + 14) ($col[$c] - 16) 20 13 $color $bold 'Aptos' $(if ($c -eq 0) {1} else {2}) 3
            $x += $col[$c]
        }
    }
    Add-Notes $slide @'
The baseline gate passed. All five candidates then returned HTTP 200 and the controlled outside-file marker. Under the frozen criterion, the result was zero pass, five fail, and zero inconclusive. The baseline is a control and is not part of the five-candidate denominator.
'@

    # Slide 5 - Traversal 02 example
    $slide = $presentation.Slides.Add(5, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Traversal 02: one traceable evidence chain' '4. FOCUSED WALKTHROUGH' 5
    $cards = @(
        @{x=48; tag='NORMAL FILE'; input='welcome.txt'; status='HTTP 200'; detail='Expected public content'; fill=$greenLight; stroke=$green; result='PASS'},
        @{x=342; tag='DIRECT TRAVERSAL'; input='../../outside-zone/...'; status='HTTP 400'; detail='Rejected as intended'; fill=$greenLight; stroke=$green; result='PASS'},
        @{x=636; tag='SYMLINK PATH'; input='link/outside-secret.txt'; status='HTTP 200'; detail='Controlled marker disclosed'; fill=$redLight; stroke=$red; result='FAIL'}
    )
    foreach ($card in $cards) {
        $null = Add-Box $slide $card.x 132 276 160 $card.fill $card.stroke 1
        $null = Add-Text $slide $card.tag ($card.x + 18) 149 240 20 11 $card.stroke $true
        $null = Add-Text $slide $card.input ($card.x + 18) 180 240 38 14 $ink $true 'Consolas'
        $null = Add-Text $slide $card.status ($card.x + 18) 227 110 24 18 $navy $true
        $null = Add-Pill $slide $card.result ($card.x + 162) 222 92 $card.stroke $white
        $null = Add-Text $slide $card.detail ($card.x + 18) 264 240 20 13 $muted $false
    }
    $null = Add-Box $slide 48 324 864 150 $codeBg $codeBg 1
    $null = Add-Text $slide 'WHY THE THIRD REQUEST FAILED' 68 344 824 20 12 (RGB 137 178 226) $true
    $null = Add-Text $slide @'
Request:  /file?name=link%2Foutside-secret.txt
Observed: HTTP 200  |  FIXPROOF_CONTROLLED_TRAVERSAL_SECRET
'@ 68 377 505 58 16 $codeText $false 'Consolas'
    $null = Add-Line $slide 596 368 596 448 (RGB 87 107 135) 1 $false $false
    $null = Add-Text $slide 'The candidate checked the path text under the allowed root. fs.readFile then followed link to an outside filesystem target.' 620 374 260 66 15 $white $false
    $null = Add-Text $slide 'Manual WSL2 spot-check: Traversal 02 only' 620 445 260 18 11 (RGB 167 195 228) $true
    Add-Notes $slide @'
Here is the Traversal 02 evidence chain. A normal file returned HTTP 200 with the expected content. The direct traversal returned HTTP 400, as intended. But the symbolic-link request returned HTTP 200 with FIXPROOF_CONTROLLED_TRAVERSAL_SECRET. The candidate checked the lexical path, then fs.readFile followed the link to an outside filesystem target. I also manually reproduced this candidate in WSL2.
'@

    # Slide 6 - Preservation
    $slide = $presentation.Slides.Add(6, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Later evidence qualified the conclusion - not the history' '5. PRESERVED STUDY LAYERS' 6
    $timelineY = 196
    $null = Add-Line $slide 140 $timelineY 820 $timelineY $blueDark 3 $false $false
    $nodes = @(
        @{x=140; n='1'; title='PRIMARY-v1'; sub='15 initial attempts'; body='Traversal runtime suites passed; five cases routed to adjudication.'; fill=$blueLight; stroke=$blue},
        @{x=480; n='2'; title='SUPPLEMENTAL-v1'; sub='140 observations'; body='PATH-S06 remained inconclusive on Windows. That result stays frozen.'; fill=$orangeLight; stroke=$orange},
        @{x=820; n='3'; title='PATH-S06 EXTENSION'; sub='5 separate outcomes'; body='Five registered failures; five later rejection qualifications.'; fill=$purpleLight; stroke=$purple}
    )
    foreach ($node in $nodes) {
        $circle = $slide.Shapes.AddShape($msoShapeOval, ($node.x - 22), ($timelineY - 22), 44, 44)
        $circle.Fill.Solid(); $circle.Fill.ForeColor.RGB = $node.stroke
        $circle.Line.Visible = $msoFalse
        $null = Add-Text $slide $node.n ($node.x - 12) ($timelineY - 13) 24 24 15 $white $true 'Aptos' 2 3
        $null = Add-Box $slide ($node.x - 125) 238 250 142 $node.fill $node.stroke 1
        $null = Add-Text $slide $node.title ($node.x - 105) 254 210 20 13 $node.stroke $true
        $null = Add-Text $slide $node.sub ($node.x - 105) 282 210 22 17 $navy $true
        $null = Add-Text $slide $node.body ($node.x - 105) 315 210 56 13 $muted $false
    }
    $null = Add-Box $slide 115 414 730 58 $white $line 1
    $null = Add-Text $slide 'UNCHANGED' 136 432 90 20 12 $blue $true
    $null = Add-Text $slide 'Original primary reviews, supplemental outcomes, and denominators.' 232 429 285 28 14 $ink $false
    $null = Add-Text $slide 'NEW' 545 432 46 20 12 $purple $true
    $null = Add-Text $slide 'Later evidence and human qualifications.' 597 429 228 28 14 $ink $false
    Add-Notes $slide @'
This evidence qualifies the conclusion without rewriting the study. Primary-v1 keeps its 15 attempts and reviews. Supplemental-v1 keeps its 140 observations, including five Windows-inconclusive PATH-S06 cases. The extension separately records five failures and five later human rejection qualifications.
'@

    # Slide 7 - Interpretation and next steps
    $slide = $presentation.Slides.Add(7, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Bounded finding, clear next steps' '6. INTERPRETATION AND COURSE DIRECTION' 7
    $null = Add-Box $slide 48 132 410 224 $greenLight $green 1
    $null = Add-Text $slide 'WHAT THIS ESTABLISHES' 68 151 370 20 12 $green $true
    Add-CheckItem $slide 'All five saved candidates fail registered PATH-S06.' 68 190 355 $green
    Add-CheckItem $slide 'Blocking ../ does not establish symlink-target containment.' 68 238 355 $green
    Add-CheckItem $slide 'Later evidence can qualify decisions without rewriting prior results.' 68 286 355 $green

    $null = Add-Box $slide 482 132 430 224 $orangeLight $orange 1
    $null = Add-Text $slide 'WHAT IT DOES NOT ESTABLISH' 502 151 390 20 12 $orange $true
    $null = Add-Text $slide 'Application-wide path-traversal security' 502 193 370 24 15 $ink $true
    $null = Add-Text $slide 'A production repair-success rate' 502 237 370 24 15 $ink $true
    $null = Add-Text $slide 'Generalization beyond three controlled Express fixtures' 502 281 370 44 15 $ink $true

    $null = Add-Box $slide 48 382 864 92 $navy $navy 1
    $null = Add-Text $slide 'NEXT' 68 402 68 20 12 (RGB 146 180 224) $true
    $null = Add-Text $slide 'Reconcile peer feedback | clean-package reproduction | refresh active docs and public evidence | finalize report and presentation' 142 398 730 44 16 $white $true
    $null = Add-Text $slide 'Feedback: What adds more confidence - independent reproduction or one more controlled fixture? What evidence would you expect?' 142 447 730 22 12 (RGB 190 210 235) $false
    Add-Notes $slide @'
Within this registered case, all five saved candidates remain vulnerable to the symbolic-link escape. This does not establish application-wide security or a production repair-success rate. My next priorities are peer-feedback reconciliation, clean-package reproduction, current documentation, and the final report and presentation.

My feedback question is: would independent reproduction or one more controlled fixture add more confidence, and what evidence would you expect?

ChatGPT and Codex assisted development, testing, documentation, and presentation preparation. I reviewed the evidence, made the human decisions, and remain responsible for the claims.
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

# Build a contact sheet from the rendered slides for visual review.
Add-Type -AssemblyName System.Drawing
$slideImages = @(Get-ChildItem -LiteralPath $renderDirectory -Filter '*.PNG' | Sort-Object Name)
$thumbWidth = 400
$thumbHeight = 225
$sheet = New-Object Drawing.Bitmap 1600, 450
$graphics = [Drawing.Graphics]::FromImage($sheet)
$graphics.Clear([Drawing.Color]::FromArgb(24, 29, 38))
$graphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
try {
    for ($i = 0; $i -lt $slideImages.Count; $i++) {
        $image = [Drawing.Image]::FromFile($slideImages[$i].FullName)
        try {
            $x = ($i % 4) * $thumbWidth
            $y = [Math]::Floor($i / 4) * $thumbHeight
            $graphics.DrawImage($image, $x, $y, $thumbWidth, $thumbHeight)
        } finally {
            $image.Dispose()
        }
    }
    $sheet.Save($contactSheet, [Drawing.Imaging.ImageFormat]::Png)
} finally {
    $graphics.Dispose()
    $sheet.Dispose()
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($target)
try {
    $slideCount = @($archive.Entries | Where-Object { $_.FullName -match '^ppt/slides/slide\d+\.xml$' }).Count
    $notesCount = @($archive.Entries | Where-Object { $_.FullName -match '^ppt/notesSlides/notesSlide\d+\.xml$' }).Count
    $presentationText = New-Object Text.StringBuilder
    foreach ($entry in @($archive.Entries | Where-Object { $_.FullName -match '^ppt/slides/slide\d+\.xml$' })) {
        $reader = New-Object IO.StreamReader($entry.Open())
        try { [void]$presentationText.Append($reader.ReadToEnd()) } finally { $reader.Dispose() }
    }
} finally {
    $archive.Dispose()
}
if ($slideCount -ne 7 -or $notesCount -ne 7) {
    throw "Unexpected deck structure: $slideCount slides, $notesCount notes."
}
$requiredTokens = @('PATH-S06', '0 / 5', 'Traversal 02', 'SUPPLEMENTAL-v1', 'independent reproduction')
foreach ($token in $requiredTokens) {
    if (-not $presentationText.ToString().Contains($token)) {
        throw "Required slide token missing: $token"
    }
}

$verification = [ordered]@{
    generated_on = (Get-Date).ToString('o')
    output = $target
    pdf = $pdfPath
    rendered_slides = $renderDirectory
    contact_sheet = $contactSheet
    slides = $slideCount
    speaker_notes = $notesCount
    pptx_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    pdf_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $pdfPath).Hash.ToLowerInvariant()
    package_structure = 'pass'
    evidence_boundary = 'primary-v1, supplemental-v1, and path-s06-extension-v1 remain separate'
    recording_status = 'pending visual inspection and personal rehearsal'
}
$verification | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $verificationPath -Encoding utf8

Write-Output "Created: $target"
Write-Output "Created: $pdfPath"
Write-Output "Rendered slides: $renderDirectory"
Write-Output "Contact sheet: $contactSheet"
Write-Output "Verification: $verificationPath"
