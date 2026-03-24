param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$passes = [System.Collections.Generic.List[string]]::new()
$errors = [System.Collections.Generic.List[string]]::new()

function Add-Pass {
    param([string]$Message)
    $passes.Add($Message)
}

function Add-Error {
    param([string]$Message)
    $errors.Add($Message)
}

function Parse-Frontmatter {
    param([string]$Path)

    $content = Get-Content -Raw -Path $Path
    if ($content -notmatch '(?s)^---\r?\n(.*?)\r?\n---') {
        throw "Missing YAML frontmatter: $Path"
    }

    $result = @{}
    foreach ($line in ($Matches[1] -split "\r?\n")) {
        if ($line -match '^\s*([^:#]+):\s*(.+?)\s*$') {
            $result[$Matches[1].Trim()] = $Matches[2].Trim().Trim("'`"")
        }
    }

    return $result
}

function Split-ListField {
    param([string]$Value)

    if (-not $Value) {
        return @()
    }

    return @(
        $Value.Split(",") |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -ne "" }
    )
}

$requiredPaths = @(
    "CLAUDE.md",
    "README.md",
    "lessons.md",
    "validation-report.md",
    ".claude\settings.json",
    ".claude\commands",
    ".claude\skills",
    ".claude\rules\constraints.md",
    ".claude\scripts\validate-workflow.ps1",
    ".claude\scripts\smoke-test-workflow.ps1",
    ".claude\contracts\command.schema.json",
    ".claude\contracts\lesson-entry.schema.json",
    ".claude\contracts\validation-report.schema.json",
    ".claude\contracts\review-finding.schema.json"
)

foreach ($relativePath in $requiredPaths) {
    $fullPath = Join-Path $Root $relativePath
    if (Test-Path $fullPath) {
        Add-Pass "Found $relativePath"
    }
    else {
        Add-Error "Missing required path: $relativePath"
    }
}

$settingsPath = Join-Path $Root ".claude\settings.json"
$settings = $null
try {
    $settings = Get-Content -Raw -Path $settingsPath | ConvertFrom-Json
    Add-Pass "Parsed .claude/settings.json"
}
catch {
    Add-Error "Invalid JSON in .claude/settings.json: $($_.Exception.Message)"
}

$registeredCommands = @{}
$registeredSkills = @{}

if ($settings -and $settings.commands) {
    foreach ($prop in $settings.commands.PSObject.Properties) {
        $registeredCommands[$prop.Name] = $prop.Value.file
        $target = Join-Path $Root $prop.Value.file
        if (Test-Path $target) {
            Add-Pass "Registered command '$($prop.Name)' points to an existing file"
        }
        else {
            Add-Error "Registered command '$($prop.Name)' points to a missing file: $($prop.Value.file)"
        }
    }
}

if ($settings -and $settings.skills) {
    foreach ($prop in $settings.skills.PSObject.Properties) {
        $registeredSkills[$prop.Name] = $prop.Value.file
        $target = Join-Path $Root $prop.Value.file
        if (Test-Path $target) {
            Add-Pass "Registered skill '$($prop.Name)' points to an existing file"
        }
        else {
            Add-Error "Registered skill '$($prop.Name)' points to a missing file: $($prop.Value.file)"
        }
    }
}

$internalSkills = @{}
$skillDirs = Get-ChildItem -Path (Join-Path $Root ".claude\skills") -Directory | Sort-Object Name
foreach ($dir in $skillDirs) {
    $skillPath = Join-Path $dir.FullName "SKILL.md"
    if (-not (Test-Path $skillPath)) {
        Add-Error "Skill directory '$($dir.Name)' is missing SKILL.md"
        continue
    }

    try {
        $frontmatter = Parse-Frontmatter -Path $skillPath
        foreach ($requiredField in @("name", "description", "version")) {
            if ($frontmatter.ContainsKey($requiredField) -and $frontmatter[$requiredField]) {
                Add-Pass "Skill '$($dir.Name)' includes frontmatter field '$requiredField'"
            }
            else {
                Add-Error "Skill '$($dir.Name)' is missing frontmatter field '$requiredField'"
            }
        }

        if ($frontmatter.ContainsKey("internal") -and $frontmatter["internal"].ToLower() -eq "true") {
            $internalSkills[$dir.Name] = $true
            if ($frontmatter.ContainsKey("name")) {
                $internalSkills[$frontmatter["name"]] = $true
            }
            Add-Pass "Internal support skill '$($dir.Name)' is explicitly marked internal"
        }
        elseif ($registeredSkills.Values -contains ".claude/skills/$($dir.Name)/SKILL.md") {
            Add-Pass "Skill '$($dir.Name)' is registered in settings.json"
        }
        else {
            Add-Error "Skill '$($dir.Name)' exists on disk but is not registered in settings.json"
        }
    }
    catch {
        Add-Error $_.Exception.Message
    }
}

