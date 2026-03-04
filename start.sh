#!/bin/bash

echo "🚀 Iniciando Jira Report App..."

# Comprobar fichero .env
if [ ! -f ".env" ]; then
    echo "❌ Error: No se encontró el fichero .env"
    echo "   Copia .env.default a .env y rellena tus datos:"
    echo "   cp .env.default .env"
    exit 1
fi

# Comprobar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado. Por favor instálalo."
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno
source venv/bin/activate

# Instalar dependencias
echo "⬇️  Comprobando dependencias..."
pip install -r requirements.txt

# Ejecutar app
echo "✅ Ejecutando aplicación..."
streamlit run app.py
