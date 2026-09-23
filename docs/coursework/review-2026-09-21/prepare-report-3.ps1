[CmdletBinding()]
param(
    [string]$Report2Path = 'C:\Users\Tony Tran\OneDrive\Documents\Progress Report 2 (Tony Tran) - Updated Draft (1).docx',
    [string]$OutputPath = 'docs\coursework\review-2026-09-21\Progress Report 3 (Tony Tran) - Working Draft September 23 - Professor Feedback Aligned.docx',
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$projectRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $projectRoot) {
    throw 'Run this script from inside the FixProof repository.'
}
$source = [IO.Path]::GetFullPath($Report2Path)
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
    throw "Report 2 template not found: $source"
}
if ((Test-Path -LiteralPath $target) -and -not $Overwrite) {
    throw "Output already exists; refusing to overwrite: $target"
}

$w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
$xmlNs = 'http://www.w3.org/XML/1998/namespace'
$inputZip = [IO.Compression.ZipFile]::OpenRead($source)
try {
    $sourceEntry = $inputZip.GetEntry('word/document.xml')
    if (-not $sourceEntry) { throw 'Template is missing word/document.xml.' }
    $reader = [IO.StreamReader]::new($sourceEntry.Open(), [Text.Encoding]::UTF8)
    try { $sourceXml = $reader.ReadToEnd() } finally { $reader.Dispose() }
} finally {
    $inputZip.Dispose()
}

$doc = [Xml.XmlDocument]::new()
$doc.PreserveWhitespace = $true
$doc.LoadXml($sourceXml)
$ns = [Xml.XmlNamespaceManager]::new($doc.NameTable)
$ns.AddNamespace('w', $w)
$body = $doc.SelectSingleNode('/w:document/w:body', $ns)
if (-not $body -or $body.ChildNodes.Count -ne 62) {
    throw 'Report 2 body topology differs from the reviewed 62-block template.'
}
$template = @{
    section = $body.ChildNodes[0].CloneNode($true)
    title = $body.ChildNodes[1].CloneNode($true)
    author = $body.ChildNodes[2].CloneNode($true)
    subtitle = $body.ChildNodes[3].CloneNode($true)
    heading = $body.ChildNodes[4].CloneNode($true)
    normal = $body.ChildNodes[5].CloneNode($true)
    list = $body.ChildNodes[10].CloneNode($true)
    timeline = $body.ChildNodes[31].CloneNode($true)
    evaluation = $body.ChildNodes[35].CloneNode($true)
}
$sectionProperties = $body.LastChild.CloneNode($true)
if ($sectionProperties.LocalName -ne 'sectPr') {
    throw 'Template section properties not found.'
}
$body.RemoveAll()

function Set-ParagraphText {
    param([Xml.XmlElement]$Paragraph, [string]$Value)
    $paragraphProps = $Paragraph.SelectSingleNode('./w:pPr', $ns)
    $runProps = $Paragraph.SelectSingleNode('./w:r/w:rPr', $ns)
    if ($runProps) { $runProps = $runProps.CloneNode($true) }
    $Paragraph.RemoveAll()
    if ($paragraphProps) { [void]$Paragraph.AppendChild($paragraphProps) }
    $run = $doc.CreateElement('w', 'r', $w)
    if ($runProps) { [void]$run.AppendChild($runProps) }
    $textNode = $doc.CreateElement('w', 't', $w)
    $spaceAttribute = $doc.CreateAttribute('xml', 'space', $xmlNs)
    $spaceAttribute.Value = 'preserve'
    [void]$textNode.Attributes.Append($spaceAttribute)
    $textNode.InnerText = $Value
    [void]$run.AppendChild($textNode)
    [void]$Paragraph.AppendChild($run)
}

function Add-Paragraph {
    param([string]$Kind, [string]$Value)
    $paragraph = [Xml.XmlElement]$template[$Kind].CloneNode($true)
    Set-ParagraphText $paragraph $Value
    [void]$body.AppendChild($paragraph)
}

