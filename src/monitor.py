import tkinter as tk
from tkinter import ttk, filedialog
import datetime
from core.core import CoreMonitor
import struct

class MonitorApp(CoreMonitor):
    def __init__(self):
        super().__init__()
        self.log_file_real_time = None

    def update_log(self, data):
        self.line_count += 1
        self.treeview_lines += 1

        std_id, ext_id, ide, rtr, dlc, timestamp, can_data = struct.unpack('<IIIIII8s', data)
        self.can_values = {
            "line": self.line_count,
            "hour": datetime.datetime.now().strftime("%H:%M:%S.%f"),
            "stdid": hex(std_id),
            "extid": hex(ext_id),
            "ide": bool(ide),
            "rtr": bool(rtr),
            "dlc": dlc,
            "timestamp": timestamp,
            "data": can_data.hex(' ').upper()
        }

        self.gui_log.insert("", tk.END, iid=self.line_count, values=[self.can_values[col] for col in self.can_values])

        if self.gui_checkbutton_follow_state.get():
            self.gui_log.yview_moveto(1)

        if self.gui_checkbutton_export_log_real_time_state.get():
            if self.log_file_real_time:
                #try:
                self.log_file_real_time.write(",".join(str(self.can_values[col]) for col in self.COLUMNS_LOG) + "\n")
                #except:
                #    pass

        if self.treeview_lines > self.MAX_LOG_LINES:
            self.gui_log.delete(self.line_count - self.MAX_LOG_LINES)
            self.treeview_lines -= 1

    def export_log(self):
        file_route = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"LOG_{self.gui_combobox_port.get()}_{self.gui_combobox_baudrate.get()}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        )

        if file_route:
            try:
                with open(file_route, "w", encoding="utf-8") as file:
                    file.write(",".join(self.COLUMNS_LOG) + "\n")
                    file.write("\n".join(",".join(str(self.gui_log.item(child)["values"][self.gui_log["columns"].index(col)]) for col in self.COLUMNS_LOG) for child in self.gui_log.get_children()))
            except Exception as e:
                self.gui_label_info.config(text=f"Error al guardar el archivo: {e}", fg="red")

    def export_log_real_time(self):
        if not self.gui_checkbutton_export_log_real_time_state.get():
            return

        self.log_file_real_time = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"LOG_{self.gui_combobox_port.get()}_{self.gui_combobox_baudrate.get()}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        )
        if not self.log_file_real_time:
            self.gui_checkbutton_export_log_real_time_state.set(False)
            return

        try:
            route = self.log_file_real_time
            self.log_file_real_time = open(route, "w", encoding="utf-8")
            self.log_file_real_time.write(",".join(self.COLUMNS_LOG) + "\n")
        except Exception as e:
            self.gui_label_info.config(text=f"Error al guardar el archivo: {e}", fg="red")
            self.gui_checkbutton_export_log_real_time_state.set(False)
            self.log_file_real_time = None

    def clear_log(self):
        self.gui_log.delete(*self.gui_log.get_children())
        self.line_count = 0
        self.treeview_lines = 0

    def loop(self):
        if self.port_serial.is_open and self.port_serial.in_waiting >= 32:
            data = self.port_serial.read(32)
            if self.gui_checkbutton_listen_state.get():
                self.update_log(data)

        self.gui_window.after(self.LOOP_MS, self.loop)

    def gui_apply_port(self):
        baudrate = self.gui_combobox_baudrate.get()
        if not baudrate.isdigit():
            self.gui_label_info.config(text="El baudrate debe ser un número", fg="red")
            return

        device = self.gui_combobox_port.get()
        baudrate = int(baudrate)

        if self.update_port(device, baudrate):
            self.gui_label_info.config(text=f"Conectado al puerto {device} de baudrate {baudrate}", fg="green")
            self.line_count = 0
            self.treeview_lines = 0
        else:
            self.gui_label_info.config(text=f"No se pudo conectar al puerto {device}", fg="red")
        self.clear_log()

    def gui_update_port_list(self):
        self.gui_combobox_port.configure(values=self.get_ports())
        self.gui_label_info.config(text="Lista de puertos actualizada", fg="green")

    def gui_listen_and_follow_log(self):
        if self.gui_checkbutton_listen_state.get():
            self.gui_checkbutton_follow_state.set(True)

    def gui_search_default_port(self):
        default_port = self.search_default_port()
        if default_port:
            self.gui_label_info.config(text=f"Puerto por defecto encontrado: {default_port}", fg="green")
            return default_port
        else:
            return "Desconectado"

    def gui_close(self):
        if self.port_serial.is_open:
            self.port_serial.close()
        if self.log_file is not None:
            self.log_file.close()
        self.gui_window.destroy()

    def gui_create(self):
        self.gui_window = tk.Tk()
        self.gui_window.title("MonitorApp")
        self.gui_window.geometry("1000x600+100+100")
        self.gui_window.protocol("WM_DELETE_WINDOW", self.gui_close)
        #row 1
        gui_frame_configuration = tk.Frame(self.gui_window)
        gui_frame_configuration.grid(row=0, column=0, padx=10, pady=(10,0), sticky=tk.EW)

        tk.Button(gui_frame_configuration, text="Actualizar", command=self.gui_update_port_list).pack(side=tk.LEFT)
        #row 2
        self.gui_label_info = tk.Label(self.gui_window, text="Lista de puertos actualizada", fg="green")
        self.gui_label_info.grid(row=1, column=0, padx=10, pady=(10,0), sticky=tk.NW)
        #row 1
        tk.Label(gui_frame_configuration, text="Puerto:").pack(side=tk.LEFT, padx=(10,0))

        self.gui_combobox_port = ttk.Combobox(gui_frame_configuration, values=self.get_ports())
        self.gui_combobox_port.set(self.gui_search_default_port())
        self.gui_combobox_port.pack(side=tk.LEFT, padx=(10,0))

        tk.Label(gui_frame_configuration, text="Baudrate:").pack(side=tk.LEFT, padx=(10,0))

        self.gui_combobox_baudrate = ttk.Combobox(gui_frame_configuration, values=self.BAUDRATE_LIST)
        self.gui_combobox_baudrate.set(self.DEFAULT_BAUDRATE)
        self.gui_combobox_baudrate.pack(side=tk.LEFT, padx=(10,0))

        tk.Button(gui_frame_configuration, text="Aplicar", command=self.gui_apply_port).pack(side=tk.LEFT, padx=(10,0))

        self.gui_checkbutton_listen_state = tk.BooleanVar(value=False)
        self.gui_checkbutton_listen = tk.Checkbutton(gui_frame_configuration, text="Escuchar", variable=self.gui_checkbutton_listen_state, indicatoron=False, command=self.gui_listen_and_follow_log)
        self.gui_checkbutton_listen.pack(side=tk.LEFT, padx=(10,0))

        self.gui_checkbutton_follow_state = tk.BooleanVar(value=True)
        self.gui_checkbutton_follow = tk.Checkbutton(gui_frame_configuration, text="Seguir logs", variable=self.gui_checkbutton_follow_state, indicatoron=False)
        self.gui_checkbutton_follow.pack(side=tk.LEFT, padx=(10,0))

        tk.Button(gui_frame_configuration, text="Limpiar", command=self.clear_log).pack(side=tk.RIGHT)
        #row 3
        self.gui_window.rowconfigure(2, weight=1)
        self.gui_window.columnconfigure(0, weight=1)

        self.gui_log = ttk.Treeview(columns=("line", "hour", "stdid", "extid", "ide", "rtr", "dlc", "timestamp", "data"), show="headings")
        self.gui_log.grid(row=2, column=0, padx=10, pady=(10,0), sticky=tk.NSEW)

        for col in self.gui_log["columns"]:
            self.gui_log.heading(col, text=col.upper())
            self.gui_log.column(col, width=0, anchor=tk.CENTER)

        self.gui_log.configure(displaycolumns=self.COLUMNS_TREEVIEW)
        #row 4
        gui_frame_configuration2 = tk.Frame(self.gui_window)
        gui_frame_configuration2.grid(row=3, column=0, padx=10, pady=10, sticky=tk.EW)

        self.gui_button_export_log = tk.Button(gui_frame_configuration2, text="Exportar log", command=self.export_log)
        self.gui_button_export_log.pack(side=tk.LEFT)

        self.gui_checkbutton_export_log_real_time_state = tk.BooleanVar(value=False)
        self.gui_checkbutton_export_log_real_time = tk.Checkbutton(gui_frame_configuration2, text="Exportar log en tiempo real", variable=self.gui_checkbutton_export_log_real_time_state, indicatoron=False, command=self.export_log_real_time)
        self.gui_checkbutton_export_log_real_time.pack(side=tk.LEFT, padx=(10,0))

if __name__ == "__main__":
    app = MonitorApp()
    app.gui_create()
    app.gui_window.after(0, app.loop)
    app.gui_window.mainloop()
