#!/usr/bin/env python3
"""
Script para descargar e instalar Python 3.10 automáticamente
"""

import sys
import subprocess
import os
import urllib.request
import tempfile
import platform

def check_python_310():
    """Verificar si Python 3.10 ya está instalado"""
    commands = ["py -3.10", "python3.10", "python310"]
    
    for cmd in commands:
        try:
            result = subprocess.run(f"{cmd} --version", shell=True, capture_output=True, text=True)
            if result.returncode == 0 and "Python 3.10" in result.stdout:
                print(f"✅ Python 3.10 ya está instalado: {cmd}")
                return True, cmd
        except:
            continue
    
    return False, None

def install_with_winget():
    """Instalar Python 3.10 usando winget"""
    try:
        print("📦 Instalando Python 3.10 con winget...")
        result = subprocess.run("winget install Python.Python.3.10", shell=True)
        return result.returncode == 0
    except:
        return False

def install_from_microsoft_store():
    """Abrir Microsoft Store para instalar Python 3.10"""
    try:
        print("🏪 Abriendo Microsoft Store para instalar Python 3.10...")
        subprocess.run("start ms-windows-store://pdp/?ProductId=9PJPW5LDXLZ5", shell=True)
        print("💡 Instala Python 3.10 desde Microsoft Store y luego ejecuta este script nuevamente")
        return True
    except:
        return False

def download_and_install_python():
    """Descargar e instalar Python 3.10 desde python.org"""
    try:
        print("📥 Descargando Python 3.10.11 desde python.org...")
        
        # URL para Python 3.10.11 Windows x64
        if platform.machine().endswith('64'):
            url = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
        else:
            url = "https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe"
        
        # Descargar el instalador
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as tmp_file:
            urllib.request.urlretrieve(url, tmp_file.name)
            installer_path = tmp_file.name
        
        print(f"💾 Archivo descargado: {installer_path}")
        print("🚀 Ejecutando instalador de Python 3.10...")
        
        # Ejecutar instalador con opciones recomendadas
        result = subprocess.run([
            installer_path,
            "/quiet",  # Instalación silenciosa
            "InstallAllUsers=1",  # Instalar para todos los usuarios
            "PrependPath=1",  # Agregar al PATH
            "Include_test=0",  # No incluir tests
            "Include_launcher=1"  # Incluir py launcher
        ])
        
        # Limpiar archivo temporal
        try:
            os.unlink(installer_path)
        except:
            pass
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"❌ Error descargando Python: {e}")
        return False

def main():
    print("🐍 Instalador automático de Python 3.10")
    print("=" * 50)
    
    # Verificar si ya está instalado
    installed, cmd = check_python_310()
    if installed:
        print(f"✅ Python 3.10 ya disponible como: {cmd}")
        return True
    
    print("❌ Python 3.10 no encontrado. Instalando...")
    
    # Intentar diferentes métodos de instalación
    methods = [
        ("winget", install_with_winget),
        ("Microsoft Store", install_from_microsoft_store),
        ("Descarga directa", download_and_install_python)
    ]
    
    for method_name, method_func in methods:
        print(f"\n🔄 Intentando instalar con {method_name}...")
        
        if method_func():
            if method_name == "Microsoft Store":
                print("⏳ Espera a que termine la instalación desde Microsoft Store...")
                input("Presiona Enter cuando hayas terminado la instalación...")
            
            # Verificar instalación
            print("🔍 Verificando instalación...")
            installed, cmd = check_python_310()
            if installed:
                print(f"✅ Python 3.10 instalado exitosamente!")
                print(f"💡 Ahora ejecuta: setup_python310_env.ps1")
                return True
        
        print(f"❌ Falló instalación con {method_name}")
    
    print("\n❌ No se pudo instalar Python 3.10 automáticamente")
    print("💡 Opciones manuales:")
    print("   1. Microsoft Store: https://www.microsoft.com/store/productId/9PJPW5LDXLZ5")
    print("   2. Python.org: https://www.python.org/downloads/release/python-31011/")
    return False

if __name__ == "__main__":
    success = main()
    input("\nPresiona Enter para salir...")
    sys.exit(0 if success else 1)
