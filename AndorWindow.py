import os
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors


UM_PER_PULSE = 0.01
WIDTH = 10


class AndorWindow(tk.Frame):
    def __init__(self, master=None, sdk: atmcd = None):
        super().__init__(master)
        self.master = master
        self.sdk = sdk
        self.codes = atmcd_codes
        self.errors = atmcd_errors
        self.spec = None
        self.xpixels = None
        self.std_temperature = -80  # <= 0っぽい

        self.create_widgets()

    def create_widgets(self):
        self.msg = tk.StringVar(value="初期化してください")
        self.temperature = tk.StringVar(value='現在：20℃')
        self.acquisition_mode = self.codes.Acquisition_Mode.SINGLE_SCAN
        self.read_mode = self.codes.Read_Mode.FULL_VERTICAL_BINNING
        self.extension = tk.StringVar(value='.sif')

        self.frame_config = ttk.LabelFrame(master=self, text='Andor')
        self.frame_config.grid(row=0, column=0, sticky='NESW', padx=10, pady=10)
        self.frame_graph = ttk.LabelFrame(master=self, text='Spectrum')
        self.frame_graph.grid(row=0, column=1, sticky='NESW', padx=10, pady=10)

        # Andor機器用ウィジェット
        self.button_initialize = ttk.Button(master=self.frame_config, text='Initialize', command=self.initialize, width=WIDTH, style='default.TButton', padding=[0, 15])
        self.label_msg = ttk.Label(master=self.frame_config, textvariable=self.msg)
        self.label_std_temperature = ttk.Label(master=self.frame_config, text='目標：' + str(self.std_temperature) + '℃')
        self.label_temperature = ttk.Label(master=self.frame_config, textvariable=self.temperature, background='red', foreground='white')
        self.label_exposure_time = ttk.Label(master=self.frame_config, text='露光時間：')
        self.entry_exposure_time = ttk.Entry(master=self.frame_config, width=WIDTH, justify=tk.CENTER)
        self.entry_exposure_time.config(font=('游ゴシック', 20))
        self.entry_exposure_time.insert(0, '10')
        self.label_second = ttk.Label(master=self.frame_config, text='sec')
        self.button_acquire = ttk.Button(master=self.frame_config, text='Acquire', command=self.acquire_event, state=tk.DISABLED, width=WIDTH*3, style='default.TButton')
        self.entry_filename = ttk.Entry(master=self.frame_config, width=WIDTH, justify=tk.CENTER)
        self.entry_filename.config(font=('游ゴシック', 20))
        self.entry_filename.insert(0, 'test01')
        self.combobox_extension = ttk.Combobox(master=self.frame_config, values=('.sif', '.asc'), textvariable=self.extension, width=WIDTH, justify=tk.CENTER)
        self.combobox_extension.config(font=('游ゴシック', 20))
        self.button_save = ttk.Button(master=self.frame_config, text='Save', command=self.save_as, state=tk.DISABLED, width=WIDTH, style='default.TButton')

        self.button_initialize.grid(row=0, rowspan=2, column=0)
        self.label_msg.grid(row=0, column=1, columnspan=3)
        self.label_std_temperature.grid(row=1, column=1)
        self.label_temperature.grid(row=1, column=2)
        self.label_exposure_time.grid(row=4, column=0)
        self.entry_exposure_time.grid(row=4, column=1)
        self.label_second.grid(row=4, column=2)
        self.button_acquire.grid(row=5, column=0, columnspan=3)
        self.entry_filename.grid(row=6, column=0)
        self.combobox_extension.grid(row=6, column=1)
        self.button_save.grid(row=6, column=2)

        # グラフ関係
        self.fig = plt.figure(figsize=(5, 5))
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().grid(row=0, column=0)

    def draw(self):
        if self.spec is None:
            print('No spectrum to draw')
            return False
        self.ax.cla()
        self.ax.plot(self.spec)
        self.canvas.draw()

    def initialize(self):
        if self.sdk.Initialize('') == self.errors.Error_Codes.DRV_SUCCESS:
            self.msg.set('初期化成功')
            self.label_msg.config(background='#00ff00')
        else:
            self.msg.set('初期化失敗')
            self.label_msg.config(background='#ff0000')
        self.cooler_on()

    def cooler_on(self):
        self.sdk.SetTemperature(self.std_temperature)
        self.sdk.CoolerON()
        self.update_temperature()

    def update_temperature(self):
        ret, temperature = self.sdk.GetTemperature()
        self.temperature.set('現在：' + str(temperature) + '℃')
        if ret != self.errors.Error_Codes.DRV_TEMP_STABILIZED:
            self.master.after(1000, self.update_temperature)
        else:
            self.msg.set('冷却完了')
            self.label_temperature.config(background='blue')
            self.button_acquire.config(state=tk.ACTIVE)

    def prepare_acquisition(self):
        self.sdk.handle_return(self.sdk.SetAcquisitionMode(self.acquisition_mode))
        self.sdk.handle_return(self.sdk.SetReadMode(self.read_mode))
        self.sdk.handle_return(self.sdk.SetTriggerMode(self.codes.Trigger_Mode.INTERNAL))
        ret, self.xpixels, ypixels = self.sdk.GetDetector()
        self.sdk.handle_return(ret)
        exposure_time = float(self.entry_exposure_time.get())
        self.sdk.handle_return(self.sdk.SetExposureTime(exposure_time))
        self.sdk.handle_return(self.sdk.PrepareAcquisition())

    def acquire(self):
        if self.xpixels is None:
            print('Not prepared')
            return False
        self.button_acquire.config(state=tk.DISABLED)
        self.sdk.handle_return(self.sdk.StartAcquisition())
        self.sdk.handle_return(self.sdk.WaitForAcquisition())
        ret, self.spec, first, last = self.sdk.GetImages16(1, 1, self.xpixels)
        self.sdk.handle_return(ret)
        self.draw()
        self.button_acquire.config(state=tk.ACTIVE)
        self.button_save.config(state=tk.ACTIVE)

    def acquire_event(self):
        self.prepare_acquisition()
        self.acquire()

    def save_as(self, filename=None):
        if filename is None:
            directory = os.getcwd()
            path = os.path.join(directory, self.entry_filename.get())
        else:
            path = filename

        if self.extension.get() == '.sif':
            self.save_as_sif(path + '.sif')
        elif self.extension.get() == '.asc':
            if self.spec is None:
                print('need argument "spec" to save as asc')
                return False
            self.save_as_asc(path + '.asc')

    def save_as_sif(self, path):
        self.sdk.handle_return(self.sdk.SaveAsSif(path))

    def save_as_asc(self, path):
        spec_str = list(map(lambda x: str(x) + '\n', self.spec))
        with open(path, 'w') as f:
            f.writelines(spec_str)
