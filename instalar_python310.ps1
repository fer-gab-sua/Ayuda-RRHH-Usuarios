# Script para instalar Python 3.10 en Windows
# Ejecutar como administrador

Write-Host "🐍 Instalando Python 3.10 para compatibilidad con PythonAnywhere..." -ForegroundColor Green
Write-Host "=" * 60

# Verificar si winget está disponible
try {
    winget --version | Out-Null
    $wingetAvailable = $true
    Write-Host "✅ winget disponible" -ForegroundColor Green
} catch {
    $wingetAvailable = $false
    Write-Host "❌ winget no disponible" -ForegroundColor Red
}

if ($wingetAvailable) {
    Write-Host "📦 Instalando Python 3.10 usando winget..." -ForegroundColor Yellow
    winget install Python.Python.3.10
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python 3.10 instalado exitosamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Error instalando Python 3.10 con winget" -ForegroundColor Red
        Write-Host "💡 Intenta descargar manualmente desde https://www.python.org/downloads/release/python-31011/" -ForegroundColor Yellow
    }
} else {
    Write-Host "📥 winget no disponible. Opciones:" -ForegroundColor Yellow
    Write-Host "1. Descargar Python 3.10.11 desde: https://www.python.org/downloads/release/python-31011/" -ForegroundColor Cyan
    Write-Host "2. Instalar winget desde Microsoft Store" -ForegroundColor Cyan
    Write-Host "3. Usar chocolatey: choco install python310" -ForegroundColor Cyan
}

Write-Host "`n🔄 Refrescando variables de entorno..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "`n✅ Instalación completa. Ejecuta 'setup_python310_env.ps1' para configurar el entorno." -ForegroundColor Green