function Set-CellText {
    param([Xml.XmlElement]$Cell, [string]$Value)
    $paragraphs = @($Cell.SelectNodes('./w:p', $ns))
    if ($paragraphs.Count -lt 1) { throw 'Template table cell has no paragraph.' }
    for ($i = $paragraphs.Count - 1; $i -ge 1; $i--) {
        [void]$Cell.RemoveChild($paragraphs[$i])
    }
    Set-ParagraphText ([Xml.XmlElement]$paragraphs[0]) $Value
}

function Add-Table {
    param([string]$Kind, [object[]]$Rows)
    $table = [Xml.XmlElement]$template[$Kind].CloneNode($true)
    $existingRows = @($table.SelectNodes('./w:tr', $ns))
    if ($existingRows.Count -lt 2) { throw "Template table has too few rows: $Kind" }
    $header = $existingRows[0].CloneNode($true)
    $detail = $existingRows[1].CloneNode($true)
    foreach ($row in $existingRows) { [void]$table.RemoveChild($row) }
    for ($rowIndex = 0; $rowIndex -lt $Rows.Count; $rowIndex++) {
        $row = [Xml.XmlElement]$(if ($rowIndex -eq 0) {
            $header.CloneNode($true)
        } else {
            $detail.CloneNode($true)
        })
        $cells = @($row.SelectNodes('./w:tc', $ns))
        if ($cells.Count -ne $Rows[$rowIndex].Count) {
            throw "Column mismatch for $Kind row $rowIndex."
        }
        for ($cellIndex = 0; $cellIndex -lt $cells.Count; $cellIndex++) {
            Set-CellText ([Xml.XmlElement]$cells[$cellIndex]) ([string]$Rows[$rowIndex][$cellIndex])
        }
        [void]$table.AppendChild($row)
    }
    [void]$body.AppendChild($table)
}

Add-Paragraph section 'Section: CS OCY, OC1'
Add-Paragraph title 'FixProof: A Validation-Oriented System for AI-Generated Vulnerability Remediation'
Add-Paragraph author 'Tony Tran'
Add-Paragraph subtitle 'Progress Report 3 - working draft; evidence verified through September 23, 2026'
Add-Paragraph normal 'Submission checkpoint: Update actual dates and hours through the submission date, reconcile September 11-13 work, check the live Canvas template and deadline, and personally verify the AI-use disclosure before submitting.'

Add-Paragraph heading 'Problem Statement:'
Add-Paragraph normal 'AI coding tools can produce insecure code, while a proposed security repair can leave a weakness exploitable or change intended application behavior. Disappearance of a static-analysis warning alone is incomplete evidence of a correct repair. Pearce et al. (2022) found approximately 40% of 1,689 Copilot-generated programs vulnerable within their selected security scenarios. Existing work also studies LLM vulnerability repair and validation feedback (Pearce et al., 2023; Kulsum et al., 2024). FixProof asks how separately recorded static, runtime-security, functional, and human-review evidence can support a patch decision.'
Add-Paragraph normal 'The evaluated scope is deliberately narrow: three purpose-built JavaScript/Express applications with reflected XSS (CWE-79), SQL injection (CWE-89), and path traversal (CWE-22). FixProof evaluates AI-generated repairs to these fixtures, not a representative corpus of AI-generated applications or production systems. This refinement addresses the original concern about concrete application construction, model role, and systematic evaluation.'
Add-Paragraph normal 'The 15 repair attempts do not estimate how often AI-generated repairs succeed in production. Instead, this controlled benchmark evaluates whether separate evidence channels reveal information omitted by an initial pass/fail result. All 15 candidates passed the frozen primary security and functional checks, but the preregistered supplemental evaluation later identified five behavioral-parity failures, ten robustness failures, and five inconclusive symlink-security observations. These results support the project goal at the workflow level: an AI-generated repair should be treated as an untrusted candidate and evaluated through preserved static, runtime, behavioral, policy, and human-review evidence. The measured percentages apply only to these three fixtures and are not projected to production repositories.'

