#!/bin/bash

# ═══════════════════════════════════════════════════════════════════
# LINUP - Setup completo para compilar APK
# ═══════════════════════════════════════════════════════════════════

set -e  # Detener si hay errores

echo "════════════════════════════════════════════════════════════"
echo "  LINUP - Configuración del Environment"
echo "════════════════════════════════════════════════════════════"
echo ""

# 1. Verificar Python
echo "[1/6] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Instálalo con: brew install python@3.11"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION encontrado"
echo ""

# 2. Crear entorno virtual
echo "[2/6] Creando entorno virtual..."
if [ -d "venv" ]; then
    echo "⚠️  El entorno virtual ya existe, usando el existente"
else
    python3 -m venv venv
    echo "✓ Entorno virtual creado"
fi
echo ""

# 3. Activar entorno e instalar dependencias
echo "[3/6] Instalando dependencias..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install flet --break-system-packages 2>/dev/null || pip install flet
echo "✓ Flet instalado"
echo ""

# 4. Verificar Flutter
echo "[4/6] Verificando Flutter..."
if ! command -v flutter &> /dev/null; then
    echo "⚠️  Flutter no encontrado en PATH"
    echo "   Flet lo descargará automáticamente en el primer build"
else
    FLUTTER_VERSION=$(flutter --version | head -n1 | cut -d' ' -f2)
    echo "✓ Flutter $FLUTTER_VERSION encontrado"
fi
echo ""

# 5. Verificar Android SDK
echo "[5/6] Verificando Android SDK..."
if [ -d "$HOME/Library/Android/sdk" ]; then
    echo "✓ Android SDK encontrado"
    export ANDROID_HOME="$HOME/Library/Android/sdk"
    export PATH="$PATH:$ANDROID_HOME/platform-tools"
else
    echo "⚠️  Android SDK no encontrado"
    echo "   Flet lo descargará automáticamente en el primer build"
fi
echo ""

# 6. Resumen
echo "[6/6] Resumen de configuración"
echo "════════════════════════════════════════════════════════════"
echo "Python:        $PYTHON_VERSION"
echo "Flet:          $(pip show flet | grep Version | cut -d' ' -f2)"
echo "Proyecto:      $(pwd)"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "✅ Environment listo!"
echo ""
echo "PRÓXIMOS PASOS:"
echo "  1. Activar entorno: source venv/bin/activate"
echo "  2. Probar localmente: flet run main.py"
echo "  3. Compilar APK:      flet build apk"
echo ""
echo "NOTAS:"
echo "  • El primer build puede tardar 20-40 minutos"
echo "  • Los siguientes builds tardan 3-8 minutos"
echo "  • El APK queda en: build/apk/app.apk"
echo "  • Instalar: adb install -r build/apk/app.apk"
echo ""
