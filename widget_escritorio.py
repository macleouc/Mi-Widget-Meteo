#!/usr/bin/env python3
import json
import locale
import os
import threading
from datetime import datetime
import requests
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except locale.Error:
    pass

CONFIG_DIR = os.path.expanduser("~/.config/mi-widget")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "ciudad": "Mérida",
    "lat": 38.9161,
    "lon": -6.3437,
    "x": None,
    "y": None,
}

WMO_CODES = {
    0: ("☀️", "Despejado"),
    1: ("🌤️", "Mayormente despejado"),
    2: ("⛅", "Parcialmente nublado"),
    3: ("☁️", "Nublado"),
    45: ("🌫️", "Niebla"),
    48: ("🌫️", "Niebla helada"),
    51: ("🌦️", "Llovizna ligera"),
    53: ("🌦️", "Llovizna moderada"),
    55: ("🌧️", "Llovizna densa"),
    61: ("🌧️", "Lluvia débil"),
    63: ("🌧️", "Lluvia moderada"),
    65: ("🌧️", "Lluvia fuerte"),
    71: ("❄️", "Nieve débil"),
    73: ("❄️", "Nieve moderada"),
    75: ("❄️", "Nieve fuerte"),
    80: ("🌦️", "Chubascos débiles"),
    81: ("🌧️", "Chubascos moderados"),
    82: ("⛈️", "Chubascos fuertes"),
    95: ("⛈️", "Tormenta"),
    96: ("⛈️", "Tormenta con granizo"),
    99: ("⛈️", "Tormenta fuerte"),
}

CSS = """
#widget-box {
    background-color: rgba(24, 26, 32, 0.78);
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.14);
    padding: 18px 24px;
}
.btn-corner {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 4px;
    min-width: 24px;
    min-height: 24px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.45);
}
.btn-corner:hover {
    color: rgba(255, 255, 255, 0.95);
    background-color: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}
#hora {
    font-family: 'Ubuntu', 'Sans', sans-serif;
    font-size: 46px;
    font-weight: 700;
    color: #ffffff;
}
#fecha {
    font-family: 'Ubuntu', 'Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    color: #b0b8c8;
    margin-top: -4px;
}
#separador {
    background-color: rgba(255, 255, 255, 0.12);
    min-height: 1px;
    margin: 12px 0px;
}
#temp {
    font-family: 'Ubuntu', 'Sans', sans-serif;
    font-size: 26px;
    font-weight: 600;
    color: #ffffff;
}
#desc-tiempo {
    font-family: 'Ubuntu', 'Sans', sans-serif;
    font-size: 13px;
    color: #d0d7e5;
}
#ciudad {
    font-family: 'Ubuntu', 'Sans', sans-serif;
    font-size: 11px;
    color: #8a94a6;
}
"""


def cargar_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def guardar_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


