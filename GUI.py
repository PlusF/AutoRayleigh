import time
import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors, CameraCapabilities
import SKStage


UM_PER_PULSE = 0.01
WIDTH = 10


class AndorWindow(tk.Frame):
    ACQUISITION_MODES = ['Single Scan']
    READ_MODES = ['Full Vertical Binning']

    def __init__(self, master=None, sdk=None):
        super().__init__(master)
        self.master = master
        self.sdk = sdk
        self.codes = atmcd_codes
        self.errors = atmcd_errors
        # self.helper = CameraCapabilities.CapabilityHelper(self.sdk)  ####
        self.std_temperature = -80

        self.create_widgets()

        # if self.sdk.Initialize('') == self.errors.Error_Codes.DRV_SUCCESS:  ####
        #     self.msg.set('successfully initialized')
        # else:
        #     self.msg.set('initialization failed')

    def create_widgets(self):
        self.msg = tk.StringVar(value='initializing...')
        self.temperature = tk.IntVar(value=0)
        self.exposure_time = tk.DoubleVar(value=30)

        self.frame_config = ttk.LabelFrame(master=self, text='Andor')
        self.frame_config.grid(row=0, column=0, sticky=('N', 'E', 'S', 'W'), padx=10, pady=10)
        self.frame_graph = ttk.LabelFrame(master=self, text='Spectrum')
        self.frame_graph.grid(row=0, column=1, sticky=('N', 'E', 'S', 'W'), padx=10, pady=10)

        # Andor機器用ウィジェット
        self.label_msg = ttk.Label(master=self.frame_config, textvariable=self.msg)
        self.button_cooler = ttk.Button(master=self.frame_config, text='Cooler ON', command=self.cooler_on, width=WIDTH)
        self.label_std_temperature = ttk.Label(master=self.frame_config, text=self.std_temperature)
        self.label_temperature = ttk.Label(master=self.frame_config, textvariable=self.temperature, background='red', foreground='white')
        self.button_acquire = ttk.Button(master=self.frame_config, text='Acquire', command=self.acquire, state=tk.DISABLED, width=WIDTH)

        self.label_msg.grid(row=0, column=0)
        self.button_cooler.grid(row=1, column=0)
        self.label_std_temperature.grid(row=2, column=0)
        self.label_temperature.grid(row=3, column=0)
        self.button_acquire.grid(row=4, column=0)

        # グラフ関係
        self.fig = plt.figure(figsize=(4, 4))
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().grid(row=0, column=1)
        self.draw()

    def draw(self):
        self.ax.plot(np.linspace(0, 10), np.sin(np.linspace(0, 10)))
        self.canvas.draw()

    def cooler_on(self):
        self.sdk.SetTemperature(self.std_temperature)
        self.sdk.CoolerON()
        self.button_cooler.config(state=tk.DISABLED)
        self.update_temperature()


    def update_temperature(self):
        ret, temperature = self.sdk.GetTemperature()
        self.temperature.set(temperature)
        if ret != self.errors.Error_Codes.DRV_TEMP_STABILIZED:
            self.msg.set('cooling...')
            self.master.after(3000, self.update_temperature)
        else:
            self.msg.set('temperature stabilized')
            self.label_temperature.config(background='blue')
            self.button_acquire.config(state=tk.ACTIVE)

    def acquire(self):
        self.sdk.SetAcquisitionMode(self.codes.Acquisition_Mode.SINGLE_SCAN)
        self.sdk.SetReadMode(self.codes.Read_Mode.FULL_VERTICAL_BINNING)
        self.sdk.SetTriggerMode(self.codes.Trigger_Mode.INTERNAL)
        ret, xpixels, ypixels = self.sdk.GetDetector()
        self.sdk.SetExposureTime(2)
        # self.sdk.SetAccumulationCircleTime(6)
        self.sdk.SetFilterMode(2)
        ret, spec = self.sdk.acquire()
        # self.sdk.acqire_series(length=3)

    # def set_bg(self):
    #     ret, arr = self.sdk.SetBackground(size=1)

    # def abort(self):
    #     self.sdk.AbortAcquisition()

    # def get_status(self):
    #     ret, status = self.sdk.GetStatus()


