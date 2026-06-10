# Compila docs/thesis.tex a docs/thesis.pdf vía pdflatex.
#
# Requiere una instalación LaTeX (MiKTeX o TeX Live).
# Instala MiKTeX si no la tenés:    winget install MiKTeX.MiKTeX
#
# Uso:
#   cd docs
#   .\build.ps1

$ErrorActionPreference = "Stop"

if (-not (Get-Command pdflatex -ErrorAction SilentlyContinue)) {
    Write-Host "pdflatex no encontrado. Instalalo con: winget install MiKTeX.MiKTeX" -ForegroundColor Red
    exit 1
}

Write-Host "[build] primera pasada..." -ForegroundColor Cyan
pdflatex -interaction=nonstopmode -halt-on-error thesis.tex | Out-Null

Write-Host "[build] segunda pasada (resuelve TOC y referencias)..." -ForegroundColor Cyan
pdflatex -interaction=nonstopmode -halt-on-error thesis.tex | Out-Null

if (Test-Path thesis.pdf) {
    $size = (Get-Item thesis.pdf).Length / 1KB
    Write-Host ("[build] OK -> thesis.pdf ({0:N1} KB)" -f $size) -ForegroundColor Green
} else {
    Write-Host "[build] FAIL: thesis.pdf no se generó. Revisá thesis.log." -ForegroundColor Red
    exit 1
}

# limpieza de archivos auxiliares
Remove-Item -ErrorAction SilentlyContinue thesis.aux, thesis.log, thesis.toc, thesis.out
Get-ChildItem sections -Filter "*.aux" -ErrorAction SilentlyContinue | Remove-Item
