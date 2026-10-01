[CmdletBinding()]
param(
    [string]$InputPath = 'docs\coursework\review-2026-09-30\Progress-Report-4-working-draft.md',
    [string]$OutputPath = 'docs\coursework\review-2026-09-30\Progress Report 4 (Tony Tran) - Student Evidence Aligned October 1.docx',
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
$allowedRoot = Resolve-ProjectPath 'docs\coursework\review-2026-09-30'
$pdfPath = [IO.Path]::ChangeExtension($target, '.pdf')

if (-not $target.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay inside docs/coursework/review-2026-09-30.'
}
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Source Markdown not found: $source"
}
if ((Test-Path -LiteralPath $target) -and -not $Overwrite) {
    throw "Output already exists; use -Overwrite to replace it: $target"
}

[IO.Directory]::CreateDirectory($allowedRoot) | Out-Null
if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Force }
if (Test-Path -LiteralPath $pdfPath) { Remove-Item -LiteralPath $pdfPath -Force }

$wdAlignParagraphLeft = 0
$wdAlignParagraphCenter = 1
$wdAlignParagraphRight = 2
$wdCollapseEnd = 0
$wdAutoFitWindow = 2
$wdFormatDocumentDefault = 16
$wdExportFormatPDF = 17
$wdFieldPage = 33
$wdPageBreak = 7

