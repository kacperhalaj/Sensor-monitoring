import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import json
import os
from datetime import datetime, timedelta
import subprocess
from server.server import NetworkServer

CONFIG_PATH = "server_gui_config.json"

# Bufor historii odczytów per sensor_id
class SensorHistory:
    def __init__(self):
        self.history = {}

    def add(self, sensor_id, value, unit, timestamp):
        if sensor_id not in self.history:
            self.history[sensor_id] = []
        self.history[sensor_id].append((timestamp, value, unit))
        # Usuwamy stare wpisy (starsze niż 13h)
        cutoff = datetime.now() - timedelta(hours=13)
        self.history[sensor_id] = [
            (ts, v, u) for (ts, v, u) in self.history[sensor_id] if ts >= cutoff
        ]

    def get_last(self, sensor_id):
        if sensor_id not in self.history or not self.history[sensor_id]:
            return None
        return self.history[sensor_id][-1]

    def get_avg(self, sensor_id, hours):
        if sensor_id not in self.history:
            return None
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)
        values = [v for (ts, v, u) in self.history[sensor_id] if ts >= cutoff]
        if not values:
            return None
        return sum(values) / len(values)

    def get_unit(self, sensor_id):
        last = self.get_last(sensor_id)
        return last[2] if last else ""

    def get_last_timestamp(self, sensor_id):
        last = self.get_last(sensor_id)
        return last[0].strftime('%Y-%m-%d %H:%M:%S') if last else ""

    def get_all_sensor_ids(self):
        return list(self.history.keys())


class ServerGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP Sensor Server GUI")
        self.sensor_history = SensorHistory()
        self.queue = queue.Queue()
        self.server_thread = None
        self.server = None
        self.status = tk.StringVar()
        self.status.set("Zatrzymany")
        self.port_var = tk.StringVar()
        self.load_config()
        self._setup_gui()
        self.auto_update_interval = 2000  # ms

        self.client_process = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._schedule_auto_update()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    data = json.load(f)
                    self.port_var.set(str(data.get("port", 5000)))
            except Exception:
                self.port_var.set("5000")
        else:
            self.port_var.set("5000")

    def save_config(self):
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump({"port": int(self.port_var.get())}, f)
        except Exception:
            pass

    def _setup_gui(self):
        # Górny panel
        frame_top = ttk.Frame(self.root)
        frame_top.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(frame_top, text="Port TCP:").pack(side=tk.LEFT)
        entry_port = ttk.Entry(frame_top, textvariable=self.port_var, width=8)
        entry_port.pack(side=tk.LEFT, padx=5)
        self.btn_start = ttk.Button(frame_top, text="Start", command=self.on_start)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        self.btn_stop = ttk.Button(frame_top, text="Stop", command=self.on_stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        # Tabela czujników
        frame_mid = ttk.Frame(self.root)
        frame_mid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ("sensor", "last_value", "unit", "timestamp", "avg_1h", "avg_12h")
        self.tree = ttk.Treeview(frame_mid, columns=columns, show="headings")
        self.tree.heading("sensor", text="Sensor")
        self.tree.heading("last_value", text="Ostatnia wartość")
        self.tree.heading("unit", text="Jednostka")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("avg_1h", text="Średnia 1h")
        self.tree.heading("avg_12h", text="Średnia 12h")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree_scroll = ttk.Scrollbar(frame_mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Status bar
        frame_bot = ttk.Frame(self.root)
        frame_bot.pack(fill=tk.X, padx=5, pady=5)
        self.status_label = ttk.Label(frame_bot, textvariable=self.status)
        self.status_label.pack(side=tk.LEFT)

    def on_start(self):
        try:
            port = int(self.port_var.get())
            self.save_config()
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowy port!")
            return
        if self.server_thread and self.server and self.server.running:
            messagebox.showinfo("Informacja", "Serwer już działa.")
            return
        self.status.set("Uruchamianie serwera...")
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.server_thread = threading.Thread(target=self._run_server, args=(port,))
        self.server_thread.daemon = True
        self.server_thread.start()

        # Po 3s uruchomienie klienta w osobnym procesie
        self.root.after(3000, self._start_client_process)

    def _start_client_process(self):
        try:
            # Uruchom run_client.py w tym katalogu
            self.client_process = subprocess.Popen(['python', 'run_client.py'])
            self.status.set(self.status.get() + " | Uruchomiono klienta")
        except Exception as e:
            self.status.set("Serwer uruchomiony, błąd przy uruchamianiu klienta: " + str(e))
            messagebox.showerror("Błąd klienta", str(e))

    def on_stop(self):
        if self.server:
            self.server.stop()
        self.status.set("Zatrzymany")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        if self.client_process:
            try:
                self.client_process.terminate()
            except Exception:
                pass
            self.client_process = None

    def on_close(self):
        self.on_stop()
        self.root.after(300, self.root.destroy)

    def _run_server(self, port):
        try:
            self.server = NetworkServer(port=port)
            self.server.register_callback(self.on_sensor_data)
            self.status.set("Nasłuchiwanie na porcie %d" % port)
            self.server.start()
        except Exception as e:
            self.status.set("Błąd: %s" % str(e))
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            messagebox.showerror("Błąd serwera", str(e))

    def on_sensor_data(self, data):
        try:
            ts = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
            for key, sensor in data["readings"].items():
                sensor_id = sensor["sensor_id"]
                value = sensor["value"]
                unit = sensor["unit"]
                self.sensor_history.add(sensor_id, value, unit, ts)
        except Exception as e:
            pass

    def _schedule_auto_update(self):
        self._update_table()
        self.root.after(self.auto_update_interval, self._schedule_auto_update)

    def _update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for sensor_id in self.sensor_history.get_all_sensor_ids():
            last = self.sensor_history.get_last(sensor_id)
            avg1 = self.sensor_history.get_avg(sensor_id, 1)
            avg12 = self.sensor_history.get_avg(sensor_id, 12)
            unit = self.sensor_history.get_unit(sensor_id)
            ts = self.sensor_history.get_last_timestamp(sensor_id)
            value = last[1] if last else ""
            row = (
                sensor_id,
                f"{value:.2f}" if value != "" else "",
                unit,
                ts,
                f"{avg1:.2f}" if avg1 is not None else "",
                f"{avg12:.2f}" if avg12 is not None else "",
            )
            self.tree.insert("", tk.END, values=row)

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGuiApp(root)
    root.mainloop()