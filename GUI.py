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
    def __init__(self, master=None, sdk: atmcd=None):
        super().__init__(master)
        self.master = master
        self.sdk = sdk
        self.codes = atmcd_codes
        self.errors = atmcd_errors
        # self.helper = CameraCapabilities.CapabilityHelper(self.sdk)  ####
        self.std_temperature = -80  # <= 0っぽい
        self.acquisition_mode_dict = {'Single': self.codes.Acquisition_Mode.SINGLE_SCAN,
                                      'Accumulate': self.codes.Acquisition_Mode.ACCUMULATE}
        self.read_mode_dict = {'Full Vertical Binning': self.codes.Read_Mode.FULL_VERTICAL_BINNING,
                               'Image': self.codes.Read_Mode.IMAGE}

        self.create_widgets()

        # if self.sdk.Initialize('') == self.errors.Error_Codes.DRV_SUCCESS:  ####
        #     self.msg.set('successfully initialized')
        # else:
        #     self.msg.set('initialization failed')

        # ret, min_wl, max_wl = self.sdk.GetCountConvertWavelengthRange()
        # self.sdk.handle_return(ret)
        # print(min_wl, max_wl)

    def create_widgets(self):
        self.msg = tk.StringVar(value='initializing...')
        self.temperature = tk.StringVar(value='現在：20℃')
        self.acquisition_mode = tk.StringVar(value='Single')
        self.read_mode = tk.StringVar(value='Full Vertical Binning')
        self.exposure_time = tk.DoubleVar(value=30)

        self.frame_config = ttk.LabelFrame(master=self, text='Andor')
        self.frame_config.grid(row=0, column=0, sticky='NESW', padx=10, pady=10)
        self.frame_graph = ttk.LabelFrame(master=self, text='Spectrum')
        self.frame_graph.grid(row=0, column=1, sticky='NESW', padx=10, pady=10)

        # Andor機器用ウィジェット
        self.label_msg = ttk.Label(master=self.frame_config, textvariable=self.msg, width=WIDTH)
        self.button_cooler = ttk.Button(master=self.frame_config, text='Cooler ON', command=self.cooler_on, width=WIDTH, style='default.TButton')
        self.label_std_temperature = ttk.Label(master=self.frame_config, text='目標：' + str(self.std_temperature) + '℃')
        self.label_temperature = ttk.Label(master=self.frame_config, textvariable=self.temperature, background='red', foreground='white')
        self.combobox_acquisition_mode = ttk.Combobox(master=self.frame_config, textvariable=self.acquisition_mode, values=list(self.acquisition_mode_dict.keys()), width=WIDTH, font=('游ゴシック', 20))
        self.combobox_read_mode = ttk.Combobox(master=self.frame_config, textvariable=self.read_mode, values=list(self.read_mode_dict.keys()), width=WIDTH, font=('游ゴシック', 20))
        self.entry_exposure_time = ttk.Entry(master=self.frame_config, width=WIDTH)
        self.button_take_bg = ttk.Button(master=self.frame_config, text='Take BG', command=self.take_bg, state=tk.DISABLED, width=WIDTH, style='default.TButton')
        self.button_acquire = ttk.Button(master=self.frame_config, text='Acquire', command=self.acquire, state=tk.DISABLED, width=WIDTH, style='default.TButton')
        self.button_save = ttk.Button(master=self.frame_config, text='Save', command=self.save_as_sif, state=tk.DISABLED, width=WIDTH, style='default.TButton')

        self.label_msg.grid(row=0, column=0)
        self.button_cooler.grid(row=1, column=0)
        self.label_std_temperature.grid(row=2, column=0)
        self.label_temperature.grid(row=3, column=0)
        self.combobox_acquisition_mode.grid(row=4, column=0)
        self.combobox_read_mode.grid(row=5, column=0)
        self.entry_exposure_time.grid(row=6, column=0)
        self.button_take_bg.grid(row=7, column=0)
        self.button_acquire.grid(row=8, column=0)
        self.button_save.grid(row=9, column=0)

        # グラフ関係
        self.fig = plt.figure(figsize=(4, 4))
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().grid(row=0, column=1)
        self.draw(np.sin(np.linspace(0, 10)))

    def draw(self, spec):
        self.ax.plot(spec)
        self.canvas.draw()

    def cooler_on(self):
        self.sdk.SetTemperature(self.std_temperature)
        self.sdk.CoolerON()
        self.button_cooler.config(state=tk.DISABLED)
        self.update_temperature()

    def update_temperature(self):
        ret, temperature = self.sdk.GetTemperature()
        self.temperature.set('現在：' + str(temperature) + '℃')
        if ret != self.errors.Error_Codes.DRV_TEMP_STABILIZED:
            self.msg.set('cooling...')
            self.master.after(1000, self.update_temperature)
        else:
            self.msg.set('temperature stabilized')
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
        self.sdk.handle_return(self.sdk.SetExposureTime(2))
        self.sdk.handle_return(self.sdk.PrepareAcquisition())
        self.sdk.handle_return(self.sdk.StartAcquisition())
        self.sdk.handle_return(self.sdk.WaitForAcquisition())
        return xpixels

    def take_bg(self):
        xpixels = self.prepare_acquisition()
        ret, arr = self.sdk.GetBackground(size=1)
        ret, arr = self.sdk.SetBackground(size=1)

    def acquire(self):
        xpixels = self.prepare_acquisition()
        ret, spec, first, last = self.sdk.GetImages16(0, 0, xpixels)
        self.sdk.handle_return(ret)
        self.draw(spec)
        # self.sdk.SetAccumulationCircleTime(6)

    # def abort(self):
    #     self.sdk.AbortAcquisition()

    # def get_status(self):
    #     ret, status = self.sdk.GetStatus()

    def save_as_sif(self):
        path = 'test.sif'
        self.sdk.handle_return(self.sdk.SaveAsSif(path))