Add-Paragraph heading 'Solution Statement:'
Add-Paragraph normal 'FixProof uses Python to orchestrate Semgrep CE scanning, finding normalization, focused remediation prompts, candidate application in a copied workspace, JavaScript syntax checks, SAST comparison, targeted security tests, and functional tests. Deterministic policy routes a candidate to REJECT, READY_FOR_HUMAN_REVIEW, or NEEDS_HUMAN_ADJUDICATION. The repair model proposes source changes but does not evaluate, approve, or deploy its own patch. Human conclusions are stored separately from automated decisions.'
Add-Paragraph normal 'These choices are deliberate. Three minimal fixtures make vulnerability ground truth, attack behavior, and benign behavior reproducible within the practicum timeline, at the cost of production realism. A fixed model, prompt version, and five calls per CWE hold generation conditions constant while showing within-fixture variation; they do not provide independent application samples or model-to-model comparison. Semgrep supplies one preserved static signal, while targeted runtime and functional checks measure exploit behavior and intended behavior separately. Copied workspaces preserve study inputs but are not security sandboxes. Deterministic policy makes evidence handling repeatable, and a separate human boundary prevents the repair model from approving its own output.'
Add-Paragraph normal 'Deliverables include the prototype, three versioned CWE benchmarks, preserved primary and supplemental evidence, a dashboard and CLI demonstration, reproducibility documentation, and the final presentation and report. The dashboard displays saved evidence; a controlled live replay is labeled separately from the frozen 15-attempt study.'

Add-Paragraph heading 'Completed Tasks (Since Progress Report 2):'
Add-Paragraph list 'Confirmed the historical primary-review checkpoint: all ten original SAST/runtime disagreement reviews are complete. Seven accepted the candidate under the original evidence; three requested additional testing. These reviews were already described in Video II and are background, not work newly completed after the September 13 Report 2 submission.'
Add-Paragraph list 'Predefined and froze supplemental-v1 before candidate execution. It registered 28 cases across three CWEs and separated security, behavioral-parity, and new robustness oracles. Three vulnerable baselines were characterized before the same applicable cases were applied to all 15 saved primary candidates in disposable copies. No new model calls were made.'
Add-Paragraph list 'Recorded 140 supplemental candidate-case observations: security 55 pass, zero fail, five inconclusive; behavioral parity 40 pass, five fail; robustness 25 pass, ten fail. These different categories are not pooled into a security success rate.'
Add-Paragraph list 'Recorded three requested September 15 follow-up rejections for XSS 04, XSS 05, and path-traversal 01. On September 21, I reviewed XSS 01 and 02 against the same frozen missing-input criterion and recorded separate FOLLOW_UP_REJECT_CANDIDATE qualifications. Their original ACCEPT_CANDIDATE records and primary metrics remain unchanged.'
Add-Paragraph list 'Documented limits in the supplement: four XSS candidates changed omitted-name output; traversal 01 rejected a valid in-root filename; all five SQLi candidates missed a newly defined repeated-parameter rule; selected traversal candidates missed new robustness rules. Windows could not create the symlink fixture, so five traversal security observations remain inconclusive rather than passing.'
Add-Paragraph list 'Recorded nine additional September 22 supplemental human results after reviewing the linked patches and registered outcomes. I accepted SQLi 01-05 for the bounded SQL-injection repair because parameterized queries passed every registered security and parity case and returned no broadened rows; SQL-R01 remains a disclosed robustness failure because repeated usernames returned HTTP 200 with an empty array instead of HTTP 400. I requested more testing for traversal 02-05 because symlink-escape protection remains inconclusive; traversal 03 also failed three malformed-input robustness cases and traversal 05 failed the repeated-parameter case. These records do not alter frozen primary evidence or registered outcomes.'
Add-Paragraph list 'Improved verification portability after an old-checkout absolute path prevented supplemental verification here. The verifier checks the registered source in the active checkout with matching hashes. On September 22, 119 automated tests passed; primary evidence verified 15/15 attempts and 10/10 original reviews; supplemental evidence verified three baselines and 15 candidates; and all 14 supplemental human packet/result bindings verified: five rejections, five bounded acceptances, and four requests for more testing.'
Add-Paragraph list 'Generated and inspected the 15-candidate evidence appendix. Its primary and supplemental matrices preserve the original automated states, registered failures and inconclusive cases, all 14 later human decisions, and complete recorded rationales. It is a backup reference for Video III rather than a replacement for the report narrative.'
Add-Paragraph list 'Reviewed repository structure, documentation, test-code snippets and saved results, and supplied human rationales. Video II was posted; Video II peer feedback remains in progress and is separate from this project evaluation.'
Add-Paragraph normal 'Reporting checkpoint: September 14-23, 2026, following the September 13 Report 2 submission. I estimate 1.5 hours per day for ten days, approximately 15 hours, spent mainly reviewing the file structure and documentation, validating test and saved-evidence results, reviewing candidate patches and code snippets, supplying human-review rationales, and aligning the report with the professor''s feedback. This is my estimate, not a number inferred from commits or automated test time. Earlier reports recorded 31.5 hours plus a separate 13.5-hour September 2-10 period. The documented subtotal is approximately 60 hours plus any September 11-13 work not included in Report 2. Reconcile those dates and update this paragraph through the actual Report 3 cutoff before submitting.'