class SKWindow(tk.Frame):
    def __init__(self, master=None, ser=None):
        super().__init__(master)
        self.master = master
        self.sc = SKStage.StageController(ser)

        self.create_widgets()

        # self.update()  ####

    def create_widgets(self):
        self.start = [0, 0, 0]
        self.x_st = tk.DoubleVar(value=0)
        self.y_st = tk.DoubleVar(value=0)
        self.z_st = tk.DoubleVar(value=0)
        self.goal = [0, 0, 0]
        self.x_gl = tk.DoubleVar(value=0)
        self.y_gl = tk.DoubleVar(value=0)
        self.z_gl = tk.DoubleVar(value=0)

        self.frame_coord = ttk.LabelFrame(master=self, text='Stage')
        self.frame_coord.grid(row=0, column=0, sticky=('N', 'E', 'S', 'W'), padx=10, pady=10)

        self.label_x = ttk.Label(master=self.frame_coord, text='x [\u03bcm]')
        self.label_y = ttk.Label(master=self.frame_coord, text='y [\u03bcm]')
        self.label_z = ttk.Label(master=self.frame_coord, text='z [\u03bcm]')
        self.label_st = ttk.Label(master=self.frame_coord, text='start')
        self.label_cr = ttk.Label(master=self.frame_coord, text='current')
        self.label_gl = ttk.Label(master=self.frame_coord, text='goal')
        self.label_x_st = ttk.Label(master=self.frame_coord, textvariable=self.x_st)
        self.label_y_st = ttk.Label(master=self.frame_coord, textvariable=self.y_st)
        self.label_z_st = ttk.Label(master=self.frame_coord, textvariable=self.z_st)
        self.entry_x = ttk.Entry(master=self.frame_coord, width=WIDTH)
        self.entry_y = ttk.Entry(master=self.frame_coord, width=WIDTH)
        self.entry_z = ttk.Entry(master=self.frame_coord, width=WIDTH)
        self.label_x_gl = ttk.Label(master=self.frame_coord, textvariable=self.x_gl)
        self.label_y_gl = ttk.Label(master=self.frame_coord, textvariable=self.y_gl)
        self.label_z_gl = ttk.Label(master=self.frame_coord, textvariable=self.z_gl)
        self.button_set_start = ttk.Button(master=self.frame_coord, text='Set Start', command=self.set_start, width=WIDTH)
        self.button_go = ttk.Button(master=self.frame_coord, text='Go', command=self.go, width=WIDTH)
        self.button_set_goal = ttk.Button(master=self.frame_coord, text='Set Goal', command=self.set_goal, width=WIDTH)
        self.entry_num_step = ttk.Entry(master=self.frame_coord, width=WIDTH)
        self.button_step = ttk.Button(master=self.frame_coord, text='Step', command=self.step, width=WIDTH)

        row_0 = 0
        row_1 = 1
        row_2 = 4
        col_0 = 1
        col_1 = 2
        col_2 = 3

        self.label_st.grid(row=row_0, column=col_0)
        self.label_cr.grid(row=row_0, column=col_1)
        self.label_gl.grid(row=row_0, column=col_2)
        self.label_x.grid(row=row_1, column=0)
        self.label_y.grid(row=row_1 + 1, column=0)
        self.label_z.grid(row=row_1 + 2, column=0)
        self.label_x_st.grid(row=row_1, column=col_0)
        self.label_y_st.grid(row=row_1 + 1, column=col_0)
        self.label_z_st.grid(row=row_1 + 2, column=col_0)
        self.entry_x.grid(row=row_1, column=col_1)
        self.entry_y.grid(row=row_1 + 1, column=col_1)
        self.entry_z.grid(row=row_1 + 2, column=col_1)
        self.label_x_gl.grid(row=row_1, column=col_2)
        self.label_y_gl.grid(row=row_1 + 1, column=col_2)
        self.label_z_gl.grid(row=row_1 + 2, column=col_2)

        self.button_set_start.grid(row=row_2, column=col_0)
        self.button_go.grid(row=row_2, column=col_1)
        self.button_set_goal.grid(row=row_2, column=col_2)

        self.entry_num_step.grid(row=row_2 + 1, column=col_1)
        self.button_step.grid(row=row_2 + 1, column=col_2)


    def update(self):
        coord = self.sc.get_pos()
        self.entry_x.delete(0, tk.END)
        self.entry_y.delete(0, tk.END)
        self.entry_z.delete(0, tk.END)
        self.entry_x.insert(tk.END, coord[0] * UM_PER_PULSE)
        self.entry_y.insert(tk.END, coord[1] * UM_PER_PULSE)
        self.entry_z.insert(tk.END, coord[2] * UM_PER_PULSE)
        self.master.after(200, self.update)

    def set_start(self):
        self.start = np.array(self.sc.get_pos())  # ゴール設定
        self.x_st.set(self.start[0] * UM_PER_PULSE)
        self.y_st.set(self.start[1] * UM_PER_PULSE)
        self.z_st.set(self.start[2] * UM_PER_PULSE)

    def set_goal(self):
        self.goal = np.array(self.sc.get_pos())  # ゴール設定
        self.x_gl.set(self.goal[0] * UM_PER_PULSE)
        self.y_gl.set(self.goal[1] * UM_PER_PULSE)
        self.z_gl.set(self.goal[2] * UM_PER_PULSE)

    def go(self):
        x = self.entry_x.get()
        y = self.entry_y.get()
        z = self.entry_z.get()
        self.sc.move_linear([x, y, z])

    def step(self, current_step):
        num_step = self.entry_num_step.get()
