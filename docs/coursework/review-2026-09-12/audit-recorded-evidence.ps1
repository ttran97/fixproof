param([string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path)
$ErrorActionPreference = 'Stop'
$issues = [Collections.Generic.List[string]]::new()
$checks = [Collections.Generic.List[object]]::new()
function Read-Json([string]$path) { Get-Content -LiteralPath (Join-Path $ProjectRoot $path) -Raw -Encoding UTF8 | ConvertFrom-Json }
function Check-Binding($binding, [string]$category) {
    $path = [IO.Path]::GetFullPath((Join-Path $ProjectRoot $binding.path))
    if (-not $path.StartsWith($ProjectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Evidence path outside repository' }
    $actual = if (Test-Path -LiteralPath $path -PathType Leaf) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() } else { 'missing' }
    $ok = $actual -eq $binding.sha256
    $checks.Add([ordered]@{category=$category; path=$binding.path; matches=$ok})
    if (-not $ok) { $issues.Add("$category hash mismatch: $($binding.path)") }
}
$report = Read-Json 'data/evaluation/primary-report.json'
$manifest = Read-Json 'data/primary_trials/v1/primary-experiment-manifest.json'
foreach ($b in $report.evidence_bindings) { Check-Binding $b 'report_evidence' }
Check-Binding $report.manifest 'report_manifest'
foreach ($b in $manifest.implementation_files.PSObject.Properties) { Check-Binding @{path=$b.Name;sha256=$b.Value} 'frozen_implementation' }
$plan = Read-Json 'data/evaluation/trial-plan.json'
foreach ($b in $plan.freeze_evidence.PSObject.Properties) { if ($b.Value.sha256) { Check-Binding $b.Value 'frozen_input' } }
$rows = @()
$dates = @()
foreach ($slot in $manifest.attempts) {
    $folder = 'data/primary_trials/v1/cases/{0}/attempt-{1:00}' -f $slot.case_id,[int]$slot.attempt
    $a = Read-Json "$folder/attempt.json"
    foreach ($b in $a.artifacts.PSObject.Properties) { Check-Binding $b.Value 'attempt_artifact' }
    if ($a.status -ne 'completed' -or $a.trial_id -ne $slot.trial_id) { $issues.Add("Incomplete/wrong slot: $folder") }
    $d = (Read-Json "$folder/decision.json").decision
    $s = (Read-Json "$folder/security.json").security_validation
    $f = (Read-Json "$folder/functional.json").functional_validation
    $e = $d.evidence
    $expected = if ($e.syntax -ne 'pass' -or $e.new_sast_findings -gt 0 -or $s.status -ne 'pass' -or $f.status -ne 'pass') { 'REJECT' } elseif ($e.target_sast -eq 'resolved') { 'READY_FOR_HUMAN_REVIEW' } elseif ($e.target_sast -eq 'persistent') { 'NEEDS_HUMAN_ADJUDICATION' } else { 'REJECT' }
    if ($d.disposition -ne $expected -or $a.disposition -ne $expected) { $issues.Add("Decision mismatch: $folder") }
    $w = (Read-Json "$folder/workspace/$($a.canonical_id)/attempt-$('{0:00}' -f [int]$a.attempt)/workspace.json").patch_workspace
    $hashFields = @{original_source='original_source_sha256';workspace_source='candidate_source_sha256';patch_file='patch_sha256'}
    foreach ($field in $hashFields.Keys) {
        $portable = $w.$field.Replace('\','/') -replace '^.*?/fixproof/',''
        $content = [IO.File]::ReadAllText((Join-Path $ProjectRoot $portable)).Replace("`r`n","`n").Replace("`r","`n")
        $sha = [Security.Cryptography.SHA256]::Create()
        $hash = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($content)))).Replace('-','').ToLowerInvariant()
        $sha.Dispose()
        $ok = $hash -eq $w.hashes.($hashFields[$field])
        $checks.Add([ordered]@{category='workspace_normalized_text';path=$portable;matches=$ok})
        if (-not $ok) { $issues.Add("Workspace text hash mismatch: $portable") }
    }
    $dates += @($a.history | Where-Object status -eq 'completed' | ForEach-Object recorded_at)
    $rows += [ordered]@{trial=$a.trial_id;case=$a.case_id;target_sast=$e.target_sast;security=$s.status;functional=$f.status;new_findings=$e.new_sast_findings;decision=$expected;source_hash=$w.hashes.candidate_source_sha256;response_id=$a.response_id}
}
$reviews = @()
foreach ($file in Get-ChildItem (Join-Path $ProjectRoot 'data/primary_reviews/v1') -Recurse -Filter result.json) {
    $result = (Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json).adjudication_result
    Check-Binding $result.packet_binding 'review_packet'
    $packet = (Read-Json $result.packet_binding.path).adjudication_packet
    foreach ($b in $packet.evidence_binding.artifacts.PSObject.Properties) { Check-Binding $b.Value 'review_evidence' }
    $reviews += [ordered]@{case=$result.case_id;attempt=$result.attempt;verdict=$result.verdict;reviewed_at=$result.reviewed_at;reviewer=$result.reviewer}
}
$summary = [ordered]@{
    audit_date='2026-09-12'; mode='PowerShell saved-artifact hash checks and decision/count consistency; no Python/scanner/model/runtime execution'
    commit=(& git -C $ProjectRoot rev-parse HEAD); scheduled=$manifest.attempts.Count; completed=$rows.Count
    target_resolved=@($rows | Where-Object target_sast -eq resolved).Count
    security_pass=@($rows | Where-Object security -eq pass).Count
    functional_pass=@($rows | Where-Object functional -eq pass).Count
    ready=@($rows | Where-Object decision -eq READY_FOR_HUMAN_REVIEW).Count
    disagreements=@($rows | Where-Object decision -eq NEEDS_HUMAN_ADJUDICATION).Count
    false_successes=@($rows | Where-Object { $_.target_sast -eq 'resolved' -and $_.decision -eq 'REJECT' }).Count
    candidates_with_new_findings=@($rows | Where-Object new_findings -gt 0).Count
    unique_candidate_sources=@($rows.source_hash | Sort-Object -Unique).Count
    unique_response_ids=@($rows.response_id | Sort-Object -Unique).Count
    review_results=$reviews.Count; first_completed_utc=($dates | Sort-Object | Select-Object -First 1); last_completed_utc=($dates | Sort-Object | Select-Object -Last 1)
    issues=@($issues); checks=@($checks); trials=$rows; reviews=$reviews
    limitations=@('Not the full Python primary-report verifier; scanner normalization, prompt reconstruction, baseline runtime and lifecycle ledger were not re-executed.','Hashes establish agreement with saved bindings, not authenticity, security completeness, or personal review quality.','Historical report of 89 tests passing was not rerun in this environment.')
}
$summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'recorded-evidence-audit.json') -Encoding UTF8
$checks | ForEach-Object { [pscustomobject]$_ } | Group-Object category | Select-Object Name,Count | Format-Table
[pscustomobject]$summary | Select-Object scheduled,completed,target_resolved,security_pass,functional_pass,ready,disagreements,false_successes,unique_candidate_sources,review_results,first_completed_utc,last_completed_utc | Format-List
if ($issues.Count) { $issues; throw 'Audit mismatches found' }
Write-Output 'All recorded hash and decision/count checks passed.'
