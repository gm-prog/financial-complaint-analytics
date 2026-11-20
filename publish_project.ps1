[CmdletBinding()]
param(
    [ValidateSet('public', 'private')]
    [string]$Visibility = 'public',
    [string]$RepositoryName = 'financial-complaint-analytics',
    [switch]$IncludePowerBI
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "`n=== Financial Complaint Analytics: GitHub publish ===" -ForegroundColor Cyan
Write-Host "Project folder: $ProjectRoot"

# Search only likely user folders for the previously saved PBIX.
$searchRoots = @(
    (Join-Path $env:USERPROFILE 'Desktop'),
    (Join-Path $env:USERPROFILE 'Documents'),
    (Join-Path $env:USERPROFILE 'Downloads'),
    (Join-Path $env:USERPROFILE 'OneDrive'),
    (Join-Path $env:USERPROFILE 'OneDrive\Desktop'),
    (Join-Path $env:USERPROFILE 'OneDrive\Documents')
) | Select-Object -Unique | Where-Object { Test-Path $_ }

$pbixCandidates = @()
foreach ($root in $searchRoots) {
    try {
        $pbixCandidates += Get-ChildItem -Path $root -Filter '*.pbix' -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match 'Complaint|Analytics' }
    } catch { }
}
$pbixCandidates = $pbixCandidates | Sort-Object LastWriteTime -Descending -Unique
if ($pbixCandidates.Count -gt 0) {
    $pbix = $pbixCandidates | Select-Object -First 1
    $pbixDestination = Join-Path $ProjectRoot 'powerbi\ComplaintAnalytics_Backup.pbix'
    Copy-Item -LiteralPath $pbix.FullName -Destination $pbixDestination -Force
    Write-Host "Found and copied Power BI file: $($pbix.FullName)" -ForegroundColor Green
    Write-Host 'PBIX remains local-only unless -IncludePowerBI is supplied.' -ForegroundColor Yellow
} else {
    Write-Host 'No Complaint/Analytics PBIX was found in Desktop, Documents, Downloads, or OneDrive.' -ForegroundColor Yellow
    Write-Host 'The repository can still be created. Copy the final PBIX into .\powerbi\ later.'
}

$git = Get-Command git -ErrorAction SilentlyContinue
$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $git) {
    throw "Git for Windows is not available in this PowerShell session. Install it with: winget install --id Git.Git -e. Reopen PowerShell and rerun this script."
}
if (-not $gh) {
    throw "GitHub CLI is not available. Install it with: winget install --id GitHub.cli -e. Reopen PowerShell and rerun this script."
}

Write-Host "`nChecking GitHub CLI authentication..." -ForegroundColor Cyan
gh auth status
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub CLI is not authenticated. Run: gh auth login  then rerun this script.'
}

$owner = (gh api user --jq .login).Trim()
if (-not $owner) { throw 'Could not read the authenticated GitHub username.' }
$repoFullName = "$owner/$RepositoryName"
$repoUrl = "https://github.com/$repoFullName"

if (-not (Test-Path (Join-Path $ProjectRoot '.git'))) {
    git init -b main
    if ($LASTEXITCODE -ne 0) { throw 'git init failed.' }
}

# Set a local commit identity only if Git has none configured.
$gitName = git config user.name
if (-not $gitName) { git config user.name $owner }
$gitEmail = git config user.email
if (-not $gitEmail) {
    $githubId = (gh api user --jq .id).Trim()
    git config user.email "$githubId+$owner@users.noreply.github.com"
}

if ($IncludePowerBI) {
    $pbixFiles = Get-ChildItem -Path (Join-Path $ProjectRoot 'powerbi') -Filter '*.pbix' -File -ErrorAction SilentlyContinue
    if (-not $pbixFiles) { throw 'IncludePowerBI was requested, but no PBIX exists in .\powerbi\.' }
    foreach ($file in $pbixFiles) {
        if ($file.Length -ge 100MB) {
            throw "PBIX is $([math]::Round($file.Length/1MB,1)) MB. GitHub regular files must be under 100 MB; do not force-add it. Use Git LFS or share the PBIX separately."
        }
        git add -f -- $file.FullName
        if ($LASTEXITCODE -ne 0) { throw "Could not stage PBIX $($file.Name)." }
    }
    Write-Host 'PBIX explicitly staged for publication. Confirm you have permission to publish embedded data.' -ForegroundColor Yellow
}

git add -A
if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }
$hasStagedChanges = $false
git diff --cached --quiet
if ($LASTEXITCODE -eq 1) { $hasStagedChanges = $true }
if ($hasStagedChanges) {
    git commit -m 'Add financial complaint analytics internship project'
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed.' }
} else {
    Write-Host 'No new local changes to commit.'
}

# Create a fresh GitHub repository when it does not already exist.
$existingUrl = $null
try { $existingUrl = gh repo view $repoFullName --json url --jq .url 2>$null } catch { $existingUrl = $null }
if ($LASTEXITCODE -eq 0 -and $existingUrl) {
    Write-Host "Repository already exists: $existingUrl" -ForegroundColor Yellow
    $origin = git remote get-url origin 2>$null
    if (-not $origin) {
        git remote add origin "https://github.com/$repoFullName.git"
        if ($LASTEXITCODE -ne 0) { throw 'Could not set origin remote.' }
    } elseif ($origin -notmatch [regex]::Escape($repoFullName)) {
        throw "An origin remote already exists ($origin) and does not match $repoFullName. Review it manually; no remote was overwritten."
    }
    git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw 'Push failed. The remote may contain unrelated commits; inspect before retrying.' }
} else {
    $visibilityFlag = "--$Visibility"
    gh repo create $repoFullName $visibilityFlag --source . --remote origin --push
    if ($LASTEXITCODE -ne 0) { throw 'GitHub repository creation/push failed.' }
}

Write-Host "`nSUCCESS: $repoUrl" -ForegroundColor Green
Write-Host "Visibility: $Visibility"
Write-Host 'Raw CSVs and PBIX remain excluded by default. SQL scripts were not fabricated.'
Write-Host 'Copy the GitHub URL above into the internship portal after opening it in a browser.'