Add-Paragraph heading 'Tasks for the Next Project Report:'
Add-Paragraph list 'Complete the Video II peer-feedback assignment by September 27, separately from Report 3, and retain the submission receipt.'
Add-Paragraph list 'Finalize Report 3 for the planned October 1 submission: reconcile actual dates and hours, confirm the live Canvas deadline, check each metric and cited source, complete the AI-use disclosure, transfer the draft into the course template, and inspect the rendered file before submitting.'
Add-Paragraph list 'Expand the related-work comparison across benchmark type, repair model, validation oracle, retries, success criteria, and limits. Draft final-paper methods and results with the primary, pilot/control, and supplemental evidence clearly separated.'
Add-Paragraph list 'Prepare Video III using one saved primary candidate and its supplemental comparison. Explain XSS 03 versus XSS 04 or the later XSS 01-02 qualifications, then rehearse a bounded pilot replay without calling it a rerun of the primary study.'
Add-Paragraph list 'Decide whether to retain the symlink limitation or conduct a separately dated run on a capable environment. Before final delivery, extend the clean-archive checklist to verify supplemental evidence and all 14 human-record bindings as well as primary evidence.'
Add-Paragraph list 'Create a clean versioned release snapshot before the final demonstration. Exclude local dependencies, caches, generated logs, and secrets; then rerun the primary, supplemental, human-record, and full automated checks from the packaged copy.'

Add-Paragraph heading 'Questions I Have or Issues I Am Running Into:'
Add-Paragraph normal 'The central issue is interpretation across evidence collected at different times. The original XSS 01-02 acceptances reflected the primary suite, but later XSS-P01 showed the same omitted-name parity failure as rejected XSS 04-05. I applied the frozen criterion consistently through separate later rejections; I did not rewrite the original decisions. A passing registered XSS attack suite does not establish full behavioral preservation.'
Add-Paragraph normal 'The path-traversal symlink case could not execute on this Windows environment, leaving five security observations inconclusive. I therefore recorded requests for more testing rather than claiming symlink-safe traversal protection for attempts 02-05. Traversal 03 additionally failed three robustness contracts, and traversal 05 failed the repeated-parameter contract. One fixture per CWE and five repair attempts per fixture limit application diversity. Remote Semgrep rule provenance, targeted test coverage, same-host reproducibility, and lack of production performance testing further limit generalization. The five SQLi automated READY_FOR_HUMAN_REVIEW states were not automatic approvals; my September 22 bounded acceptances are separate human records and preserve the failed SQL-R01 outcomes.'
Add-Paragraph normal 'Feedback requested: Is this three-fixture, category-separated supplemental evaluation sufficient for the practicum scope? Would an independent second reviewer for selected disagreements add more useful evidence than broadening to another CWE?'