class ConfigDialog(Gtk.Dialog):
    def __init__(self, parent, config_actual):
        super().__init__(
            title="Configurar ubicación del widget",
            transient_for=parent,
            flags=0,
        )
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
        )
        self.set_default_size(380, 260)
        self.resultados_busqueda = []

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(14)
        box.set_margin_end(14)

        box.pack_start(Gtk.Label(label="Buscar ciudad:", xalign=0.0), False, False, 0)
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.entry_buscar = Gtk.Entry()
        self.entry_buscar.set_text(config_actual["ciudad"])
        self.entry_buscar.set_placeholder_text("Ej. Mérida, Cádiz, Madrid...")
        self.entry_buscar.connect("activate", lambda _: self.on_buscar())
        search_box.pack_start(self.entry_buscar, True, True, 0)

        btn_buscar = Gtk.Button(label="Buscar")
        btn_buscar.connect("clicked", lambda _: self.on_buscar())
        search_box.pack_start(btn_buscar, False, False, 0)
        box.pack_start(search_box, False, False, 0)

        self.combo_resultados = Gtk.ComboBoxText()
        self.combo_resultados.connect("changed", self.on_seleccionar_resultado)
        box.pack_start(self.combo_resultados, False, False, 0)

        self.lbl_estado = Gtk.Label(label="", xalign=0.0)
        box.pack_start(self.lbl_estado, False, False, 0)

        coords_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        coords_box.pack_start(Gtk.Label(label="Lat:"), False, False, 0)
        self.entry_lat = Gtk.Entry()
        self.entry_lat.set_text(str(config_actual["lat"]))
        coords_box.pack_start(self.entry_lat, True, True, 0)

        coords_box.pack_start(Gtk.Label(label="Lon:"), False, False, 0)
        self.entry_lon = Gtk.Entry()
        self.entry_lon.set_text(str(config_actual["lon"]))
        coords_box.pack_start(self.entry_lon, True, True, 0)
        box.pack_start(coords_box, False, False, 0)

        self.show_all()

    def on_buscar(self):
        query = self.entry_buscar.get_text().strip()
        if not query:
            return
        self.lbl_estado.set_text("Buscando...")
        threading.Thread(target=self._buscar_ciudad, args=(query,), daemon=True).start()

    def _buscar_ciudad(self, query):
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": query, "count": 5, "language": "es", "format": "json"}
        try:
            r = requests.get(url, params=params, timeout=10)
            results = r.json().get("results", [])
            GLib.idle_add(self._mostrar_resultados, results)
        except Exception:
            GLib.idle_add(self._mostrar_resultados, None)

    def _mostrar_resultados(self, results):
        self.combo_resultados.remove_all()
        self.resultados_busqueda = []

        if results is None:
            self.lbl_estado.set_text("Error de conexión al buscar.")
            return
        if not results:
            self.lbl_estado.set_text("No se encontraron coincidencias.")
            return

        for item in results:
            nombre = item.get("name", "")
            region = item.get("admin1", "")
            pais = item.get("country", "")
            etiqueta = ", ".join(p for p in (nombre, region, pais) if p)
            self.resultados_busqueda.append((nombre, item["latitude"], item["longitude"]))
            self.combo_resultados.append_text(etiqueta)

        self.combo_resultados.set_active(0)
        self.lbl_estado.set_text(f"Encontradas {len(results)} ubicaciones.")

    def on_seleccionar_resultado(self, combo):
        idx = combo.get_active()
        if 0 <= idx < len(self.resultados_busqueda):
            nombre, lat, lon = self.resultados_busqueda[idx]
            self.entry_buscar.set_text(nombre)
            self.entry_lat.set_text(str(lat))
            self.entry_lon.set_text(str(lon))

    def obtener_valores(self):
        try:
            lat = float(self.entry_lat.get_text().strip())
            lon = float(self.entry_lon.get_text().strip())
        except ValueError:
            return None
        ciudad = self.entry_buscar.get_text().strip() or "Ubicación"
        return {"ciudad": ciudad, "lat": lat, "lon": lon}


