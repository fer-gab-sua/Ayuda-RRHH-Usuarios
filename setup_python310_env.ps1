# Script para configurar entorno virtual con Python 3.10
# Ejecutar después de tener Python 3.10 instalado

Write-Host "🚀 Configurando entorno virtual con Python 3.10..." -ForegroundColor Green
Write-Host "=" * 60

# Verificar que Python 3.10 esté disponible
$python310Available = $false
$pythonCommands = @("py -3.10", "python3.10", "python310")

foreach ($cmd in $pythonCommands) {
    try {
        $version = & $cmd --version 2>$null
        if ($version -match "Python 3\.10") {
            $pythonCmd = $cmd
            $python310Available = $true
            Write-Host "✅ Python 3.10 encontrado: $cmd" -ForegroundColor Green
            Write-Host "   Versión: $version" -ForegroundColor Cyan
            break
        }
    } catch {
        # Continuar con el siguiente comando
    }
}

if (-not $python310Available) {
    Write-Host "❌ Python 3.10 no encontrado" -ForegroundColor Red
    Write-Host "💡 Ejecuta primero 'instalar_python310.ps1'" -ForegroundColor Yellow
    Write-Host "💡 O descarga Python 3.10.11 desde: https://www.python.org/downloads/release/python-31011/" -ForegroundColor Yellow
    exit 1
}

# Eliminar entorno virtual existente si existe
if (Test-Path "venv") {
    Write-Host "🗑️  Eliminando entorno virtual existente..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
}

# Crear nuevo entorno virtual con Python 3.10
Write-Host "📦 Creando entorno virtual con Python 3.10..." -ForegroundColor Yellow
& $pythonCmd -m venv venv

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error creando entorno virtual" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Entorno virtual creado exitosamente" -ForegroundColor Green

# Activar entorno virtual
Write-Host "🔧 Activando entorno virtual..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Actualizar pip
Write-Host "📈 Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Verificar versión de Python en el entorno virtual
$venvPythonVersion = python --version
Write-Host "✅ Python en venv: $venvPythonVersion" -ForegroundColor Green

# Instalar dependencias
Write-Host "📦 Instalando dependencias desde requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencias instaladas exitosamente" -ForegroundColor Green
} else {
    Write-Host "❌ Error instalando dependencias" -ForegroundColor Red
    Write-Host "💡 Verifica que requirements.txt existe y es válido" -ForegroundColor Yellow
}

Write-Host "`n🎉 Configuración completa!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host "Para usar el entorno virtual:" -ForegroundColor Cyan
Write-Host "  1. Activar: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Ejecutar: python manage.py runserver" -ForegroundColor White
Write-Host "  3. Desactivar: deactivate" -ForegroundColor White
Write-Host "`n🌐 Ahora tu entorno local usará las mismas versiones que PythonAnywhere!" -ForegroundColor Green
