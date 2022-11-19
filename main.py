import os, time, serial, threading, sys, csv, math
import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
if os.name == 'nt':
    from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors
else:
    atmcd =  atmcd_codes = atmcd_errors = None
from ConfigLoader import ConfigLoader
from HSC103Controller import HSC103Controller
from EmptySdk import EmptySdk


UM_PER_PULSE = 0.01
WIDTH = 10
FONT = ('游ゴシック', 20)


class MinimalWindow(tk.Frame):
    def __init__(self, master, config='./config.json'):
        super().__init__(master)
        self.master = master
        self.master.title('RAS')

        self.cl = ConfigLoader(config)

        if self.cl.mode == 'RELEASE':
            folder = self.cl.folder
            if not os.path.exists(folder):
                os.mkdir(folder)

        self.open_ports()

        self.spec_accumulated = None
        self.locations = [['x', 'y', 'z']]

        self.set_style()
        self.create_widgets()

        self.create_and_start_thread_pos()

        self.update_graph()

    def open_ports(self):
        if self.cl.mode == 'RELEASE':
            self.sdk = atmcd()
            self.ser = serial.Serial(self.cl.port, self.cl.baudrate)
            self.hsc = HSC103Controller(self.ser)
        elif self.cl.mode == 'DEBUG':
            self.sdk = EmptySdk()
            self.ser = None
            self.hsc = HSC103Controller(self.ser)
        else:
            raise ValueError('Error with config.json. mode must be DEBUG or RELEASE.')

    def set_style(self):
        style = ttk.Style()
        if os.name == 'nt':
            style.theme_use('winnative')  # windowsにしかないテーマ
        style.configure('.', font=FONT)
        style.configure("red.TButton", activeforeground='red', foreground='red')

    def create_and_start_thread_pos(self):
        # update_positionの受信待ちで画面がフリーズしないようthreadを立てる
        self.thread_pos = threading.Thread(target=self.update_position)
        self.thread_pos.daemon = True
        self.thread_pos.start()

    def create_and_start_thread_cool(self):
        # update_temperature用のthreadを立てる
        self.thread_cool = threading.Thread(target=self.update_temperature)
        self.thread_cool.daemon = True
        self.thread_cool.start()

    def create_and_start_thread_acq(self):
        # autoで画面がフリーズしないようthreadを立てる
        self.thread_acq = threading.Thread(target=self.prepare_and_acquire)
        self.thread_acq.daemon = True
        self.thread_acq.start()

    def create_and_start_thread_auto(self):
        # autoで画面がフリーズしないようthreadを立てる
        self.thread_auto = threading.Thread(target=self.auto_acquire_and_save)
        self.thread_auto.daemon = True
        self.thread_auto.start()

    def create_widgets(self):
        self.frame_hsc = ttk.LabelFrame(master=self.master, text='HSC-103')
        self.frame_andor = ttk.LabelFrame(master=self.master, text='Andor')
        self.frame_auto = ttk.LabelFrame(master=self.master, text='Auto Scan')
        self.frame_graph = ttk.LabelFrame(master=self.master, text='Spectrum')
        self.frame_hsc.grid(row=0, column=0, sticky='NESW')
        self.frame_andor.grid(row=1, column=0, sticky='NESW')
        self.frame_auto.grid(row=2, column=0, sticky='NESW')
        self.frame_graph.grid(row=0, column=1, rowspan=4, sticky='NESW')
        # frame_hsc
        self.x_st = tk.DoubleVar(value=0)
        self.y_st = tk.DoubleVar(value=0)
        self.z_st = tk.DoubleVar(value=0)
        self.x_cr = tk.DoubleVar(value=0)
        self.y_cr = tk.DoubleVar(value=0)
        self.z_cr = tk.DoubleVar(value=0)
        self.x_gl = tk.DoubleVar(value=0)
        self.y_gl = tk.DoubleVar(value=0)
        self.z_gl = tk.DoubleVar(value=0)
        self.x_go = tk.DoubleVar(value=0)
        self.y_go = tk.DoubleVar(value=0)
        self.z_go = tk.DoubleVar(value=0)
        self.label_x = ttk.Label(master=self.frame_hsc, text='x [\u03bcm]')
        self.label_y = ttk.Label(master=self.frame_hsc, text='y [\u03bcm]')
        self.label_z = ttk.Label(master=self.frame_hsc, text='z [\u03bcm]')
        self.label_st = ttk.Label(master=self.frame_hsc, text='start')
        self.label_cr = ttk.Label(master=self.frame_hsc, text='current')
        self.label_gl = ttk.Label(master=self.frame_hsc, text='goal')
        self.label_x_st = ttk.Label(master=self.frame_hsc, textvariable=self.x_st)
        self.label_y_st = ttk.Label(master=self.frame_hsc, textvariable=self.y_st)
        self.label_z_st = ttk.Label(master=self.frame_hsc, textvariable=self.z_st)
        self.label_x = ttk.Label(master=self.frame_hsc, textvariable=self.x_cr)
        self.label_y = ttk.Label(master=self.frame_hsc, textvariable=self.y_cr)
        self.label_z = ttk.Label(master=self.frame_hsc, textvariable=self.z_cr)
        self.label_x_gl = ttk.Label(master=self.frame_hsc, textvariable=self.x_gl)
        self.label_y_gl = ttk.Label(master=self.frame_hsc, textvariable=self.y_gl)
        self.label_z_gl = ttk.Label(master=self.frame_hsc, textvariable=self.z_gl)
        self.entry_x = ttk.Entry(master=self.frame_hsc, textvariable=self.x_go, width=WIDTH, justify=tk.CENTER)
        self.entry_y = ttk.Entry(master=self.frame_hsc, textvariable=self.y_go, width=WIDTH, justify=tk.CENTER)
        self.entry_z = ttk.Entry(master=self.frame_hsc, textvariable=self.z_go, width=WIDTH, justify=tk.CENTER)
        self.button_set_start = ttk.Button(master=self.frame_hsc, text='Set Start', command=self.set_start, width=WIDTH)
        self.button_set_goal = ttk.Button(master=self.frame_hsc, text='Set Goal', command=self.set_goal, width=WIDTH)
        self.button_go = ttk.Button(master=self.frame_hsc, text='GO', command=self.go, width=WIDTH)
        self.button_stop = ttk.Button(master=self.frame_hsc, text='STOP', command=self.stop, width=WIDTH, style='red.TButton')
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
        self.button_set_goal.grid(row=row_2, column=col_2)
        self.button_go.grid(row=row_2, column=col_3)
        self.button_stop.grid(row=row_2+1, column=col_0, columnspan=4, sticky=tk.NSEW)

        # frame_andor
        self.msg = tk.StringVar(value="初期化してください")
        self.temperature = tk.StringVar(value='現在：20℃')
        self.extension = tk.StringVar(value='.sif')
        self.button_initialize = ttk.Button(master=self.frame_andor, text='Initialize', command=self.initialize, width=WIDTH, padding=[0, 15])
        self.label_msg = ttk.Label(master=self.frame_andor, textvariable=self.msg)
        self.label_std_temperature = ttk.Label(master=self.frame_andor, text='目標：' + str(self.cl.temperature) + '℃')
        self.label_temperature = ttk.Label(master=self.frame_andor, textvariable=self.temperature, background='red', foreground='white')
        self.label_exposure_time = ttk.Label(master=self.frame_andor, text='露光時間：')
        self.exposure_time = tk.DoubleVar(value=10)
        self.entry_exposure_time = ttk.Entry(master=self.frame_andor, textvariable=self.exposure_time, width=WIDTH, justify=tk.CENTER)
        self.label_second = ttk.Label(master=self.frame_andor, text='sec')
        self.label_accumulation_times = ttk.Label(master=self.frame_andor, text='積算回数：')
        self.accumulation_times = tk.IntVar(value=1)
        self.entry_accumulation_times = ttk.Entry(master=self.frame_andor, textvariable=self.accumulation_times, width=WIDTH, justify=tk.CENTER)
        self.label_times = ttk.Label(master=self.frame_andor, text='回')
        self.button_acquire = ttk.Button(master=self.frame_andor, text='Acquire', command=self.create_and_start_thread_acq, state=tk.DISABLED, width=WIDTH * 3)
        self.entry_filename = ttk.Entry(master=self.frame_andor, width=WIDTH, justify=tk.CENTER)
        self.entry_filename.insert(0, 'test01')
        self.combobox_extension = ttk.Combobox(master=self.frame_andor, values=('.sif', '.asc'), textvariable=self.extension, width=WIDTH, justify=tk.CENTER)
        self.combobox_extension.config(font=('游ゴシック', 20))
        self.button_save = ttk.Button(master=self.frame_andor, text='Save', command=self.save_as, state=tk.DISABLED, width=WIDTH)
        self.button_initialize.grid(row=0, rowspan=2, column=0)
        self.label_msg.grid(row=0, column=1, columnspan=3)
        self.label_std_temperature.grid(row=1, column=1)
        self.label_temperature.grid(row=1, column=2)
        self.label_exposure_time.grid(row=2, column=0)
        self.entry_exposure_time.grid(row=2, column=1)
        self.label_second.grid(row=2, column=2)
        self.label_accumulation_times.grid(row=3, column=0)
        self.entry_accumulation_times.grid(row=3, column=1)
        self.label_times.grid(row=3, column=2)
        self.button_acquire.grid(row=4, column=0, columnspan=3)
        self.entry_filename.grid(row=5, column=0)
        self.combobox_extension.grid(row=5, column=1)
        self.button_save.grid(row=5, column=2)

        # frame_auto
        self.label_step = ttk.Label(master=self.frame_auto, text='回数：')
        self.max_step = tk.IntVar(value=10)
        self.entry_step = ttk.Entry(master=self.frame_auto, textvariable=self.max_step, width=WIDTH, justify=tk.CENTER)
        self.button_start_auto = ttk.Button(master=self.frame_auto, text='START', command=self.start_auto, width=WIDTH, style='default.TButton', state=tk.DISABLED)
        self.number = tk.IntVar(value=0)
        self.progressbar = ttk.Progressbar(master=self.frame_auto, orient=tk.HORIZONTAL, variable=self.number, maximum=10, length=200, mode='determinate')
        self.state = tk.StringVar(value='Not Ready')
        self.label_state = ttk.Label(master=self.frame_auto, textvariable=self.state)
        self.label_step.grid(row=0, column=0)
        self.entry_step.grid(row=0, column=1)
        self.button_start_auto.grid(row=0, column=2)
        self.progressbar.grid(row=0, column=3)
        self.label_state.grid(row=1, column=0, columnspan=4)

        # frame_graph
        self.fig = plt.figure(figsize=(5, 5))
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        # quit
        self.button_quit = ttk.Button(master=self.master, text='QUIT', command=self.quit, style='red.TButton')
        self.button_quit.grid(row=3, column=0, sticky=tk.NSEW)

    def update_position(self):
        while True:
            x, y, z = self.hsc.get_position()
            self.x_cr.set(round(x * UM_PER_PULSE, 2))
            self.y_cr.set(round(y * UM_PER_PULSE, 2))
            self.z_cr.set(round(z * UM_PER_PULSE, 2))
            time.sleep(self.cl.dt * 0.001)

    def set_start(self):
        self.x_st.set(self.x_cr.get())
        self.y_st.set(self.y_cr.get())
        self.z_st.set(self.z_cr.get())

    def set_goal(self):
        self.x_gl.set(self.x_cr.get())
        self.y_gl.set(self.y_cr.get())
        self.z_gl.set(self.z_cr.get())

    def go(self):
        x = (float(self.entry_x.get()) - float(self.x_cr.get())) / UM_PER_PULSE
        y = (float(self.entry_y.get()) - float(self.y_cr.get())) / UM_PER_PULSE
        z = (float(self.entry_z.get()) - float(self.z_cr.get())) / UM_PER_PULSE
        self.hsc.move_linear([x, y, z])

    def stop(self):
        self.hsc.stop_emergency()

    def initialize(self):
        # 初期化
        if self.cl.mode == 'RELEASE':
            if self.sdk.Initialize('') == atmcd_errors.Error_Codes.DRV_SUCCESS:
                self.msg.set('初期化成功')
                self.label_msg.config(background='#00ff00')
                self.button_initialize.config(state=tk.DISABLED)
            else:
                self.msg.set('初期化失敗')
                self.label_msg.config(background='#ff0000')
        elif self.cl.mode == 'DEBUG':
            print('skipped initialization')
            self.msg.set('初期化成功')
            self.label_msg.config(background='#00ff00')
            self.button_initialize.config(state=tk.DISABLED)
        # coolerをonに
        self.sdk.SetTemperature(self.cl.temperature)
        self.sdk.CoolerON()
        self.create_and_start_thread_cool()

    def update_temperature(self):
        if self.cl.mode == 'RELEASE':
            while True:
                ret, temperature = self.sdk.GetTemperature()
                self.temperature.set('現在：' + str(temperature) + '℃')
                if ret == atmcd_errors.Error_Codes.DRV_TEMP_STABILIZED:
                    break
                time.sleep(self.cl.dt * 0.001)
        elif self.cl.mode == 'DEBUG':
            print('skip updating temperature')

        self.msg.set('冷却完了')
        self.label_temperature.config(background='blue')
        self.button_acquire.config(state=tk.ACTIVE)
        self.button_start_auto.config(state=tk.ACTIVE)
        self.state.set('Ready to Start')

    def prepare_acquisition(self):
        if self.cl.mode == 'RELEASE':
            self.sdk.handle_return(self.sdk.SetAcquisitionMode(atmcd_codes.Acquisition_Mode.SINGLE_SCAN))
            self.sdk.handle_return(self.sdk.SetReadMode(atmcd_codes.Read_Mode.FULL_VERTICAL_BINNING))
            self.sdk.handle_return(self.sdk.SetTriggerMode(atmcd_codes.Trigger_Mode.INTERNAL))
            ret, self.xpixels, ypixels = self.sdk.GetDetector()
            self.sdk.handle_return(ret)
            self.sdk.handle_return(self.sdk.SetExposureTime(self.exposure_time.get()))  # TODO: 露光時間入力の例外処理
            self.sdk.handle_return(self.sdk.PrepareAcquisition())
        elif self.cl.mode == 'DEBUG':
            print('prepare acquisition')

    def acquire(self):
        self.spec_accumulated = 0
        for i in range(self.accumulation_times.get()):
            self.msg.set(f'Acquisition {i + 1}/{self.accumulation_times.get()}')
            if self.cl.mode == 'RELEASE':
                self.sdk.handle_return(self.sdk.StartAcquisition())
                self.sdk.handle_return(self.sdk.WaitForAcquisition())
                ret, spec, first, last = self.sdk.GetImages16(1, 1, self.xpixels)
                self.spec_accumulated += np.array(spec)
                self.sdk.handle_return(ret)
            elif self.cl.mode == 'DEBUG':
                print('acquired')
                spec = np.sin(np.linspace(0, np.random.rand() * 10, 100))
                self.spec_accumulated += spec
                time.sleep(0.5)
        self.msg.set('Finished Acquisition')

    def update_graph(self):
        if self.spec_accumulated is None or isinstance(self.spec_accumulated, int):
            pass
        else:
            self.draw()
        self.master.after(1000, self.update_graph)

    def draw(self):
        self.ax.cla()
        self.ax.plot(self.spec_accumulated)
        self.ax.set_xticks([])
        self.canvas.draw()

    def prepare_and_acquire(self):
        self.entry_exposure_time.config(state=tk.DISABLED)
        self.entry_accumulation_times.config(state=tk.DISABLED)
        self.button_acquire.config(state=tk.DISABLED)
        self.button_save.config(state=tk.DISABLED)
        self.prepare_acquisition()
        self.acquire()
        self.entry_exposure_time.config(state=tk.ACTIVE)
        self.entry_accumulation_times.config(state=tk.ACTIVE)
        self.button_acquire.config(state=tk.ACTIVE)
        self.button_save.config(state=tk.ACTIVE)

    def save_as(self, filename=None):
        if filename is None:
            # saveボタンから呼ばれた時
            path = os.path.join(self.cl.folder, self.entry_filename.get())
        else:
            # 自動スキャンの時
            path = filename

        if self.extension.get() == '.sif':
            self.save_as_sif(path + '.sif')
        elif self.extension.get() == '.asc':
            self.save_as_asc(path + '.asc')
        else:
            self.state.set('Invalid extension')

    def save_as_sif(self, path):
        if self.cl.mode == 'RELEASE':
            self.sdk.handle_return(self.sdk.SaveAsSif(path))
        elif self.cl.mode == 'DEBUG':
            print('saved')

    def save_as_asc(self, path):
        if self.cl.mode == 'RELEASE':
            spec_str = list(map(lambda x: str(x) + '\n', self.spec_accumulated))
            with open(path, 'w') as f:
                f.writelines(spec_str)
        elif self.cl.mode == 'DEBUG':
            print('saved')

    def get_start(self):
        x = self.x_st.get()
        y = self.y_st.get()
        z = self.z_st.get()
        return [x, y, z]

    def get_current(self):
        x = self.x_cr.get()
        y = self.y_cr.get()
        z = self.z_cr.get()
        return [x, y, z]

    def get_goal(self):
        x = self.x_gl.get()
        y = self.y_gl.get()
        z = self.z_gl.get()
        return [x, y, z]

    def start_auto(self):
        if self.max_step.get() <= 0:
            self.state.set('Step must be greater than 0')
            return
        self.state.set('Setting up...')

        self.prepare_acquisition()

        self.hsc.set_speed_max()
        # 座標計算
        self.start = np.array(self.get_start()).astype('float') / UM_PER_PULSE
        current = np.array(self.get_current()).astype('float') / UM_PER_PULSE
        self.goal = np.array(self.get_goal()).astype('float') / UM_PER_PULSE

        # start位置に移動
        self.hsc.move_abs(self.start)
        distance = np.linalg.norm(np.array(current - self.start))
        time.sleep(distance / 40000 + 1)  # TODO: 到着を確認してから次に進む

        # ProgressBarの設定
        self.progressbar.config(maximum=self.max_step.get())
        self.number.set(1)

        self.create_and_start_thread_auto()

    def auto_acquire_and_save(self):
        self.entry_exposure_time.config(state=tk.DISABLED)
        self.entry_accumulation_times.config(state=tk.DISABLED)
        self.button_acquire.config(state=tk.DISABLED)
        self.button_save.config(state=tk.DISABLED)
        self.button_start_auto.config(state=tk.DISABLED)

        number = 1
        step = self.max_step.get()
        while number <= step:
            time_left = math.ceil((step - number + 1) * self.exposure_time.get() * 2  * self.accumulation_times.get() / 60)
            self.state.set(f'Acquisition {number} of {step}... {time_left} minutes left')

            point = self.start + (self.goal - self.start) * (number - 1) / (step - 1)
            self.hsc.move_abs(point)
            self.locations.append(point * UM_PER_PULSE)
            distance = np.linalg.norm(np.array(point - self.start))
            time.sleep(distance / 40000 + 1)  # TODO: 到着を確認してから次に進む

            self.acquire()

            self.save_as_asc(os.path.join(os.getcwd(), 'data', f'{number}of{step}.asc'))

            number += 1
            self.number.set(number)
            self.locations_to_csv()

        self.state.set('Auto Acquisition Finished')
        self.entry_exposure_time.config(state=tk.ACTIVE)
        self.entry_accumulation_times.config(state=tk.ACTIVE)
        self.button_acquire.config(state=tk.ACTIVE)
        self.button_save.config(state=tk.ACTIVE)
        self.button_start_auto.config(state=tk.ACTIVE)

    def locations_to_csv(self):
        if self.cl.mode == 'RELEASE':
            filename = os.path.join(self.cl.folder, 'location.csv')
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(self.locations)
        else:
            print('locations saved')

    def quit(self):
        if self.cl.mode == 'RELEASE':
            self.sdk.ShutDown()
            self.ser.close()
        self.master.destroy()
        sys.exit()  # デーモン化してあるスレッドはここで死ぬ


def main():
    root = tk.Tk()
    root.option_add("*font", FONT)
    root.protocol('WM_DELETE_WINDOW', (lambda: 'pass')())  # QUITボタン以外の終了操作を許可しない
    app = MinimalWindow(master=root, config='./config.json')
    app.mainloop()


if __name__ == '__main__':
    main()
