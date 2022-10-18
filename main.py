import tkinter as tk
from tkinter import ttk
import os, time, serial, threading
import numpy as np
from ConfigLoader import ConfigLoader
from HSC103Controller import HSC103Controller
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
if os.name == 'nt':
    from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors
else:
    atmcd =  atmcd_codes = atmcd_errors = None


UM_PER_PULSE = 0.01
WIDTH = 10
FONT = ('游ゴシック', 20)


class MinimalWindow(tk.Frame):
    def __init__(self, master, sdk, ser, cl=None):
        super().__init__(master)
        self.master = master
        self.master.title('SCANT')
        self.sdk = sdk
        self.hsc = HSC103Controller(ser)
        self.cl = cl

        self.spec = None

        self.create_widgets()

        self.acquiring = False
        self.quit_flag = False
        self.create_and_start_thread_pos()
        self.create_thread_acq()

    def set_style(self):
        s = ttk.Style()
        if os.name == 'nt':
            s.theme_use('winnative')
        s.configure('TLabel', font=('游ゴシック', 20))
        s.configure('TEntry', font=('游ゴシック', 20))
        s.configure('TButton', font=('游ゴシック', 20))
        s.configure('red.TButton', font=('游ゴシック', 20), background='#ff0000', foreground='#ff0000')

    def create_and_start_thread_pos(self):
        # update_positionの受信待ちで画面がフリーズしないようthreadを立てる
        self.thread_pos = threading.Thread(target=self.update_position)
        self.thread_pos.daemon = True
        self.thread_pos.start()

    def create_thread_acq(self):
        # autoで画面がフリーズしないようthreadを立てる
        self.thread_acq = threading.Thread(target=self.auto_acquire_and_save)
        self.thread_acq.daemon = True

    def start_thread_acq(self):
        self.thread_acq.start()

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
        # self.entry_x.config(font='游ゴシック 20')
        # self.entry_y.config(font='游ゴシック 20')
        # self.entry_z.config(font='游ゴシック 20')
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
        self.entry_exposure_time = ttk.Entry(master=self.frame_andor, width=WIDTH, justify=tk.CENTER)
        # self.entry_exposure_time.config(font=('游ゴシック', 20))
        self.entry_exposure_time.insert(0, '10')
        self.label_second = ttk.Label(master=self.frame_andor, text='sec')
        self.button_acquire = ttk.Button(master=self.frame_andor, text='Acquire', command=self.acquire, state=tk.DISABLED, width=WIDTH * 3)
        self.entry_filename = ttk.Entry(master=self.frame_andor, width=WIDTH, justify=tk.CENTER)
        # self.entry_filename.config(font=('游ゴシック', 20))
        self.entry_filename.insert(0, 'test01')
        self.combobox_extension = ttk.Combobox(master=self.frame_andor, values=('.sif', '.asc'), textvariable=self.extension, width=WIDTH, justify=tk.CENTER)
        self.combobox_extension.config(font=('游ゴシック', 20))
        self.button_save = ttk.Button(master=self.frame_andor, text='Save', command=self.save_as, state=tk.DISABLED, width=WIDTH)
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

        # frame_auto
        self.label_step = ttk.Label(master=self.frame_auto, text='回数：')
        self.max_step = tk.IntVar(value=10)
        self.entry_step = ttk.Entry(master=self.frame_auto, textvariable=self.max_step, width=WIDTH, justify=tk.CENTER)
        # self.entry_step.config(font=('游ゴシック', 20))
        self.button_start = ttk.Button(master=self.frame_auto, text='START', command=self.start_auto, width=WIDTH, style='default.TButton')
        self.number = tk.IntVar(value=0)
        self.progressbar = ttk.Progressbar(master=self.frame_auto, orient=tk.HORIZONTAL, variable=self.number, maximum=10, length=200, mode='determinate')
        self.state = tk.StringVar(value='キャリブレーション用ファイルは保存しましたか？')
        self.label_state = ttk.Label(master=self.frame_auto, textvariable=self.state)
        self.label_step.grid(row=0, column=0)
        self.entry_step.grid(row=0, column=1)
        self.button_start.grid(row=0, column=2)
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
        while not self.quit_flag:
            if self.hsc is None:
                self.x_cr.set(self.x_cr.get() + 1)
                self.y_cr.set(self.y_cr.get() + 1)
                self.z_cr.set(self.z_cr.get() + 1)
            else:
                x, y, z = self.hsc.get_position()
                self.x_cr.set(round(x, 2))
                self.y_cr.set(round(y, 2))
                self.z_cr.set(round(z, 2))
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
        if self.sdk.Initialize('') == atmcd_errors.Error_Codes.DRV_SUCCESS:
            self.msg.set('初期化成功')
            self.label_msg.config(background='#00ff00')
        else:
            self.msg.set('初期化失敗')
            self.label_msg.config(background='#ff0000')
        # coolerをonに
        self.sdk.SetTemperature(self.cl.temperature)
        self.sdk.CoolerON()
        self.update_temperature()

    def update_temperature(self):
        ret, temperature = self.sdk.GetTemperature()
        self.temperature.set('現在：' + str(temperature) + '℃')
        if ret != atmcd_errors.Error_Codes.DRV_TEMP_STABILIZED:
            self.master.after(1000, self.update_temperature)
        else:
            self.msg.set('冷却完了')
            self.label_temperature.config(background='blue')
            self.button_acquire.config(state=tk.ACTIVE)

    def prepare_acquisition(self):
        self.sdk.handle_return(self.sdk.SetAcquisitionMode(atmcd_codes.Acquisition_Mode.SINGLE_SCAN))
        self.sdk.handle_return(self.sdk.SetReadMode(atmcd_codes.Read_Mode.FULL_VERTICAL_BINNING))
        self.sdk.handle_return(self.sdk.SetTriggerMode(atmcd_codes.Trigger_Mode.INTERNAL))
        ret, self.xpixels, ypixels = self.sdk.GetDetector()
        self.sdk.handle_return(ret)
        exposure_time = float(self.entry_exposure_time.get())
        self.sdk.handle_return(self.sdk.SetExposureTime(exposure_time))
        self.sdk.handle_return(self.sdk.PrepareAcquisition())

    def acquire(self):
        self.prepare_acquisition()
        self.button_acquire.config(state=tk.DISABLED)
        self.sdk.handle_return(self.sdk.StartAcquisition())
        self.sdk.handle_return(self.sdk.WaitForAcquisition())
        ret, self.spec, first, last = self.sdk.GetImages16(1, 1, self.xpixels)
        self.sdk.handle_return(ret)
        self.draw()
        self.button_acquire.config(state=tk.ACTIVE)
        self.button_save.config(state=tk.ACTIVE)

    def draw(self):
        if self.spec is None:
            print('No spectrum to draw')
            return False
        self.ax.cla()
        self.ax.plot(self.spec)
        self.canvas.draw()

    def save_as(self, filename=None):
        if filename is None:
            directory = os.getcwd()
            path = os.path.join(directory, self.entry_filename.get())
        else:
            path = filename

        if self.extension.get() == '.sif':
            self.save_as_sif(path + '.sif')
        elif self.extension.get() == '.asc':
            self.save_as_asc(path + '.asc')
        else:
            self.state.set('Invalid extension')

    def save_as_sif(self, path):
        self.sdk.handle_return(self.sdk.SaveAsSif(path))

    def save_as_asc(self, path):
        spec_str = list(map(lambda x: str(x) + '\n', self.spec))
        with open(path, 'w') as f:
            f.writelines(spec_str)

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
        self.state.set('Setting up...')

        self.hsc.set_speed_max()
        # 座標計算
        self.start = np.array(self.get_start()).astype('float') / UM_PER_PULSE
        self.goal = np.array(self.get_goal()).astype('float') / UM_PER_PULSE

        # start位置に移動
        self.hsc.move_abs(self.start)
        distance = np.linalg.norm(np.array(self.get_current()) - self.start)
        interval = distance / 1000  # set_speed_max()で20000um/s以上になっているはず・・・だがうまくいっていない
        time.sleep(max([1, interval]))  # 距離が近くても念のため1秒は待つ

        # ProgressBarの設定
        self.progressbar.config(maximum=self.max_step.get() + 1)
        self.number.set(0)
        self.interval = np.linalg.norm(self.goal - self.start) / 1000

        self.start_thread_acq()

    def auto_acquire_and_save(self):
        self.acquiring = True
        number = 0
        step = int(self.entry_step.get())
        while number <= step and not self.quit_flag:
            self.state.set(f'Acquisition {number} of {step}')

            point = self.start + (self.goal - self.start) * number / step
            self.hsc.move_abs(point)
            time.sleep(max([1, self.interval]))  # TODO: 到着を確認してから次に進む

            self.acquire()

            folder = os.path.join(os.getcwd(), 'data')
            if not os.path.exists(folder):
                os.mkdir(folder)
            self.save_as_asc(os.path.join(folder, f'{number}of{step}.asc'))

            number += 1
            self.number.set(number)

        self.acquiring = False

    def quit(self):
        self.quit_flag = True
        # mainloop内でthreadを作っているので、mainloop内でjoinさせないとバグる
        if self.acquiring:
            print('Thread is still working. Please wait.')
            self.thread_pos.join()
            self.thread_acq.join()

        self.master.destroy()


def main():
    cl = ConfigLoader('./config.json')
    if cl.mode == 'RELEASE':
        sdk = atmcd()
        ser = serial.Serial(cl.port, cl.baudrate)
    elif cl.mode == 'DEBUG':
        sdk = ser = None
    else:
        raise ValueError('Error with config.json. mode must be DEBUG or RELEASE.')

    root = tk.Tk()
    root.option_add("*font", FONT)
    root.protocol('WM_DELETE_WINDOW', (lambda: 'pass')())  # QUITボタン以外の終了操作を許可しない
    app = MinimalWindow(master=root, sdk=sdk, ser=ser, cl=cl)
    app.mainloop()

    if cl.mode == 'RELEASE':
        sdk.ShutDown()
        ser.close()


if __name__ == '__main__':
    main()
