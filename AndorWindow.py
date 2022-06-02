import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors, CameraCapabilities


UM_PER_PULSE = 0.01
WIDTH = 10


class AndorWindow(tk.Frame):
    def __init__(self, master=None, sdk: atmcd=None):
        super().__init__(master)
        self.master = master
        self.sdk = sdk
        self.codes = atmcd_codes
        self.errors = atmcd_errors
        # self.helper = CameraCapabilities.CapabilityHelper(self.sdk)  ####
        self.std_temperature = -80  # <= 0っぽい
        self.acquisition_mode_dict = {'Single': self.codes.Acquisition_Mode.SINGLE_SCAN,  # ExposureTimeのみ
                                      'Accumulate': self.codes.Acquisition_Mode.ACCUMULATE}  # ExposureTime, AccumulationCycleTime, NumberOfAccumulation
        self.read_mode_dict = {'Full Vertical Binning': self.codes.Read_Mode.FULL_VERTICAL_BINNING,
                               'Single Track': self.codes.Read_Mode.SINGLE_TRACK,  # Single Trackモードでは範囲指定の必要あり　SetSingleTrack(128, 20)
                               'Image': self.codes.Read_Mode.IMAGE}  # ImageモードではSetImage(1, 1, 1, 1024, 1, 256)

        self.create_widgets()

        # ret, min_wl, max_wl = self.sdk.GetCountConvertWavelengthRange()
        # self.sdk.handle_return(ret)
        # print(min_wl, max_wl)

    def create_widgets(self):
        self.msg = tk.StringVar(value="初期化してください")
        self.temperature = tk.StringVar(value='現在：20℃')
        self.acquisition_mode = tk.StringVar(value='Single')
        self.read_mode = tk.StringVar(value='Full Vertical Binning')

        self.frame_config = ttk.LabelFrame(master=self, text='Andor')
        self.frame_config.grid(row=0, column=0, sticky='NESW', padx=10, pady=10)
        self.frame_graph = ttk.LabelFrame(master=self, text='Spectrum')
        self.frame_graph.grid(row=0, column=1, sticky='NESW', padx=10, pady=10)

        # Andor機器用ウィジェット
        self.button_initialize = ttk.Button(master=self.frame_config, text='Initialize', command=self.initialize, width=WIDTH, style='default.TButton', padding=[0, 15])
        self.label_msg = ttk.Label(master=self.frame_config, textvariable=self.msg)
        self.label_std_temperature = ttk.Label(master=self.frame_config, text='目標：' + str(self.std_temperature) + '℃')
        self.label_temperature = ttk.Label(master=self.frame_config, textvariable=self.temperature, background='red', foreground='white')
        self.combobox_acquisition_mode = ttk.Combobox(master=self.frame_config, textvariable=self.acquisition_mode, values=list(self.acquisition_mode_dict.keys()), width=WIDTH, justify=tk.CENTER, font=('游ゴシック', 20))
        self.combobox_read_mode = ttk.Combobox(master=self.frame_config, textvariable=self.read_mode, values=list(self.read_mode_dict.keys()), width=WIDTH, justify=tk.CENTER, font=('游ゴシック', 20))
        self.entry_exposure_time = ttk.Entry(master=self.frame_config, width=WIDTH, justify=tk.CENTER)
        self.entry_exposure_time.config(font=('游ゴシック', 20))
        self.entry_exposure_time.insert(0, '10')
        self.label_second = ttk.Label(master=self.frame_config, text='sec')
        self.button_acquire = ttk.Button(master=self.frame_config, text='Acquire', command=self.acquire, state=tk.DISABLED, width=WIDTH, style='default.TButton')
        self.entry_filename = ttk.Entry(master=self.frame_config, width=WIDTH, justify=tk.CENTER)
        self.entry_filename.config(font=('游ゴシック', 20))
        self.entry_filename.insert(0, 'test01')
        self.label_extension = ttk.Label(master=self.frame_config, text='.sif')
        self.button_save = ttk.Button(master=self.frame_config, text='Save', command=self.save_as_sif, state=tk.DISABLED, width=WIDTH, style='default.TButton')

        self.button_initialize.grid(row=0, rowspan=2, column=0)
        self.label_msg.grid(row=0, column=1, columnspan=3)
        self.label_std_temperature.grid(row=1, column=1)
        self.label_temperature.grid(row=1, column=2)
        self.combobox_acquisition_mode.grid(row=2, column=0)
        self.combobox_read_mode.grid(row=3, column=0)
        self.entry_exposure_time.grid(row=4, column=0)
        self.label_second.grid(row=4, column=1)
        self.button_acquire.grid(row=5, column=0)
        self.entry_filename.grid(row=6, column=0)
        self.label_extension.grid(row=6, column=1)
        self.button_save.grid(row=6, column=2)

        # グラフ関係
        self.fig = plt.figure(figsize=(4, 4))
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.draw(np.sin(np.linspace(0, 10)))

    def draw(self, spec):
        self.ax.cla()
        self.ax.plot(spec)
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
        acquisition_mode = self.combobox_acquisition_mode.get()
        read_mode = self.combobox_read_mode.get()
        self.sdk.handle_return(self.sdk.SetAcquisitionMode(self.acquisition_mode_dict[acquisition_mode]))
        self.sdk.handle_return(self.sdk.SetReadMode(self.read_mode_dict[read_mode]))
        self.sdk.handle_return(self.sdk.SetTriggerMode(self.codes.Trigger_Mode.INTERNAL))
        ret, xpixels, ypixels = self.sdk.GetDetector()
        self.sdk.handle_return(ret)
        exposure_time = float(self.entry_exposure_time.get())
        self.sdk.handle_return(self.sdk.SetExposureTime(exposure_time))
        self.sdk.handle_return(self.sdk.PrepareAcquisition())
        return xpixels

    def acquire(self):
        xpixels = self.prepare_acquisition()
        self.button_acquire.config(state=tk.DISABLED)
        self.sdk.handle_return(self.sdk.StartAcquisition())
        self.sdk.handle_return(self.sdk.WaitForAcquisition())
        ret, spec, first, last = self.sdk.GetImages16(0, 0, xpixels)
        self.sdk.handle_return(ret)
        self.draw(spec)
        self.button_acquire.config(state=tk.ACTIVE)
        self.button_save.config(state=tk.ACTIVE)
        return spec

    # def abort(self):
    #     self.sdk.AbortAcquisition()

    # def get_status(self):
    #     ret, status = self.sdk.GetStatus()

    def save_as_sif(self, filename=None):
        if filename is None:
            directory = 'C:/Users/optical group/Documents/Andor Solis/AutoRayleigh/'
            path = directory + self.entry_filename.get() + '.sif'
        else:
            path = filename
        self.sdk.handle_return(self.sdk.SaveAsSif(path))
