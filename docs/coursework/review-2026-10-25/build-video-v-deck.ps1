[CmdletBinding()]
param(
    [string]$OutputPath = 'docs\coursework\review-2026-10-25\FixProof - Video V - Final Evidence Checkpoint.pptx',
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

$target = Resolve-ProjectPath $OutputPath
$allowedRoot = Resolve-ProjectPath 'docs\coursework\review-2026-10-25'
$pdfPath = [IO.Path]::ChangeExtension($target, '.pdf')
$renderDirectory = Join-Path $allowedRoot 'video-v-rendered-slides'
$contactSheet = Join-Path $allowedRoot 'Video-V-contact-sheet.png'
$verificationPath = Join-Path $allowedRoot 'Video-V-deck-verification.json'
$scriptPath = Join-Path $allowedRoot 'Video-V-under-3-minute-script.md'

if (-not $target.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay inside docs/coursework/review-2026-10-25.'
}
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
    throw "Validated Video V script not found: $scriptPath"
}
if ((Test-Path -LiteralPath $target) -and -not $Overwrite) {
    throw "Output exists; use -Overwrite to replace it: $target"
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

function Set-SlideBackground {
    param($Slide, [int]$Color)
    $Slide.FollowMasterBackground = $msoFalse
    $Slide.Background.Fill.Solid()
    $Slide.Background.Fill.ForeColor.RGB = $Color
}

function Add-Text {
    param(
        $Slide, [string]$Text, [float]$X, [float]$Y, [float]$W, [float]$H,
        [float]$Size = 18, [int]$Color = $ink, [bool]$Bold = $false,
        [string]$Font = 'Aptos', [int]$Align = 1, [int]$Vertical = 1
    )
    $shape = $Slide.Shapes.AddTextbox($msoTextOrientationHorizontal, $X, $Y, $W, $H)
    $shape.TextFrame.MarginLeft = 0
    $shape.TextFrame.MarginRight = 0
    $shape.TextFrame.MarginTop = 0
    $shape.TextFrame.MarginBottom = 0
    $shape.TextFrame.WordWrap = $msoTrue
    $shape.TextFrame.AutoSize = 0
    try { $shape.TextFrame.VerticalAnchor = $Vertical } catch { }
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
        $Slide, [float]$X, [float]$Y, [float]$W, [float]$H,
        [int]$Fill, [int]$Stroke = $line, [bool]$Rounded = $true
    )
    $shapeType = $(if ($Rounded) { $msoShapeRoundedRectangle } else { $msoShapeRectangle })
    $shape = $Slide.Shapes.AddShape($shapeType, $X, $Y, $W, $H)
    $shape.Fill.Solid()
    $shape.Fill.ForeColor.RGB = $Fill
    $shape.Line.ForeColor.RGB = $Stroke
    $shape.Line.Weight = 1.2
    return $shape
}

function Add-Line {
    param(
        $Slide, [float]$X1, [float]$Y1, [float]$X2, [float]$Y2,
        [int]$Color = $blueDark, [float]$Weight = 2.0, [bool]$Arrow = $false
    )
    $shape = $Slide.Shapes.AddLine($X1, $Y1, $X2, $Y2)
    $shape.Line.ForeColor.RGB = $Color
    $shape.Line.Weight = $Weight
    if ($Arrow) { $shape.Line.EndArrowheadStyle = $msoArrowheadTriangle }
    return $shape
}

function Add-Pill {
    param($Slide, [string]$Text, [float]$X, [float]$Y, [float]$W, [int]$Fill, [int]$TextColor)
    $null = Add-Box $Slide $X $Y $W 30 $Fill $Fill $true
    $null = Add-Text $Slide $Text $X ($Y + 5) $W 20 12 $TextColor $true 'Aptos' 2 3
}

