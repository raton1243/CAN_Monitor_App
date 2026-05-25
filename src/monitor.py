import tkinter as tk
from tkinter import ttk, filedialog
import datetime
from core.core import CoreMonitor

class MonitorApp(CoreMonitor):
    def __init__(self):
        super().__init__()
        self.line_count = 0
        self.treeview_lines = 0

    def update_log(self, data):
        self.line_count += 1
        self.treeview_lines += 1

        can_values = self.process_can_message(data, self.line_count)

        self.gui_log.insert("", tk.END, values=[can_values[col] for col in can_values])

        if self.gui_checkbutton_follow_state.get():
            self.gui_log.yview_moveto(1)

        if self.gui_checkbutton_export_log_state.get():
            self.write_log_line()

        if self.treeview_lines > self.MAX_LOG_LINES + 20:
            self.gui_log.delete(*self.gui_log.get_children()[:20])
            self.treeview_lines -= 20

    def export_log(self):
        if not self.gui_checkbutton_export_log_state.get():
            self.close_log_file()
            self.gui_label_info.config(text="Grabación en tiempo real detenida", fg="blue")
            return

        file_route = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"LOG_{self.gui_combobox_port.get()}_{self.gui_combobox_baudrate.get()}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        )
        if not file_route:
            self.gui_checkbutton_export_log_state.set(False)
            return

        if self.create_log_file(file_route):
            self.gui_label_info.config(text=f"Grabación en tiempo real iniciada {file_route}", fg="green")
        else:
            self.gui_label_info.config(text=f"Error al crear el archivo", fg="red")
            self.gui_checkbutton_export_log_state.set(False)

    def clear_log(self):
        self.gui_log.delete(*self.gui_log.get_children())
        self.line_count = 0
        self.treeview_lines = 0

    def loop(self):
        data = self.read_port()
        if self.gui_checkbutton_listen_state.get() and data:
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
        #row 0
        gui_frame_configuration = tk.Frame(self.gui_window)
        gui_frame_configuration.grid(row=0, column=0, padx=10, pady=(10,0), sticky=tk.EW)

        tk.Button(gui_frame_configuration, text="Actualizar", command=self.gui_update_port_list).pack(side=tk.LEFT)
        #row 2
        gui_frame_configuration2 = tk.Frame(self.gui_window)
        gui_frame_configuration2.grid(row=2, column=0, padx=10, pady=10, sticky=tk.EW)

        self.gui_checkbutton_export_log_state = tk.BooleanVar(value=False)
        self.gui_checkbutton_export_log = tk.Checkbutton(gui_frame_configuration2, text="Exportar log en tiempo real", variable=self.gui_checkbutton_export_log_state, indicatoron=False, command=self.export_log)
        self.gui_checkbutton_export_log.pack(side=tk.LEFT)

        self.gui_label_info = tk.Label(gui_frame_configuration2)
        self.gui_label_info.pack(side=tk.LEFT, padx=(10,0))
        #row 0
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
        #row 1
        self.gui_window.rowconfigure(1, weight=1)
        self.gui_window.columnconfigure(0, weight=1)

        self.gui_log = ttk.Treeview(columns=("line", "hour", "stdid", "extid", "ide", "rtr", "dlc", "timestamp", "data"), show="headings")
        self.gui_log.grid(row=1, column=0, padx=10, pady=(10,0), sticky=tk.NSEW)

        for col in self.gui_log["columns"]:
            self.gui_log.heading(col, text=col.upper())
            self.gui_log.column(col, width=0, anchor=tk.CENTER)

        self.gui_log.configure(displaycolumns=self.COLUMNS_TREEVIEW)

if __name__ == "__main__":
    app = MonitorApp()
    app.gui_create()
    app.gui_window.after(0, app.loop)
    app.gui_window.mainloop()