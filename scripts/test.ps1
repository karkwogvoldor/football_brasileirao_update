param(
    [ValidateSet("fast", "unit", "integration", "contract", "all", "external")]
    [string]$Suite = "all"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python do projeto não encontrado em $Python"
}

$Marker = switch ($Suite) {
    "fast" { "not external and not slow" }
    "unit" { "unit and not external" }
    "integration" { "integration and not external" }
    "contract" { "contract and not external" }
    "external" { "external" }
    default { "not external" }
}

Push-Location $ProjectRoot
try {
    & $Python -m pytest -m $Marker
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}

