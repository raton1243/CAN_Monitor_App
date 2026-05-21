import tkinter as tk
from tkinter import ttk, filedialog
import datetime
from core.core import CoreMonitor

class MonitorApp(CoreMonitor):
    def __init__(self):
        super().__init__()

    def update_log(self, data):
        self.gui_log.insert("", "end", text=self.line_count, values=(str(datetime.datetime.now().strftime("%H:%M:%S.%f")) + " " + data.strip()))
        self.line_count += 1
        
        if self.gui_checkbutton_export_log_real_time_state.get():
            try:
                with open(self.log_route_real_time, "a", encoding="utf-8") as file:
                    csv_line = f"{self.line_count},{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')},{data.strip()}"
                    file.write(csv_line + "\n")
            except:
                pass
        
        self.gui_log.delete(*self.gui_log.get_children()[:-self.MAX_LOG_LINES])

    def export_log(self):
        file_route = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"LOG_{self.gui_combobox_port.get()}_{self.gui_combobox_baudrate.get()}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        )
        
        if file_route:
            try:
                with open(file_route, "w", encoding="utf-8") as file:
                    for child in self.gui_log.get_children():
                        values = self.gui_log.item(child)["values"]
                        text = self.gui_log.item(child)["text"]
                        
                        csv_line = f"{text}," + ",".join(map(str, values))
                        file.write(csv_line + "\n")
            except Exception as e:
                self.gui_label_info.config(text=f"Error al guardar el archivo: {e}", fg="red")

    def export_log_real_time(self):
        if self.gui_checkbutton_export_log_real_time_state.get():
            self.log_route_real_time = filedialog.asksaveasfilename(
                defaultextension=".csv",
                initialfile=f"LOG_{self.gui_combobox_port.get()}_{self.gui_combobox_baudrate.get()}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
            )
            if not self.log_route_real_time:
                self.gui_checkbutton_export_log_real_time_state.set(False)

    def clear_log(self):        
        self.gui_log.delete(*self.gui_log.get_children())
        self.line_count = 0

    def loop(self):
        if self.port_serial and self.port_serial.is_open:
            port_bytes = self.port_serial.in_waiting
            if port_bytes > 0:
                data = self.port_serial.read(port_bytes).decode("ascii", errors="replace")
                
                if self.gui_checkbutton_listen_state.get():
                    self.port_buffer += data    
                    while "\n" in self.port_buffer:
                        can_line, self.port_buffer = self.port_buffer.split("\n", 1)
                        self.update_log(can_line)
                else:
                    self.port_buffer = ""
        
        if self.gui_checkbutton_follow_state.get():
            self.gui_log.yview_moveto(1)
            pass
                
        self.gui_window.after(self.LOOP_MS, self.loop)

    def gui_update_port_list(self):
        self.gui_combobox_port.configure(values=self.get_ports())
        self.gui_label_info.config(text="Lista de puertos actualizada", fg="green")

    def gui_listen_and_follow_log(self):
        if self.gui_checkbutton_listen_state.get():
            self.gui_checkbutton_follow_state.set(True)

    def gui_create(self):
        self.gui_window = tk.Tk()
        self.gui_window.title("MonitorApp")
        self.gui_window.geometry("1000x600+100+100")
        self.gui_window.protocol("WM_DELETE_WINDOW", self.gui_close)
        #1
        gui_frame_configuration = tk.Frame(self.gui_window)
        gui_frame_configuration.grid(row=0, column=0, padx=10, pady=(10,0), sticky=tk.EW)

        tk.Button(gui_frame_configuration, text="Actualizar", command=self.gui_update_port_list).pack(side=tk.LEFT)
        #2
        self.gui_label_info = tk.Label(self.gui_window, text="Lista de puertos actualizada", fg="green")
        self.gui_label_info.grid(row=1, column=0, padx=10, pady=(10,0), sticky=tk.NW)
        #1
        tk.Label(gui_frame_configuration, text="Puerto:").pack(side=tk.LEFT, padx=(10,0))

        self.gui_combobox_port = ttk.Combobox(gui_frame_configuration, values=self.get_ports())
        self.gui_combobox_port.set(self.search_default_port())
        self.gui_combobox_port.pack(side=tk.LEFT, padx=(10,0))

        tk.Label(gui_frame_configuration, text="Baudrate:").pack(side=tk.LEFT, padx=(10,0))

        self.gui_combobox_baudrate = ttk.Combobox(gui_frame_configuration, values=self.BAUDRATE_LIST)
        self.gui_combobox_baudrate.set(self.DEFAULT_BAUDRATE)
        self.gui_combobox_baudrate.pack(side=tk.LEFT, padx=(10,0))

        tk.Button(gui_frame_configuration, text="Aplicar", command=self.update_port).pack(side=tk.LEFT, padx=(10,0))

        self.gui_checkbutton_listen_state = tk.BooleanVar(value=False)
        self.gui_checkbutton_listen = tk.Checkbutton(gui_frame_configuration, text="Escuchar", variable=self.gui_checkbutton_listen_state, indicatoron=False, command=self.gui_listen_and_follow_log)
        self.gui_checkbutton_listen.pack(side=tk.LEFT, padx=(10,0))

        self.gui_checkbutton_follow_state = tk.BooleanVar(value=True)
        self.gui_checkbutton_follow = tk.Checkbutton(gui_frame_configuration, text="Seguir logs", variable=self.gui_checkbutton_follow_state, indicatoron=False)
        self.gui_checkbutton_follow.pack(side=tk.LEFT, padx=(10,0))

        tk.Button(gui_frame_configuration, text="Limpiar", command=self.clear_log).pack(side=tk.RIGHT)
        #3
        self.gui_window.rowconfigure(2, weight=1)
        self.gui_window.columnconfigure(0, weight=1)

        self.gui_log = ttk.Treeview(columns=("datetime", "timestamp", "id", "dlc", "data"))
        self.gui_log.grid(row=2, column=0, padx=10, pady=(10,0), sticky=tk.NSEW)

        self.gui_log.heading("#0", text="LINE")
        self.gui_log.heading("datetime", text="DATETIME")
        self.gui_log.heading("timestamp", text="TIMESTAMP")
        self.gui_log.heading("id", text="ID")
        self.gui_log.heading("dlc", text="DLC")
        self.gui_log.heading("data", text="DATA")

        self.gui_log.column("#0", width=0, anchor=tk.CENTER)
        self.gui_log.column("datetime", width=0, anchor=tk.CENTER)
        self.gui_log.column("timestamp", width=0, anchor=tk.CENTER)
        self.gui_log.column("id", width=0, anchor=tk.CENTER)
        self.gui_log.column("dlc", width=0, anchor=tk.CENTER)
        self.gui_log.column("data", width=0, anchor=tk.CENTER)

        self.gui_log.configure(displaycolumns=self.SHOW_COLUMNS)
        #4
        gui_frame_configuration2 = tk.Frame(self.gui_window)
        gui_frame_configuration2.grid(row=3, column=0, padx=10, pady=10, sticky=tk.EW)

        self.gui_button_export_log = tk.Button(gui_frame_configuration2, text="Exportar log", command=self.export_log)
        self.gui_button_export_log.pack(side=tk.LEFT)

        self.gui_checkbutton_export_log_real_time_state = tk.BooleanVar(value=False)
        self.gui_checkbutton_export_log_real_time = tk.Checkbutton(gui_frame_configuration2, text="Exportar log en tiempo real", variable=self.gui_checkbutton_export_log_real_time_state, indicatoron=False, command=self.export_log_real_time)
        self.gui_checkbutton_export_log_real_time.pack(side=tk.LEFT, padx=(10,0))

if __name__ == "__main__":
    app = MonitorApp()
    app.main()