function Add-Header {
    param($Slide, [string]$Title, [string]$Kicker, [int]$SlideNumber)
    $null = Add-Text $Slide $Kicker 48 24 720 22 12 $blue $true
    $null = Add-Text $Slide $Title 48 48 850 48 27 $navy $true
    $null = Add-Line $Slide 48 105 912 105 $line 1 $false
    $null = Add-Text $Slide 'CS6727 | FixProof Video V' 48 510 300 16 10 $muted $false
    $null = Add-Text $Slide ([string]$SlideNumber) 885 510 27 16 10 $muted $false 'Aptos' 3
}

function Add-CheckItem {
    param($Slide, [string]$Text, [float]$X, [float]$Y, [float]$W, [int]$Accent = $green)
    $circle = $Slide.Shapes.AddShape($msoShapeOval, $X, ($Y + 1), 20, 20)
    $circle.Fill.Solid()
    $circle.Fill.ForeColor.RGB = $Accent
    $circle.Line.Visible = $msoFalse
    $null = Add-Text $Slide 'OK' ($X + 2) ($Y + 6) 16 10 6.5 $white $true 'Arial' 2 3
    $null = Add-Text $Slide $Text ($X + 30) $Y ($W - 30) 38 14 $ink $false
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

$scriptText = [IO.File]::ReadAllText($scriptPath, [Text.UTF8Encoding]::new($false))
function Get-SlideNotes {
    param([int]$Number)
    $pattern = "(?ms)^## Slide $Number\b.*?\r?\n\r?\n(?<body>.*?)(?=^## Slide \d+\b|^## Optional browser transition)"
    $match = [regex]::Match($scriptText, $pattern)
    if (-not $match.Success) { throw "Narration section missing for Slide $Number." }
    return $match.Groups['body'].Value.Trim()
}

$powerPoint = $null
$presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.Visible = $msoTrue
    $presentation = $powerPoint.Presentations.Add()
    $presentation.PageSetup.SlideWidth = 960
    $presentation.PageSetup.SlideHeight = 540

    # Slide 1 - title
    $slide = $presentation.Slides.Add(1, $ppLayoutBlank)
    Set-SlideBackground $slide $navy
    Add-Pill $slide 'POST VIDEO V' 58 50 150 $orange $navy
    $null = Add-Text $slide 'FIXPROOF' 58 110 330 58 39 $white $true
    $null = Add-Text $slide 'From AI-proposed patch to reviewable evidence' 58 174 820 84 31 $white $true
    $null = Add-Text $slide 'Final evidence and reproducibility checkpoint' 58 272 760 28 17 (RGB 190 210 235) $false
    Add-Pill $slide '15 CANDIDATES' 58 350 170 $blue $white
    Add-Pill $slide '245 CASE ROWS' 244 350 170 $purple $white
    Add-Pill $slide '131 TESTS PASSED' 430 350 190 $green $white
    $null = Add-Text $slide 'Tony Tran | CS6727 Cyber Security Practicum | October 2026' 58 492 700 18 11 (RGB 180 202 230) $false
    $null = Add-Text $slide '1' 885 492 27 18 11 (RGB 180 202 230) $false 'Aptos' 3
    Add-Notes $slide (Get-SlideNotes 1)

    # Slide 2 - progression
    $slide = $presentation.Slides.Add(2, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'How the project progressed' '1. CHRONOLOGICAL RESEARCH PATH' 2
    $items = @(
        @{x=48;n='I';title='Problem + pilot';body="Research question`nThree CWEs`nInitial pipeline";fill=$blueLight;stroke=$blue},
        @{x=226;n='II';title='Primary-v1';body="15 candidates`n100 observations`n10 conflicts";fill=$blueLight;stroke=$blue},
        @{x=404;n='III';title='Supplemental-v1';body="140 observations`nLater reviews`nPublic viewer";fill=$orangeLight;stroke=$orange},
        @{x=582;n='IV';title='PATH-S06';body="WSL2 extension`n0 pass / 5 fail`nHistory preserved";fill=$purpleLight;stroke=$purple},
        @{x=760;n='V';title='Final checkpoint';body="Clean reproduction`nClaim boundaries`nFinal package";fill=$greenLight;stroke=$green}
    )
    foreach ($item in $items) {
        $null = Add-Box $slide $item.x 154 152 224 $item.fill $item.stroke $true
        $circle = $slide.Shapes.AddShape($msoShapeOval, ($item.x + 52), 126, 48, 48)
        $circle.Fill.Solid(); $circle.Fill.ForeColor.RGB = $item.stroke; $circle.Line.Visible = $msoFalse
        $null = Add-Text $slide $item.n ($item.x + 64) 140 24 20 14 $white $true 'Aptos' 2 3
        $null = Add-Text $slide $item.title ($item.x + 14) 184 124 38 15 $navy $true 'Aptos' 2
        $null = Add-Text $slide $item.body ($item.x + 14) 235 124 92 13 $muted $false 'Aptos' 2
    }
    for ($i=0; $i -lt 4; $i++) {
        $null = Add-Line $slide ($items[$i].x + 152) 266 $items[$i+1].x 266 $blueDark 2 $true
    }
    $null = Add-Box $slide 174 416 612 54 $navy $navy $true
    $null = Add-Text $slide 'VIDEO V CONSOLIDATES THE EVIDENCE - IT ADDS NO NEW EXPERIMENT' 194 433 572 20 14 $white $true 'Aptos' 2
    Add-Notes $slide (Get-SlideNotes 2)

    # Slide 3 - roles and authority
    $slide = $presentation.Slides.Add(3, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Python coordinates; separate authorities decide' '2. FIXPROOF WORKFLOW' 3
    $roles = @(
        @{x=48;title='Fixture + finding';sub='Frozen input';fill=$blueLight;stroke=$blue},
        @{x=220;title='Repair model';sub='Proposes code';fill=$orangeLight;stroke=$orange},
        @{x=392;title='Python';sub='Copies + invokes';fill=$blueLight;stroke=$blue},
        @{x=564;title='Validators';sub='Measure evidence';fill=$greenLight;stroke=$green},
        @{x=736;title='Policy';sub='Routes outcome';fill=$purpleLight;stroke=$purple}
    )
    foreach ($role in $roles) {
        $null = Add-Box $slide $role.x 140 148 94 $role.fill $role.stroke $true
        $null = Add-Text $slide $role.title ($role.x + 10) 157 128 24 15 $navy $true 'Aptos' 2
        $null = Add-Text $slide $role.sub ($role.x + 10) 195 128 20 12 $muted $false 'Aptos' 2
    }
    for ($i=0; $i -lt 4; $i++) { $null = Add-Line $slide ($roles[$i].x + 148) 187 $roles[$i+1].x 187 $blueDark 2 $true }
    $null = Add-Line $slide 810 234 810 286 $purple 3 $true
    $null = Add-Box $slide 648 286 326 92 $purpleLight $purple $true
    $null = Add-Text $slide 'Human review' 668 304 286 24 18 $navy $true 'Aptos' 2
    $null = Add-Text $slide 'Records acceptance, rejection, or follow-up rationale' 674 339 274 28 13 $muted $false 'Aptos' 2

    $null = Add-Box $slide 48 286 560 92 $white $line $true
    $null = Add-Text $slide 'VALIDATION OUTPUTS' 68 304 520 18 11 $blue $true
    $null = Add-Pill $slide 'SYNTAX' 68 333 92 $blue $white
    $null = Add-Pill $slide 'SAST' 172 333 80 $blue $white
    $null = Add-Pill $slide 'SECURITY' 264 333 102 $green $white
    $null = Add-Pill $slide 'FUNCTIONAL' 378 333 116 $green $white
    $null = Add-Pill $slide 'EVIDENCE' 506 333 92 $purple $white

    $null = Add-Box $slide 48 414 864 58 $navy $navy $true
    $null = Add-Text $slide 'No automatic approval or deployment' 68 431 292 22 15 $white $true
    $null = Add-Text $slide 'src/fixproof/  ->  data/primary_trials/v1/  ->  data/primary_reviews/v1/' 382 431 500 22 13 (RGB 190 210 235) $false 'Consolas' 2
    Add-Notes $slide (Get-SlideNotes 3)

    # Slide 4 - results
    $slide = $presentation.Slides.Add(4, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Three evidence layers, three denominators' '3. FINAL RECORDED RESULTS' 4
    $cards = @(
        @{x=48;tag='PRIMARY-v1';headline='15 candidates';metric='100 observations';detail="5/15 target SAST resolved`n15/15 primary suites passed`n10 SAST/runtime disagreements";fill=$blueLight;stroke=$blue},
        @{x=338;tag='SUPPLEMENTAL-v1';headline='140 observations';metric='120 pass | 15 fail | 5 inconclusive';detail="Security, behavioral parity,`nand robustness remain separate";fill=$orangeLight;stroke=$orange},
        @{x=628;tag='PATH-S06 EXTENSION';headline='5 observations';metric='0 pass | 5 fail | 0 inconclusive';detail="One registered Linux`nsymbolic-link case per candidate";fill=$purpleLight;stroke=$purple}
    )
    foreach ($card in $cards) {
        $null = Add-Box $slide $card.x 138 266 250 $card.fill $card.stroke $true
        $null = Add-Text $slide $card.tag ($card.x + 18) 157 230 18 11 $card.stroke $true
        $null = Add-Text $slide $card.headline ($card.x + 18) 193 230 36 24 $navy $true
        $null = Add-Text $slide $card.metric ($card.x + 18) 239 230 44 14 $ink $true
        $null = Add-Line $slide ($card.x + 18) 291 ($card.x + 248) 291 $card.stroke 1 $false
        $null = Add-Text $slide $card.detail ($card.x + 18) 310 230 70 13 $muted $false
    }
    $null = Add-Box $slide 98 420 764 54 $navy $navy $true
    $null = Add-Text $slide '29 HUMAN RECORDS' 118 437 168 18 13 (RGB 146 180 224) $true
    $null = Add-Text $slide 'Primary, supplemental, and extension outcomes are not one combined success rate.' 294 434 548 24 15 $white $true 'Aptos' 2
    Add-Notes $slide (Get-SlideNotes 4)

    # Slide 5 - interpretation by CWE
    $slide = $presentation.Slides.Add(5, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Why multiple evidence channels mattered' '4. CASE-LEVEL INTERPRETATION' 5
    $cases = @(
        @{x=48;name='REFLECTED XSS';passed='Registered attacks blocked';qualification='4 of 5 failed XSS-P01 parity';interpret='Later rejection for exact behavior - not continued exploitability';fill=$blueLight;stroke=$blue},
        @{x=338;name='SQL INJECTION';passed='Security 15/15 | parity 10/10';qualification='SQL-R01 failed for all five';interpret='Bounded injection acceptance with robustness limitation disclosed';fill=$orangeLight;stroke=$orange},
        @{x=628;name='PATH TRAVERSAL';passed='Direct ../ request rejected';qualification='PATH-S06 failed for all five';interpret='Later rejection: lexical checks did not contain symlink targets';fill=$purpleLight;stroke=$purple}
    )
    foreach ($case in $cases) {
        $null = Add-Box $slide $case.x 136 266 320 $white $case.stroke $true
        $null = Add-Box $slide $case.x 136 266 44 $case.fill $case.stroke $true
        $null = Add-Text $slide $case.name ($case.x + 16) 149 234 18 12 $case.stroke $true 'Aptos' 2
        $null = Add-Text $slide 'PASSED' ($case.x + 18) 204 72 18 10 $green $true
        $null = Add-Text $slide $case.passed ($case.x + 18) 227 230 38 15 $navy $true
        $null = Add-Text $slide 'QUALIFICATION' ($case.x + 18) 282 110 18 10 $orange $true
        $null = Add-Text $slide $case.qualification ($case.x + 18) 305 230 42 15 $ink $true
        $null = Add-Line $slide ($case.x + 18) 362 ($case.x + 248) 362 $line 1 $false
        $null = Add-Text $slide $case.interpret ($case.x + 18) 381 230 60 13 $muted $false
    }
    $null = Add-Text $slide 'A pass in one evidence channel does not erase a recorded failure in another.' 132 474 696 24 15 $navy $true 'Aptos' 2
    Add-Notes $slide (Get-SlideNotes 5)

    # Slide 6 - reproducibility and package
    $slide = $presentation.Slides.Add(6, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Reproducible and reviewable package' '5. CLEAN REHEARSAL + PUBLIC REFERENCE' 6
    $null = Add-Box $slide 48 136 416 224 $greenLight $green $true
    $null = Add-Text $slide 'CLEAN REPRODUCTION' 68 155 376 18 11 $green $true
    Add-CheckItem $slide 'Clean Git export and fresh Python environment' 68 194 360 $green
    Add-CheckItem $slide 'Pinned Python and six Node dependency trees' 68 240 360 $green
    Add-CheckItem $slide '131 repository tests passed' 68 286 360 $green
    Add-CheckItem $slide 'Controlled demo decisions matched saved records' 68 332 360 $green

    $null = Add-Box $slide 496 136 416 224 $blueLight $blue $true
    $null = Add-Text $slide 'PUBLIC EVIDENCE VIEWER' 516 155 376 18 11 $blue $true
    $null = Add-Text $slide '15' 526 194 80 48 36 $navy $true 'Aptos Display' 2
    $null = Add-Text $slide 'candidates' 526 241 80 18 11 $muted $true 'Aptos' 2
    $null = Add-Text $slide '245' 650 194 90 48 36 $navy $true 'Aptos Display' 2
    $null = Add-Text $slide 'case rows' 650 241 90 18 11 $muted $true 'Aptos' 2
    $null = Add-Text $slide '29' 790 194 80 48 36 $navy $true 'Aptos Display' 2
    $null = Add-Text $slide 'human records' 780 241 100 18 11 $muted $true 'Aptos' 2
    $null = Add-Text $slide 'Read-only saved evidence - not a model, scanner, test runner, approval, or deployment system.' 526 288 356 52 14 $blueDark $true 'Aptos' 2

    $null = Add-Box $slide 48 390 864 84 $codeBg $codeBg $true
    $null = Add-Text $slide 'FINAL-DELIVERABLE/' 68 407 172 18 11 (RGB 137 178 226) $true 'Consolas'
    $null = Add-Text $slide '01-final-report/     02-final-presentation/     03-supporting-materials/     04-manifest-and-checksums/' 68 436 824 24 13 $white $false 'Consolas' 2
    Add-Notes $slide (Get-SlideNotes 6)

    # Slide 7 - conclusion and next steps
    $slide = $presentation.Slides.Add(7, $ppLayoutBlank)
    Set-SlideBackground $slide $paper
    Add-Header $slide 'Bounded conclusion and next milestones' '6. COURSE DIRECTION' 7
    $null = Add-Box $slide 48 132 410 188 $greenLight $green $true
    $null = Add-Text $slide 'SUPPORTED' 68 151 370 18 11 $green $true
    Add-CheckItem $slide 'Traceable decisions for registered cases' 68 188 350 $green
    Add-CheckItem $slide 'Visible disagreements, regressions, and qualifications' 68 232 350 $green
    Add-CheckItem $slide 'Reproducible evidence package in the tested environment' 68 276 350 $green

    $null = Add-Box $slide 482 132 430 188 $orangeLight $orange $true
    $null = Add-Text $slide 'NOT ESTABLISHED' 502 151 390 18 11 $orange $true
    $null = Add-Text $slide 'Production repair-success rate' 502 191 370 22 15 $ink $true
    $null = Add-Text $slide 'Scanner accuracy across repositories' 502 231 370 22 15 $ink $true
    $null = Add-Text $slide 'Generalization beyond three controlled Express fixtures' 502 271 370 38 15 $ink $true

    $null = Add-Box $slide 48 348 864 66 $navy $navy $true
    $null = Add-Text $slide 'NOV 1' 68 365 64 18 11 (RGB 146 180 224) $true
    $null = Add-Text $slide 'Report 5' 68 386 74 18 12 $white $true
    $null = Add-Text $slide 'NOV 3' 230 365 64 18 11 (RGB 146 180 224) $true
    $null = Add-Text $slide 'Video V' 230 386 74 18 12 $white $true
    $null = Add-Text $slide 'NOV 15' 390 365 72 18 11 (RGB 146 180 224) $true
    $null = Add-Text $slide 'Final presentation' 390 386 130 18 12 $white $true
    $null = Add-Text $slide 'DEC 6' 600 365 64 18 11 (RGB 146 180 224) $true
    $null = Add-Text $slide 'Final report + package' 600 386 154 18 12 $white $true

    $null = Add-Box $slide 48 434 864 52 $white $line $true
    $null = Add-Text $slide 'FEEDBACK' 68 451 76 18 11 $purple $true
    $null = Add-Text $slide 'Is one candidate example enough to explain validators, policy, and human judgment?' 152 448 740 24 14 $navy $true 'Aptos' 2
    Add-Notes $slide (Get-SlideNotes 7)

    $presentation.SaveAs($target, $ppSaveAsOpenXMLPresentation)
    $presentation.SaveAs($pdfPath, $ppSaveAsPDF)
    $presentation.Export($renderDirectory, 'PNG', 1600, 900)
    $presentation.Close()
    $presentation = $null
} finally {
    if ($presentation) { try { $presentation.Close() } catch { } }
    if ($powerPoint) {
        try { $powerPoint.Quit() } catch { }
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint) } catch { }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

# Build a contact sheet for quick visual review.
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
        $picture = [Drawing.Image]::FromFile($slideImages[$i].FullName)
        try {
            $x = ($i % 4) * $thumbWidth
            $y = [Math]::Floor($i / 4) * $thumbHeight
            $graphics.DrawImage($picture, $x, $y, $thumbWidth, $thumbHeight)
        } finally { $picture.Dispose() }
    }
    $sheet.Save($contactSheet, [Drawing.Imaging.ImageFormat]::Png)
} finally {
    $graphics.Dispose()
    $sheet.Dispose()
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($target)
try {
    $slideEntries = @($archive.Entries | Where-Object { $_.FullName -match '^ppt/slides/slide\d+\.xml$' })
    $notesEntries = @($archive.Entries | Where-Object { $_.FullName -match '^ppt/notesSlides/notesSlide\d+\.xml$' })
    $allText = New-Object Text.StringBuilder
    foreach ($entry in $slideEntries) {
        $reader = [IO.StreamReader]::new($entry.Open())
        try { [void]$allText.Append($reader.ReadToEnd()) } finally { $reader.Dispose() }
    }
} finally { $archive.Dispose() }

if ($slideEntries.Count -ne 7 -or $notesEntries.Count -ne 7) {
    throw "Unexpected package structure: $($slideEntries.Count) slides and $($notesEntries.Count) note pages."
}
$requiredTokens = @(
    '15 candidates', '140 observations', '0 pass | 5 fail',
    'Python coordinates', '131 repository tests passed', 'NOT ESTABLISHED'
)
foreach ($token in $requiredTokens) {
    if (-not $allText.ToString().Contains($token)) { throw "Required slide token missing: $token" }
}

$verification = [ordered]@{
    generated_on = (Get-Date).ToString('o')
    output = $target
    pdf = $pdfPath
    rendered_slides = $renderDirectory
    contact_sheet = $contactSheet
    slides = $slideEntries.Count
    speaker_notes = $notesEntries.Count
    main_script_words = 378
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
