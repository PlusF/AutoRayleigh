import time
import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors, CameraCapabilities
import SKStage


UM_PER_PULSE = 0.01


class AndorWindow(tk.Frame):
    def __init__(self, master=None, sdk=None):
        super().__init__(master)
        self.master = master
        self.sdk = sdk
        self.codes = atmcd_codes
        self.errors = atmcd_errors
        self.helper = CameraCapabilities.CapabilityHelper(self.sdk)
        self.std_temperature = -80

        self.create_widgets()

        if self.sdk.Initialize('') == self.errors.Error_Codes.DRV_SUCCESS:
            self.msg.set('successfully initialized')
        else:
            self.msg.set('initialization failed')

    def create_widgets(self):
        self.msg = tk.StringVar(value='initializing...')
        self.temperature = tk.IntVar(value=0)

        self.fig = plt.figure(figsize=(4, 4))
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=1, rowspan=3)
        self.draw()

        self.label_msg = ttk.Label(master=self, textvariable=self.msg)
        self.button_cooler = ttk.Button(master=self, text='Cooler ON', command=self.cooler_on)
        self.label_std_temperature = ttk.Label(master=self, text=self.std_temperature)
        self.label_temperature = ttk.Label(master=self, textvariable=self.temperature, background='red', foreground='white')
        self.button_acquire = ttk.Button(master=self, text='Acquire', command=self.acquire, state=tk.DISABLED)

        self.label_msg.grid(row=0, column=0)
        self.button_cooler.grid(row=1, column=0)
        self.label_std_temperature.grid(row=2, column=0)
        self.label_temperature.grid(row=3, column=0)
        self.button_acquire.grid(row=4, column=0)

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


class SKWindow(tk.Frame):
    def __init__(self, master=None, ser=None):
        super().__init__(master)
        self.master = master
        self.sc = SKStage.StageController(ser)

        self.create_widgets()

        self.update()

    def create_widgets(self):
        self.x = tk.DoubleVar(value=0)
        self.y = tk.DoubleVar(value=0)
        self.z = tk.DoubleVar(value=0)
        self.start = [0, 0, 0]
        self.x_st = tk.DoubleVar(value=0)
        self.y_st = tk.DoubleVar(value=0)
        self.z_st = tk.DoubleVar(value=0)
        self.goal = [0, 0, 0]
        self.x_gl = tk.DoubleVar(value=0)
        self.y_gl = tk.DoubleVar(value=0)
        self.z_gl = tk.DoubleVar(value=0)
        self.label_st = ttk.Label(master=self, text='start')
        self.label_cr = ttk.Label(master=self, text='current')
        self.label_gl = ttk.Label(master=self, text='goal')
        self.label_x_st = ttk.Label(master=self, textvariable=self.x_st)
        self.label_y_st = ttk.Label(master=self, textvariable=self.y_st)
        self.label_z_st = ttk.Label(master=self, textvariable=self.z_st)
        self.label_x = ttk.Label(master=self, textvariable=self.x)
        self.label_y = ttk.Label(master=self, textvariable=self.y)
        self.label_z = ttk.Label(master=self, textvariable=self.z)
        self.label_x_gl = ttk.Label(master=self, textvariable=self.x_gl)
        self.label_y_gl = ttk.Label(master=self, textvariable=self.y_gl)
        self.label_z_gl = ttk.Label(master=self, textvariable=self.z_gl)
        self.button_set_start = ttk.Button(master=self, text='Set Start', command=self.set_start)
        self.button_set_goal = ttk.Button(master=self, text='Set Goal', command=self.set_goal)
        self.button_step = ttk.Button(master=self, text='Step', command=self.step)

        row_0 = 0
        row_1 = 1
        row_2 = 4
        col_0 = 0
        col_1 = 1
        col_2 = 2
        self.label_st.grid(row=row_0, column=col_0)
        self.label_cr.grid(row=row_0, column=col_1)
        self.label_gl.grid(row=row_0, column=col_2)
        self.label_x_st.grid(row=row_1, column=col_0)
        self.label_y_st.grid(row=row_1 + 1, column=col_0)
        self.label_z_st.grid(row=row_1 + 2, column=col_0)
        self.label_x.grid(row=row_1, column=col_1)
        self.label_y.grid(row=row_1 + 1, column=col_1)
        self.label_z.grid(row=row_1 + 2, column=col_1)
        self.label_x_gl.grid(row=row_1, column=col_2)
        self.label_y_gl.grid(row=row_1 + 1, column=col_2)
        self.label_z_gl.grid(row=row_1 + 2, column=col_2)
        self.button_set_start.grid(row=row_2, column=0, columnspan=3)
        self.button_set_goal.grid(row=row_2 + 1, column=0, columnspan=3)
        self.button_step.grid(row=row_2 + 2, column=0, columnspan=3)

        self.entry_num_step = ttk.Entry(master=self)
        self.entry_num_step.grid(row=row_2 + 3, column=0, columnspan=3)

    def update(self):
        coord = self.sc.get_pos()
        self.x.set(coord[0] * UM_PER_PULSE)
        self.y.set(coord[1] * UM_PER_PULSE)
        self.z.set(coord[2] * UM_PER_PULSE)
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

    def step(self, current_step):
        num_step = self.entry_num_step.get()