Add-Paragraph heading 'Methodology Paragraph Summary:'
Add-Paragraph normal 'Each controlled fixture defines an attacker-controlled input, target route and vulnerable operation, synthetic data, baseline attack behavior, and benign-behavior expectations. The frozen primary protocol uses five separate initial repair calls per CWE under a fixed model and prompt, with evaluator ground truth and test implementations withheld from the repair prompt. The same saved candidates receive syntax, Semgrep, targeted HTTP/browser security, and functional checks. SAST-only interpretation and deterministic multi-stage policy are compared on those same candidates. Primary attempts, pilot retries, the non-AI false-success control, lifecycle replay, and supplemental tests have separate denominators.'
Add-Paragraph normal 'The 15 scheduled calls are experimental attempts, not 15 independent applications or 15 unique patches. The five SQLi calls produced identical candidate source, while XSS and path traversal each produced five distinct candidate sources. This duplication is preserved as an observed model outcome and prevents the repeated SQLi code from being presented as five independent implementations.'
Add-Paragraph normal 'The supplemental protocol was fixed before execution and compares each candidate with its baseline using registered security, behavioral-parity, and robustness oracles. XSS browser observations distinguish displayed text from payload execution. Inconclusive execution is not a pass. The design favors traceability and explicit decision boundaries over broad corpus realism; repeated repairs on one fixture are not independent applications.'
Add-Paragraph normal 'Pearce et al. (2022) motivates treating generated code as untrusted. Pearce et al. (2023) studies multi-model zero-shot repair and reports functional-correctness challenges. Kulsum et al. (2024) uses external compiler, sanitizer, and test feedback for iterative repair; FixProof does not claim validation feedback is new. Its bounded contribution is the auditable combination of stage-level evidence, deterministic disposition, and preserved human qualifications for three Express weaknesses. Datasets and success definitions differ, so cross-study success rates are not directly comparable.'

Add-Paragraph heading 'Timeline:'
Add-Paragraph normal 'This is the current plan, not a claim that future work has already occurred. Dates follow the supplied course schedule and must be checked in live Canvas. The September 22 draft is a checkpoint for Report 3, not its final reporting cutoff.'
$timelineRows = @(
    ,@('When', 'Description of Task', 'Status')
    ,@('Aug-Sep', 'Define problem, build three-CWE prototype and pilot, freeze primary protocol', 'Completed')
    ,@('Sep 4', 'Collect and verify 15 initial primary attempts', 'Completed')
    ,@('Sep 12-13', 'Complete original conflict reviews and post Video II', 'Completed')
    ,@('Sep 14-15', 'Freeze supplemental protocol, run three baselines and 15 saved candidates, record three requested follow-ups', 'Completed')
    ,@('Sep 21', 'Record XSS 01-02 consistency qualifications; historical checkpoint reached 116 tests', 'Completed')
    ,@('Sep 22', 'Record nine SQLi/traversal decisions; verify 119 tests and all 14 follow-up records', 'Completed')
    ,@('Sep 23', 'Complete the evidence appendix and align Report 3 with the professor''s benchmark and design-rationale feedback', 'Completed')
    ,@('September 27', 'Submit Video II peer feedback', 'In progress')
    ,@('October 1', 'Planned Progress Report 3 submission with actual effort and verified claims; confirm live Canvas deadline', 'Planned')
    ,@('October 6 / 11', 'Post Video III and submit peer feedback', 'Planned')
    ,@('October 18 / 20 / 25', 'Progress Report 4, Video IV, peer feedback; deepen related work and reproducibility', 'Planned')
    ,@('November 1 / 3 / 8', 'Progress Report 5, Video V, peer feedback; settle final results and rehearse', 'Planned')
    ,@('November 15', 'Submit final presentation video, no more than 15 minutes', 'Planned')
    ,@('November 22', 'Submit peer feedback on final presentation', 'Planned')
    ,@('December 6', 'Submit final project report and reproducible package', 'Planned')
)
Add-Table timeline $timelineRows