class MobileDesktopWidget(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.cfg = cargar_config()
        self._save_timer = None

        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)
        self.stick()
        self.set_app_paintable(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            screen, style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self.on_button_press)
        self.connect("configure-event", self.on_configure)

        overlay = Gtk.Overlay()
        self.add(overlay)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_name("widget-box")
        overlay.add(main_box)

        # Barra de iconos en la esquina superior derecha
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        controls_box.set_halign(Gtk.Align.END)
        controls_box.set_valign(Gtk.Align.START)
        controls_box.set_margin_top(10)
        controls_box.set_margin_end(12)

        btn_refresh = Gtk.Button(label="↻")
        btn_refresh.get_style_context().add_class("btn-corner")
        btn_refresh.set_tooltip_text("Actualizar tiempo ahora")
        btn_refresh.connect("clicked", self.on_manual_refresh)
        controls_box.pack_start(btn_refresh, False, False, 0)

        btn_gear = Gtk.Button(label="⚙️")
        btn_gear.get_style_context().add_class("btn-corner")
        btn_gear.set_tooltip_text("Configurar ubicación")
        btn_gear.connect("clicked", self.on_abrir_config)
        controls_box.pack_start(btn_gear, False, False, 0)

        overlay.add_overlay(controls_box)

        self.lbl_hora = Gtk.Label(label="--:--")
        self.lbl_hora.set_name("hora")
        self.lbl_hora.set_xalign(0.0)
        main_box.pack_start(self.lbl_hora, False, False, 0)

        self.lbl_fecha = Gtk.Label(label="Cargando fecha...")
        self.lbl_fecha.set_name("fecha")
        self.lbl_fecha.set_xalign(0.0)
        main_box.pack_start(self.lbl_fecha, False, False, 0)

        sep = Gtk.Box()
        sep.set_name("separador")
        main_box.pack_start(sep, False, False, 0)

        weather_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.pack_start(weather_box, False, False, 0)

        self.lbl_icono = Gtk.Label(label="⏳")
        self.lbl_icono.set_name("temp")
        weather_box.pack_start(self.lbl_icono, False, False, 0)

        info_weather = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        weather_box.pack_start(info_weather, True, True, 0)

        top_weather = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        info_weather.pack_start(top_weather, False, False, 0)

        self.lbl_temp = Gtk.Label(label="--°C")
        self.lbl_temp.set_name("temp")
        top_weather.pack_start(self.lbl_temp, False, False, 0)

        self.lbl_desc = Gtk.Label(label="Actualizando...")
        self.lbl_desc.set_name("desc-tiempo")
        self.lbl_desc.set_yalign(0.75)
        top_weather.pack_start(self.lbl_desc, False, False, 0)

        self.lbl_ciudad = Gtk.Label(label=self.cfg["ciudad"])
        self.lbl_ciudad.set_name("ciudad")
        self.lbl_ciudad.set_xalign(0.0)
        info_weather.pack_start(self.lbl_ciudad, False, False, 0)

        if self.cfg["x"] is not None and self.cfg["y"] is not None:
            self.move(max(0, int(self.cfg["x"])), max(0, int(self.cfg["y"])))

        self.actualizar_reloj()
        self.actualizar_clima()
        GLib.timeout_add_seconds(1, self.actualizar_reloj)
        GLib.timeout_add_seconds(1800, self.actualizar_clima)

    def on_configure(self, widget, event):
        x, y = self.get_position()
        if x != self.cfg.get("x") or y != self.cfg.get("y"):
            self.cfg["x"] = x
            self.cfg["y"] = y
            if self._save_timer is not None:
                GLib.source_remove(self._save_timer)
            self._save_timer = GLib.timeout_add(400, self._guardar_pos_debounced)
        return False

    def _guardar_pos_debounced(self):
        self._save_timer = None
        guardar_config(self.cfg)
        return False

    def on_button_press(self, widget, event):
        if event.button == 1:
            self.begin_move_drag(
                event.button, int(event.x_root), int(event.y_root), event.time
            )
            return True
        elif event.button == 3:
            menu = Gtk.Menu()
            item_cfg = Gtk.MenuItem(label="Configurar ubicación")
            item_cfg.connect("activate", lambda _: self.on_abrir_config(None))
            item_refresh = Gtk.MenuItem(label="Actualizar tiempo")
            item_refresh.connect("activate", lambda _: self.on_manual_refresh(None))
            item_quit = Gtk.MenuItem(label="Cerrar widget")
            item_quit.connect("activate", Gtk.main_quit)
            menu.append(item_cfg)
            menu.append(item_refresh)
            menu.append(item_quit)
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False

    def on_manual_refresh(self, _btn):
        self.lbl_desc.set_text("Actualizando...")
        self.actualizar_clima()

    def on_abrir_config(self, _btn):
        dialog = ConfigDialog(self, self.cfg)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            nuevos = dialog.obtener_valores()
            if nuevos:
                self.cfg.update(nuevos)
                guardar_config(self.cfg)
                self.lbl_ciudad.set_text(self.cfg["ciudad"])
                self.lbl_desc.set_text("Actualizando...")
                self.actualizar_clima()
        dialog.destroy()

    def actualizar_reloj(self):
        ahora = datetime.now()
        self.lbl_hora.set_text(ahora.strftime("%H:%M"))
        fecha_txt = ahora.strftime("%A, %d de %B").capitalize()
        self.lbl_fecha.set_text(fecha_txt)
        return True

    def actualizar_clima(self):
        threading.Thread(target=self._fetch_weather, daemon=True).start()
        return True

    def _fetch_weather(self):
        lat = self.cfg["lat"]
        lon = self.cfg["lon"]
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true"
        )
        try:
            r = requests.get(url, timeout=10)
            data = r.json()["current_weather"]
            temp = round(data["temperature"])
            code = data["weathercode"]
            icono, desc = WMO_CODES.get(code, ("🌡️", "Variable"))
            GLib.idle_add(self._aplicar_clima, icono, f"{temp}°C", desc)
        except Exception:
            GLib.idle_add(self._aplicar_clima, "⚠️", "--°C", "Sin conexión")

    def _aplicar_clima(self, icono, temp, desc):
        self.lbl_icono.set_text(icono)
        self.lbl_temp.set_text(temp)
        self.lbl_desc.set_text(desc)


if __name__ == "__main__":
    win = MobileDesktopWidget()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