class SeqButton(ttk.Button):
    def __init__(self, *args, **kwargs):
        ttk.Button.__init__(self, *args, **kwargs)
        self._is_pressed = 0
        self.bind('<Button-1>', self.pressed)
        self.bind('<ButtonRelease-1>', self.released)

    def pressed(self, event):
        self._is_pressed = 1

    def released(self, event):
        self._is_pressed = 0


class SKWindow(tk.Frame):
    def __init__(self, master=None, ser=None):
        super().__init__(master)
        self.master = master
        self.sc = SKStage.StageController(ser)

        self.create_widgets()

        # jog駆動用変数
        self.button_state_pre = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 0: 停止　1: 駆動
        self.direction_list = [
            [-1, 1, 0],  # North West (左上)
            [0, 1, 0],  # North (上)
            [1, 1, 0],  # North East (右上)
            [-1, 0, 0],  # West (左)
            [1, 0, 0],  # East (右)
            [-1, -1, 0],  # South West (左下)
            [0, -1, 0],  # South(下)
            [1, -1, 0],  # South East (右下)
            [0, 0, 1],  # UP (上昇)
            [0, 0, -1],  # DOWN (下降)
        ]
        self.button_list = [self.button_nw, self.button_n, self.button_ne, self.button_w, self.button_e, self.button_sw, self.button_s, self.button_se, self.button_up, self.button_down]

        self.update()  ####

    def create_widgets(self):
        self.start = [0, 0, 0]
        self.x_st = tk.DoubleVar(value=0)
        self.y_st = tk.DoubleVar(value=0)
        self.z_st = tk.DoubleVar(value=0)
        self.x_cr = tk.DoubleVar(value=0)
        self.y_cr = tk.DoubleVar(value=0)
        self.z_cr = tk.DoubleVar(value=0)
        self.goal = [0, 0, 0]
        self.x_gl = tk.DoubleVar(value=0)
        self.y_gl = tk.DoubleVar(value=0)
        self.z_gl = tk.DoubleVar(value=0)

        self.frame_coord = ttk.LabelFrame(master=self, text='Stage')
        self.frame_coord.grid(row=0, column=0, sticky='NESW', padx=10, pady=10)
        self.frame_buttons = ttk.Frame(master=self)
        self.frame_buttons.grid(row=1, column=0, sticky='NESW', padx=10, pady=10)

        self.label_x = ttk.Label(master=self.frame_coord, text='x [\u03bcm]')
        self.label_y = ttk.Label(master=self.frame_coord, text='y [\u03bcm]')
        self.label_z = ttk.Label(master=self.frame_coord, text='z [\u03bcm]')
        self.label_st = ttk.Label(master=self.frame_coord, text='start')
        self.label_cr = ttk.Label(master=self.frame_coord, text='current')
        self.label_gl = ttk.Label(master=self.frame_coord, text='goal')
        self.label_x_st = ttk.Label(master=self.frame_coord, textvariable=self.x_st)
        self.label_y_st = ttk.Label(master=self.frame_coord, textvariable=self.y_st)
        self.label_z_st = ttk.Label(master=self.frame_coord, textvariable=self.z_st)
        self.label_x = ttk.Label(master=self.frame_coord, textvariable=self.x_cr)
        self.label_y = ttk.Label(master=self.frame_coord, textvariable=self.y_cr)
        self.label_z = ttk.Label(master=self.frame_coord, textvariable=self.z_cr)
        self.label_x_gl = ttk.Label(master=self.frame_coord, textvariable=self.x_gl)
        self.label_y_gl = ttk.Label(master=self.frame_coord, textvariable=self.y_gl)
        self.label_z_gl = ttk.Label(master=self.frame_coord, textvariable=self.z_gl)
        self.entry_x = ttk.Entry(master=self.frame_coord, width=WIDTH)
        self.entry_y = ttk.Entry(master=self.frame_coord, width=WIDTH)
        self.entry_z = ttk.Entry(master=self.frame_coord, width=WIDTH)
        self.entry_x.config(font='游ゴシック 20')
        self.entry_y.config(font='游ゴシック 20')
        self.entry_z.config(font='游ゴシック 20')
        self.button_set_start = ttk.Button(master=self.frame_coord, text='Set Start', command=self.set_start, width=WIDTH, style='default.TButton')
        self.button_stop = ttk.Button(master=self.frame_coord, text='STOP', command=self.stop, width=WIDTH, style='red.TButton')
        self.button_set_goal = ttk.Button(master=self.frame_coord, text='Set Goal', command=self.set_goal, width=WIDTH, style='default.TButton')
        self.button_go = ttk.Button(master=self.frame_coord, text='GO', command=self.go, width=WIDTH, style='default.TButton')

        row_0 = 0
        row_1 = 1
        row_2 = 4
        col_0 = 1
        col_1 = 2
        col_2 = 3
        col_3 = 4

        self.label_st.grid(row=row_0, column=col_0)
        self.label_cr.grid(row=row_0, column=col_1)
        self.label_gl.grid(row=row_0, column=col_2)
        self.label_x.grid(row=row_1, column=0)
        self.label_y.grid(row=row_1 + 1, column=0)
        self.label_z.grid(row=row_1 + 2, column=0)
        self.label_x_st.grid(row=row_1, column=col_0)
        self.label_y_st.grid(row=row_1 + 1, column=col_0)
        self.label_z_st.grid(row=row_1 + 2, column=col_0)
        self.label_x.grid(row=row_1, column=col_1)
        self.label_y.grid(row=row_1 + 1, column=col_1)
        self.label_z.grid(row=row_1 + 2, column=col_1)
        self.label_x_gl.grid(row=row_1, column=col_2)
        self.label_y_gl.grid(row=row_1 + 1, column=col_2)
        self.label_z_gl.grid(row=row_1 + 2, column=col_2)
        self.entry_x.grid(row=row_1, column=col_3)
        self.entry_y.grid(row=row_1 + 1, column=col_3)
        self.entry_z.grid(row=row_1 + 2, column=col_3)

        self.button_set_start.grid(row=row_2, column=col_0)
        self.button_stop.grid(row=row_2, column=col_1)
        self.button_set_goal.grid(row=row_2, column=col_2)
        self.button_go.grid(row=row_2, column=col_3)

        self.button_nw = SeqButton(master=self.frame_buttons, text='↖', width=WIDTH, padding=[0, 10], style='default.TButton')
        self.button_n = SeqButton(master=self.frame_buttons, text='↑', width=WIDTH, padding=[0, 10], style='default.TButton')
        self.button_ne = SeqButton(master=self.frame_buttons, text='↗', width=WIDTH, padding=[0, 10], style='default.TButton')
        self.button_w = SeqButton(master=self.frame_buttons, text='←', width=WIDTH, padding=[0, 10], style='default.TButton')
        self.button_e = SeqButton(master=self.frame_buttons, text='→', width=WIDTH, padding=[0, 10], style='default.TButton')
        self.button_sw = SeqButton(master=self.frame_buttons, text='↙', width=WIDTH, padding=[0, 10], style='default.TButton')
        self.button_s = SeqButton(master=self.frame_buttons, text='↓', width=WIDTH, padding=[0, 10], style='default.TButton')
        self.button_se = SeqButton(master=self.frame_buttons, text='↘', width=WIDTH, padding=[0, 10], style='default.TButton')
        self.button_up = SeqButton(master=self.frame_buttons, text='UP', width=WIDTH, padding=[0, 10], style='default.TButton')
        self.button_down = SeqButton(master=self.frame_buttons, text='DOWN', width=WIDTH, padding=[0, 10], style='default.TButton')

        self.button_nw.grid(row=0, column=0)
        self.button_n.grid(row=0, column=1)
        self.button_ne.grid(row=0, column=2)
        self.button_w.grid(row=1, column=0)
        self.button_e.grid(row=1, column=2)
        self.button_sw.grid(row=2, column=0)
        self.button_s.grid(row=2, column=1)
        self.button_se.grid(row=2, column=2)
        self.button_up.grid(row=0, column=3)
        self.button_down.grid(row=2, column=3)

    def check_button_state(self):
        for i, (state_pre, button) in enumerate(zip(self.button_state_pre, self.button_list)):
            state_now = button._is_pressed
            if state_now - state_pre == 1:
                print(f'move {i}')
                # self.sc.jog(self.direction_list[i])  ####
            elif state_now - state_pre == -1:
                print(f'stop {i}')
                # self.sc.stop_each(np.abs(self.direction_list[i]))  ####
            self.button_state_pre[i] = state_now

    def update(self):
        # self.sc.ser.read_all()  # JOGするとNGが帰ってきてしまってget_posに不具合が生じる．原因不明．嘘，治ったかも
        # coord = self.sc.get_pos()  ####
        # self.x_cr.set(round(coord[0], 2))
        # self.y_cr.set(round(coord[1], 2))
        # self.z_cr.set(round(coord[2], 2))
        self.check_button_state()
        self.master.after(100, self.update)

    def set_start(self):
        self.x_st.set(self.x_cr.get() * UM_PER_PULSE)
        self.y_st.set(self.y_cr.get() * UM_PER_PULSE)
        self.z_st.set(self.z_cr.get() * UM_PER_PULSE)

    def set_goal(self):
        self.x_gl.set(self.x_cr.get() * UM_PER_PULSE)
        self.y_gl.set(self.y_cr.get() * UM_PER_PULSE)
        self.z_gl.set(self.z_cr.get() * UM_PER_PULSE)

    def stop(self):
        self.sc.stop_emergency()

    def go(self):
        x = (float(self.entry_x.get()) - float(self.x_cr.get())) / UM_PER_PULSE
        y = (float(self.entry_x.get()) - float(self.y_cr.get())) / UM_PER_PULSE
        z = (float(self.entry_x.get()) - float(self.z_cr.get())) / UM_PER_PULSE
        self.sc.move_linear([x, y, z])

    def step(self, current_step):
        pass