Add-Paragraph heading 'Evaluation:'
Add-Paragraph normal 'All 15 frozen primary initial attempts have complete evidence. The denominator excludes pilot retries and the constructed non-AI control. Original human conflict reviews are 10/10 complete: seven accepts under the original evidence and three requests for additional testing. Later follow-up verdicts are recorded separately.'
$primaryRows = @(
    ,@('Primary case', 'Initial attempts', 'Target SAST resolved', 'Security pass', 'Functional pass', 'Automated decision')
    ,@('Reflected XSS', '5', '0/5', '5/5', '5/5', '5 need adjudication')
    ,@('SQL injection', '5', '5/5', '5/5', '5/5', '5 ready for review')
    ,@('Path traversal', '5', '0/5', '5/5', '5/5', '5 need adjudication')
    ,@('Total', '15', '5/15', '15/15', '15/15', '5 ready; 10 conflicts')
)
Add-Table evaluation $primaryRows
Add-Paragraph normal 'Primary target-SAST resolution was 5/15 (33.3%); SAST/runtime disagreement was 10/15 (66.7%). No primary SAST false success was observed. That absence is not evidence of a general detection rate or production security. The separate pilot caught a functional regression; the constructed non-AI control exercises the false-success policy branch without entering AI-attempt metrics.'
Add-Paragraph normal 'The primary schedule contains 15 model calls, but candidate-source diversity was five XSS sources, one SQLi source, and five path-traversal sources. The five SQLi attempts are retained as five calls under the protocol, while their identical code is disclosed rather than counted as five unique solutions.'
Add-Paragraph normal 'The supplemental study evaluated the same 15 saved candidates against registered cases after baseline characterization. Its categories and denominators are separate from the primary study:'
$supplementalRows = @(
    ,@('Category', 'Observations', 'Pass', 'Fail', 'Inconclusive', 'Meaning')
    ,@('Security', '60', '55', '0', '5', 'Symlink unavailable for five traversal candidates')
    ,@('Behavioral parity', '45', '40', '5', '0', 'Four XSS missing-input changes; one traversal valid-file rejection')
    ,@('Robustness', '35', '25', '10', '0', 'New SQLi and traversal input-handling contracts')
    ,@('Total', '140', '120', '15', '5', 'Mixed categories; not one security success rate')
)
Add-Table evaluation $supplementalRows
Add-Paragraph normal 'My nine September 22 recorded decisions separate security repair from full supplemental conformance. I accepted SQLi 01-05 for the bounded tested injection repair because parameterized queries passed 3/3 supplemental security and 2/2 parity cases and returned no unauthorized rows. SQL-R01 still failed: repeated username parameters returned HTTP 200 with an empty array instead of the registered HTTP 400 response. I treat that as a disclosed, low-impact robustness limitation rather than evidence that SQL injection remained exploitable. For traversal attempts 02-05, I recorded requests for more testing because PATH-S06 was inconclusive and the lexical path checks do not establish symlink-target containment. Traversal 03 and 05 also retain their recorded robustness failures. These judgments do not relabel failed or inconclusive cases and do not overwrite the original reviews.'
Add-Paragraph normal 'For a compact example, XSS 03 and XSS 04 both passed all three supplemental security cases, but XSS 03 passed all five behavioral-parity cases while XSS 04 passed four of five. XSS 04 changed an omitted name from the baseline visible text Hello undefined to Hello. The frozen XSS-P01 criterion supported a follow-up rejection, not a claim that the tested XSS attacks remained exploitable. The same later criterion led Tony to reject XSS 01 and 02 in separate September 21 qualifications while preserving their original acceptances.'

Add-Paragraph heading 'Report Outline:'
Add-Paragraph normal '1. Problem, motivation, and research question.'
Add-Paragraph normal '2. Related work, alternatives, and specific contribution.'
Add-Paragraph normal '3. Controlled scope, threat model, and benchmark construction.'
Add-Paragraph normal '4. Architecture, model authority, validators, decision policy, and human boundary.'
Add-Paragraph normal '5. Frozen primary method, comparator, provenance, and reproducibility.'
Add-Paragraph normal '6. Primary results, separate pilot/control examples, and original human reviews.'
Add-Paragraph normal '7. Supplemental methods/results, later qualifications, limitations, and delivery feasibility.'
Add-Paragraph normal '8. Conclusion, references, evidence index, and AI-use disclosure.'

