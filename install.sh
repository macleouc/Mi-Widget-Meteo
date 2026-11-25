#!/usr/bin/env bash
set -euo pipefail

DEST_DIR="$HOME/.local/share/mi-widget"

echo "Instalando dependencias GTK3 y requests..."
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-requests
else
    echo "Instala manualmente los paquetes GTK3 para Python 3 y requests en tu distribución."
fi

mkdir -p "$DEST_DIR"
cp widget_escritorio.py "$DEST_DIR/widget_escritorio.py"
chmod +x "$DEST_DIR/widget_escritorio.py"

echo "Instalación completada. Ejecuta: $DEST_DIR/widget_escritorio.py"