function Clean-InlineMarkdown {
    param([string]$Text)
    $clean = $Text.Replace('`', '')
    $clean = $clean.Replace('**', '')
    return $clean.Trim()
}

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Add()

    $section = $document.Sections.Item(1)
    $section.PageSetup.TopMargin = 45
    $section.PageSetup.BottomMargin = 45
    $section.PageSetup.LeftMargin = 50
    $section.PageSetup.RightMargin = 50

    $normal = $document.Styles.Item('Normal')
    $normal.Font.Name = 'Times New Roman'
    $normal.Font.Size = 10.5
    $normal.ParagraphFormat.SpaceAfter = 4
    $normal.ParagraphFormat.LineSpacingRule = 0

    function Add-WordParagraph {
        param(
            [string]$Text,
            [ValidateSet('normal','section','subsection','title','meta','callout','bullet','number')]
            [string]$Kind = 'normal'
        )
        $range = $document.Range($document.Content.End - 1, $document.Content.End - 1)
        $range.Text = (Clean-InlineMarkdown $Text)
        $range.InsertParagraphAfter()
        $paragraph = $document.Paragraphs.Item($document.Paragraphs.Count - 1)
        $paragraph.Range.Font.Name = 'Times New Roman'
        $paragraph.Range.Font.Size = 10.5
        $paragraph.Range.ParagraphFormat.Alignment = $wdAlignParagraphLeft
        $paragraph.Range.ParagraphFormat.LeftIndent = 0
        $paragraph.Range.ParagraphFormat.FirstLineIndent = 0
        $paragraph.Range.ParagraphFormat.SpaceBefore = 0
        $paragraph.Range.ParagraphFormat.SpaceAfter = 4
        $paragraph.Range.ParagraphFormat.KeepWithNext = 0

        switch ($Kind) {
            'title' {
                $paragraph.Range.Font.Size = 15
                $paragraph.Range.Font.Bold = -1
                $paragraph.Range.ParagraphFormat.Alignment = $wdAlignParagraphCenter
                $paragraph.Range.ParagraphFormat.SpaceAfter = 7
            }
            'meta' {
                $paragraph.Range.Font.Size = 10.5
                $paragraph.Range.ParagraphFormat.Alignment = $wdAlignParagraphCenter
                $paragraph.Range.ParagraphFormat.SpaceAfter = 2
            }
            'section' {
                $paragraph.Range.Font.Size = 12
                $paragraph.Range.Font.Bold = -1
                $paragraph.Range.ParagraphFormat.SpaceBefore = 8
                $paragraph.Range.ParagraphFormat.SpaceAfter = 3
                $paragraph.Range.ParagraphFormat.KeepWithNext = -1
            }
            'subsection' {
                $paragraph.Range.Font.Size = 11
                $paragraph.Range.Font.Bold = -1
                $paragraph.Range.ParagraphFormat.SpaceBefore = 6
                $paragraph.Range.ParagraphFormat.SpaceAfter = 2
                $paragraph.Range.ParagraphFormat.KeepWithNext = -1
            }
            'callout' {
                $paragraph.Range.Font.Size = 9.5
                $paragraph.Range.Font.Italic = -1
                $paragraph.Range.ParagraphFormat.LeftIndent = 10
                $paragraph.Range.ParagraphFormat.RightIndent = 10
                $paragraph.Range.ParagraphFormat.SpaceBefore = 4
                $paragraph.Range.ParagraphFormat.SpaceAfter = 7
                $paragraph.Range.Shading.BackgroundPatternColor = 15132390
            }
            'bullet' {
                $paragraph.Range.Text = ([char]0x2022).ToString() + '  ' + (Clean-InlineMarkdown $Text) + [char]13
                $paragraph.Range.Font.Name = 'Times New Roman'
                $paragraph.Range.Font.Size = 10.5
                $paragraph.Range.ParagraphFormat.LeftIndent = 18
                $paragraph.Range.ParagraphFormat.FirstLineIndent = -9
                $paragraph.Range.ParagraphFormat.SpaceAfter = 3
            }
            'number' {
                $paragraph.Range.ParagraphFormat.LeftIndent = 18
                $paragraph.Range.ParagraphFormat.FirstLineIndent = -12
                $paragraph.Range.ParagraphFormat.SpaceAfter = 3
            }
        }
        return $paragraph
    }

    function Add-WordTable {
        param([object[]]$Rows)
        if ($Rows.Count -lt 2) { return }
        $columnCount = $Rows[0].Count
        $range = $document.Range($document.Content.End - 1, $document.Content.End - 1)
        $table = $document.Tables.Add($range, $Rows.Count, $columnCount)
        $table.Style = 'Table Grid'
        $table.AllowAutoFit = -1
        $table.AutoFitBehavior($wdAutoFitWindow)
        $table.Range.Font.Name = 'Times New Roman'
        $table.Range.Font.Size = 8.5
        $table.Range.ParagraphFormat.SpaceAfter = 1
        $table.Rows.Item(1).HeadingFormat = -1
        $table.Rows.Item(1).Range.Font.Bold = -1
        $table.Rows.Item(1).Range.Shading.BackgroundPatternColor = 14277081
        for ($r = 0; $r -lt $Rows.Count; $r++) {
            $table.Rows.Item($r + 1).AllowBreakAcrossPages = 0
            for ($c = 0; $c -lt $columnCount; $c++) {
                $value = if ($c -lt $Rows[$r].Count) { [string]$Rows[$r][$c] } else { '' }
                $table.Cell($r + 1, $c + 1).Range.Text = (Clean-InlineMarkdown $value)
            }
        }
        $table.Range.InsertParagraphAfter()
    }

    $raw = [IO.File]::ReadAllText($source, [Text.UTF8Encoding]::new($false))
    $lines = [regex]::Split($raw, '\r?\n')
    $paragraphBuffer = [Collections.Generic.List[string]]::new()

    function Flush-ParagraphBuffer {
        if ($paragraphBuffer.Count -gt 0) {
            $joined = (($paragraphBuffer | ForEach-Object { $_.Trim() }) -join ' ').Trim()
            if ($joined) {
                if ($joined.StartsWith('Draft status:')) {
                    [void](Add-WordParagraph $joined 'callout')
                } else {
                    [void](Add-WordParagraph $joined 'normal')
                }
            }
            $paragraphBuffer.Clear()
        }
    }

    $index = 0
    $metaLinesWritten = 0
    while ($index -lt $lines.Count) {
        $line = [string]$lines[$index]
        $trimmed = $line.Trim()

        if (-not $trimmed) {
            Flush-ParagraphBuffer
            $index++
            continue
        }

        if ($trimmed.StartsWith('|')) {
            Flush-ParagraphBuffer
            $tableLines = [Collections.Generic.List[string]]::new()
            while ($index -lt $lines.Count -and ([string]$lines[$index]).Trim().StartsWith('|')) {
                $tableLines.Add(([string]$lines[$index]).Trim())
                $index++
            }
            $rows = [Collections.Generic.List[object]]::new()
            for ($t = 0; $t -lt $tableLines.Count; $t++) {
                if ($t -eq 1 -and $tableLines[$t] -match '^\|[\s:\-|]+\|$') { continue }
                $cells = $tableLines[$t].Trim('|').Split('|') | ForEach-Object { $_.Trim() }
                $rows.Add(@($cells))
            }
            Add-WordTable @($rows)
            continue
        }

        if ($trimmed.StartsWith('## ')) {
            Flush-ParagraphBuffer
            [void](Add-WordParagraph $trimmed.Substring(3) 'section')
            $index++
            continue
        }
        if ($trimmed.StartsWith('### ')) {
            Flush-ParagraphBuffer
            [void](Add-WordParagraph $trimmed.Substring(4) 'subsection')
            $index++
            continue
        }
        if ($trimmed.StartsWith('# ')) {
            Flush-ParagraphBuffer
            $heading = $trimmed.Substring(2)
            if ($heading.StartsWith('Section:')) {
                [void](Add-WordParagraph $heading 'meta')
            } else {
                [void](Add-WordParagraph $heading 'title')
            }
            $index++
            continue
        }
        if ($trimmed.StartsWith('- ')) {
            Flush-ParagraphBuffer
            $bulletParts = [Collections.Generic.List[string]]::new()
            $bulletParts.Add($trimmed.Substring(2))
            $index++
            while ($index -lt $lines.Count) {
                $continuation = ([string]$lines[$index]).Trim()
                if (-not $continuation -or
                    $continuation.StartsWith('- ') -or
                    $continuation.StartsWith('#') -or
                    $continuation.StartsWith('|') -or
                    $continuation -match '^\d+\.\s+') {
                    break
                }
                $bulletParts.Add($continuation)
                $index++
            }
            [void](Add-WordParagraph (($bulletParts -join ' ').Trim()) 'bullet')
            continue
        }
        if ($trimmed -match '^\d+\.\s+') {
            Flush-ParagraphBuffer
            [void](Add-WordParagraph $trimmed 'number')
            $index++
            continue
        }

        if ($metaLinesWritten -lt 2 -and ($trimmed -eq 'Tony Tran' -or $trimmed.StartsWith('Progress Report 4'))) {
            Flush-ParagraphBuffer
            [void](Add-WordParagraph $trimmed 'meta')
            $metaLinesWritten++
            $index++
            continue
        }

        $paragraphBuffer.Add($line)
        if ($line.EndsWith('  ')) { Flush-ParagraphBuffer }
        $index++
    }
    Flush-ParagraphBuffer

    $footer = $document.Sections.Item(1).Footers.Item(1).Range
    $footer.Text = 'FixProof Progress Report 4 - Working Draft | '
    $footer.Font.Name = 'Times New Roman'
    $footer.Font.Size = 8
    $footer.ParagraphFormat.Alignment = $wdAlignParagraphRight
    $footer.Collapse($wdCollapseEnd)
    [void]$document.Fields.Add($footer, $wdFieldPage)

    $document.SaveAs2($target, $wdFormatDocumentDefault)
    $document.ExportAsFixedFormat($pdfPath, $wdExportFormatPDF)
    $document.Close($false)
    $document = $null
} finally {
    if ($null -ne $document) {
        try { $document.Close($false) } catch { }
    }
    if ($null -ne $word) {
        try { $word.Quit() } catch { }
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) } catch { }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Output "Created: $target"
Write-Output "Created: $pdfPath"
