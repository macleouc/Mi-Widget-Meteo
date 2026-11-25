# Widget de Escritorio (Hora, Fecha y Tiempo) para Linux Mint / MATE
Este proyecto se distribuye bajo licencia GNU GPL v3.0. Consulta el archivo LICENSE para ver el texto completo.

*Widget* flotante estilo tarjeta móvil escrito en **Python + GTK3** para escritorios Linux con composición (pensado especialmente para **Linux Mint MATE**). Muestra hora actual, fecha en español y meteorología en tiempo real mediante la API gratuita de [Open-Meteo](https://open-meteo.com/) (sin clave de API).

## Características

- **Aspecto de tarjeta flotante:** Bordes redondeados, fondo semitransparente, sin barra de título y fijado por debajo de las ventanas (`keep_below`) en todos los escritorios virtuales.
- **Arrastrable con el ratón:** Haz clic izquierdo en cualquier zona libre de la tarjeta para moverla; su posición `(x, y)` se guarda automáticamente.
- **Actualización manual y automática:** Consulta el tiempo al iniciar y cada 30 minutos; incluye el botón `↻` (junto al engranaje) y la opción del menú contextual para forzar la actualización al instante.
- **Selector de ubicación:** El botón `⚙️` abre un diálogo para buscar ciudad o introducir latitud y longitud manualmente, guardando la configuración en `~/.config/mi-widget/config.json`.

## Instalación rápida

Clona el repositorio y ejecuta el instalador:

```bash
git clone https://github.com/macleouc/Mi-Widget-Meteo.git
cd Mi-Widget-Meteo
chmod +x install.sh
./install.sh
```

`install.sh` instala las dependencias del sistema (`python3-gi`, `python3-gi-cairo`, `gir1.2-gtk-3.0` y `python3-requests` en sistemas basados en APT) y copia el ejecutable a `~/.local/share/mi-widget/widget_escritorio.py`.

## Uso

Ejecuta el *widget* desde la terminal o mediante su ruta completa:

```bash
~/.local/share/mi-widget/widget_escritorio.py
```

- **Mover:** Clic izquierdo y arrastrar.
- **Actualizar tiempo:** Clic en `↻` (arriba a la derecha) o clic derecho → **Actualizar tiempo**.
- **Cambiar ubicación:** Clic en `⚙️` (arriba a la derecha) o clic derecho → **Configurar ubicación**.
- **Cerrar:** Clic derecho → **Cerrar widget**.

### Arranque automático en MATE

1. Abre **Menú → Preferencias → Aplicaciones al inicio**.
2. Pulsa **Añadir**.
3. Indica un nombre (por ejemplo, `Widget Escritorio`) y en la orden pon `~/.local/share/mi-widget/widget_escritorio.py` (o su ruta absoluta `/home/TU_USUARIO/.local/share/mi-widget/widget_escritorio.py`).

## Notas y requisitos

- **Compositor activo:** Para que el fondo semitransparente y las esquinas redondeadas se rendericen sin recuadros negros, asegúrate de tener habilitada la composición de ventanas en **Menú → Preferencias → Configuración del escritorio → Ventanas** (*Marco + Composición* u otro compositor X11 activo).
- **Entorno:** Diseñado para sesiones X11 en Linux Mint MATE y distribuciones compatibles con GTK3.
- **Configuración:** Los ajustes de ubicación y posición se almacenan en `~/.config/mi-widget/config.json`. Si borras ese archivo, volverá a los valores por defecto al próximo arranque.
