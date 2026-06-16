$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path (Split-Path -Parent $root) 'Projeto3-Desktop\dist\VERIFIQ.exe'
$targetDir = Join-Path $root 'downloads'
$target = Join-Path $targetDir 'VERIFIQ.exe'

if (-not (Test-Path $source)) {
    throw "Não encontrei o executável em $source. Rode o build do desktop antes."
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
Copy-Item -Force $source $target
Write-Host "Executável copiado para $target"
