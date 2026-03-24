param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

$settings = Get-Content -Raw -Path (Join-Path $Root ".claude\settings.json") | ConvertFrom-Json
$registeredSkills = @{}
foreach ($prop in $settings.skills.PSObject.Properties) {
    $registeredSkills[$prop.Name] = $true
}

$internalSkills = @{}
Get-ChildItem -Path (Join-Path $Root ".claude\skills") -Directory | ForEach-Object {
    $skillPath = Join-Path $_.FullName "SKILL.md"
    if (Test-Path $skillPath) {
        $frontmatter = Parse-Frontmatter -Path $skillPath
        if ($frontmatter.ContainsKey("internal") -and $frontmatter["internal"].ToLower() -eq "true") {
            $internalSkills[$_.Name] = $true
            if ($frontmatter.ContainsKey("name")) {
                $internalSkills[$frontmatter["name"]] = $true
            }
        }
    }
}

$checked = 0
Get-ChildItem -Path (Join-Path $Root ".claude\commands") -Filter *.md -File | Sort-Object Name | ForEach-Object {
    $frontmatter = Parse-Frontmatter -Path $_.FullName
    $checked++

    foreach ($dependency in (Split-ListField -Value $frontmatter["depends_on"])) {
        if (-not $registeredSkills.ContainsKey($dependency) -and -not $internalSkills.ContainsKey($dependency)) {
            throw "Command '$($_.Name)' depends on unknown skill '$dependency'"
        }
    }

    foreach ($target in (Split-ListField -Value $frontmatter["writes_to"])) {
        if ($target -match '^\.\.?[/\\]') {
            $fullTarget = Join-Path $Root $target
            $parent = Split-Path -Parent $fullTarget
            if (-not (Test-Path $parent)) {
                throw "Command '$($_.Name)' writes to '$target' but parent path does not exist"
            }
        }
    }

    if (-not (Split-ListField -Value $frontmatter["gates"]).Count) {
        throw "Command '$($_.Name)' must declare at least one gate"
    }
}

Write-Host "Workflow smoke test summary"
Write-Host "Commands checked: $checked"
Write-Host "Result: PASS"
exit 0