# Reject .json command files (must be Markdown)
$jsonCommandFiles = Get-ChildItem -Path (Join-Path $Root ".claude\commands") -Filter *.json -File -ErrorAction SilentlyContinue
foreach ($jf in $jsonCommandFiles) {
    Add-Error "Command '$($jf.Name)' uses JSON format; commands MUST be Markdown (.md)"
}
if (-not $jsonCommandFiles -or $jsonCommandFiles.Count -eq 0) {
    Add-Pass "No JSON command files found (all commands use Markdown)"
}

$commandFiles = Get-ChildItem -Path (Join-Path $Root ".claude\commands") -Filter *.md -File | Sort-Object Name
foreach ($file in $commandFiles) {
    $relative = ".claude/commands/$($file.Name)"
    $content = Get-Content -Raw -Path $file.FullName

    if ($content -match '(?m)^## Usage\s*$') {
        Add-Pass "Command '$($file.Name)' has a Usage section"
    }
    else {
        Add-Error "Command '$($file.Name)' is missing a Usage section"
    }

    if ($content -match '(?m)^## Stage \d+:') {
        Add-Pass "Command '$($file.Name)' uses staged structure"
    }
    else {
        Add-Error "Command '$($file.Name)' is missing numbered stages"
    }

    if (($content -match '\*\*Goal\*\*:') -and ($content -match '\*\*Verify\*\*:')) {
        Add-Pass "Command '$($file.Name)' defines Goal and Verify"
    }
    else {
        Add-Error "Command '$($file.Name)' is missing Goal or Verify"
    }

    if ($registeredCommands.Values -contains $relative) {
        Add-Pass "Command '$($file.Name)' is registered in settings.json"
    }
    else {
        Add-Error "Command '$($file.Name)' exists on disk but is not registered in settings.json"
    }

    try {
        $frontmatter = Parse-Frontmatter -Path $file.FullName
        foreach ($requiredField in @("name", "purpose", "inputs", "outputs", "gates", "depends_on", "writes_to")) {
            if ($frontmatter.ContainsKey($requiredField) -and $frontmatter[$requiredField]) {
                Add-Pass "Command '$($file.Name)' includes metadata field '$requiredField'"
            }
            else {
                Add-Error "Command '$($file.Name)' is missing metadata field '$requiredField'"
            }
        }

        $expectedName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        if ($frontmatter["name"] -eq $expectedName) {
            Add-Pass "Command '$($file.Name)' metadata name matches file name"
        }
        else {
            Add-Error "Command '$($file.Name)' metadata name '$($frontmatter["name"])' does not match file name '$expectedName'"
        }

        foreach ($dependency in (Split-ListField -Value $frontmatter["depends_on"])) {
            if ($registeredSkills.ContainsKey($dependency) -or $internalSkills.ContainsKey($dependency)) {
                Add-Pass "Command '$($file.Name)' dependency '$dependency' resolves to a known skill"
            }
            else {
                Add-Error "Command '$($file.Name)' depends on unknown skill '$dependency'"
            }
        }

        foreach ($target in (Split-ListField -Value $frontmatter["writes_to"])) {
            # Skip variable-based paths (e.g. $OUTPUT_DIR/...) — resolved at runtime
            if ($target -match '^\$') {
                Add-Pass "Command '$($file.Name)' write target '$target' uses runtime variable (skipped)"
                continue
            }
            $fullTarget = Join-Path $Root $target
            $parent = Split-Path -Parent $fullTarget
            if ($parent -and (Test-Path $parent)) {
                Add-Pass "Command '$($file.Name)' write target '$target' has an existing parent path"
            }
            else {
                Add-Error "Command '$($file.Name)' write target '$target' does not have an existing parent path"
            }
        }
    }
    catch {
        Add-Error $_.Exception.Message
    }
}

$constraintsPath = Join-Path $Root ".claude\rules\constraints.md"
if (Test-Path $constraintsPath) {
    $constraintsContent = Get-Content -Raw -Path $constraintsPath
    if (($constraintsContent -match 'ALWAYS') -and ($constraintsContent -match 'NEVER')) {
        Add-Pass "constraints.md includes BOTH ALWAYS and NEVER rules"
    }
    else {
        Add-Error "constraints.md must include BOTH ALWAYS and NEVER rules"
    }
}

Write-Host "Workflow validation summary"
Write-Host "PASS: $($passes.Count)"
foreach ($item in $passes) {
    Write-Host "  [PASS] $item"
}

Write-Host "FAIL: $($errors.Count)"
foreach ($item in $errors) {
    Write-Host "  [FAIL] $item"
}

if ($errors.Count -gt 0) {
    exit 1
}

exit 0