Add-Paragraph heading 'References:'
Add-Paragraph normal 'Pearce, H., Ahmad, B., Tan, B., Dolan-Gavitt, B., & Karri, R. (2022). Asleep at the keyboard? Assessing the security of GitHub Copilot''s code contributions. 2022 IEEE Symposium on Security and Privacy. https://doi.org/10.1109/SP46214.2022.9833571'
Add-Paragraph normal 'Pearce, H., Tan, B., Ahmad, B., Karri, R., & Dolan-Gavitt, B. (2023). Examining zero-shot vulnerability repair with large language models. 2023 IEEE Symposium on Security and Privacy. https://doi.org/10.1109/SP46215.2023.10179324'
Add-Paragraph normal 'Kulsum, U., Zhu, H., Xu, B., & d''Amorim, M. (2024). A case study of LLM for automated vulnerability repair: Assessing impact of reasoning and patch validation feedback. Proceedings of the 1st ACM International Conference on AI-Powered Software. https://doi.org/10.1145/3664646.3664770'
Add-Paragraph normal 'OWASP Foundation. (n.d.). Web Security Testing Guide, version 4.2. https://wstg.owasp.org/v4.2/'
Add-Paragraph normal 'Semgrep. (n.d.). Run rules. https://semgrep.dev/docs/running-rules'

Add-Paragraph heading 'Appendix:'
Add-Paragraph normal 'Evidence index: docs/study-protocol-v1.md and benchmarks/primary/v1/ define the frozen primary study; data/primary_trials/v1/ and data/primary_reviews/v1/ preserve candidates and original reviews; data/evaluation/primary-report.json provides the verified primary report. docs/supplemental-protocol-v1.md, data/supplemental/v1/, and docs/supplemental-results-v1.md preserve the later protocol, observations, and 14 recorded human results. The September 22 review worksheet links the evidence used for the nine newest records. docs/README.md separates current references from historical drafts.'
Add-Paragraph normal 'Verification: the full suite passed 119 automated tests in the September 23 accuracy review. The primary report verified 15/15 attempts and 10/10 original reviews; the supplemental report verified three baselines and 15 saved candidates; and the human-record verifier confirmed 14/14 completed records. Four guided pilot live replays previously matched their recorded decisions. Saved-evidence verification does not repeat model calls or every historical scanner/browser experiment. A clean committed-archive rehearsal remains to be completed before final delivery.'
Add-Paragraph normal 'Generative AI disclosure: OpenAI ChatGPT/Codex assisted planning, implementation, debugging, test orchestration, documentation, evidence organization, and drafting. FixProof separately used the OpenAI API to generate recorded repair candidates. Tony Tran remains responsible for verifying claims and references, reporting actual effort, making human review decisions, and approving submitted text. Reconcile this statement with actual tool use and course disclosure requirements before submission.'

[void]$body.AppendChild($sectionProperties)
$outputDirectory = Split-Path -Parent $target
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}
Copy-Item -LiteralPath $source -Destination $target -Force
$archive = [IO.Compression.ZipFile]::Open($target, [IO.Compression.ZipArchiveMode]::Update)
try {
    $oldEntry = $archive.GetEntry('word/document.xml')
    $oldEntry.Delete()
    $newEntry = $archive.CreateEntry('word/document.xml', [IO.Compression.CompressionLevel]::Optimal)
    $stream = $newEntry.Open()
    $writer = [IO.StreamWriter]::new($stream, [Text.UTF8Encoding]::new($false))
    try { $doc.Save($writer) } finally { $writer.Dispose() }
} finally {
    $archive.Dispose()
}

Write-Output "Created Report 3 working DOCX: $target"
