import os, time, serial, threading, sys, csv, ctypes, math
import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ConfigLoader import ConfigLoader
from HSC103Controller import HSC103Controller
from EmptyLib import EmptyLib


UM_PER_PULSE = 0.01
WIDTH = 10
FONT = ('游ゴシック', 20)


class MinimalWindow(tk.Frame):
    def __init__(self, master, config='./config.json'):
        super().__init__(master)
        self.master = master
        self.master.title('SCANT')

        self.cl = ConfigLoader(config)

        if self.cl.mode == 'RELEASE':
            folder = self.cl.folder
            if not os.path.exists(folder):
                os.mkdir(folder)

        self.open_ports()

        self.locations = [['x', 'y', 'z']]
        self.wavelengths = self.data_accumulated = None

        self.set_style()
        self.create_widgets()

        self.create_and_start_thread_pos()

        self.update_graph()

    def open_ports(self):
        """
        RELEASE版なら、各装置との接続をセットアップする
        DEBUG版はプログラムの挙動を見られるように適宜設定する
        Returns:

        """
        if self.cl.mode == 'RELEASE':
            os.chdir(r"C:\Program Files\IVI Foundation\VISA\Win64\Bin")
            self.lib = ctypes.cdll.LoadLibrary("TLCCS_64.dll")
            self.ccs_handle = ctypes.c_int(0)
            self.lib.tlccs_init(b"USB0::0x1313::0x8089::M00331284::RAW", 1, 1, ctypes.byref(self.ccs_handle))
            self.ser = serial.Serial(self.cl.port, self.cl.baudrate, write_timeout=0)
            self.stage = HSC103Controller(self.ser)
        elif self.cl.mode == 'DEBUG':
            self.lib = EmptyLib()
            self.ccs_handle = None
            self.ser = None
            self.stage = HSC103Controller(self.ser)
        else:
            raise ValueError('Error with config.json. mode must be DEBUG or RELEASE.')

    def set_style(self):
        """
        アプリの見た目を整える
        Returns:
        """
        style = ttk.Style()
        if os.name == 'nt':
            style.theme_use('winnative')  # windowsにしかないテーマ
        style.configure('.', font=FONT)
        style.configure("red.TButton", activeforeground='red', foreground='red')

    def create_and_start_thread_pos(self):
        """
        update_positionの受信待ちで画面がフリーズしないようthreadを立てる
        Returns:
        """
        self.thread_pos = threading.Thread(target=self.update_position)
        self.thread_pos.daemon = True
        self.thread_pos.start()

    def create_and_start_thread_acq(self):
        """
        測定待ちのtime.sleepで画面がフリーズしないようthreadを立てる
        Returns:
        """
        self.thread_acq = threading.Thread(target=self.prepare_and_acquire)
        self.thread_acq.daemon = True
        self.thread_acq.start()

    def create_and_start_thread_auto(self):
        """
        auto acquisitionで画面がフリーズしないようthreadを立てる
        Returns:
        """
        self.thread_auto = threading.Thread(target=self.auto_acquire_and_save)
        self.thread_auto.daemon = True
        self.thread_auto.start()

    def create_widgets(self):
        """
        GUIアプリのウィジェットを作成
        Returns:
        """
        self.frame_hsc = ttk.LabelFrame(master=self.master, text='HSC-103')
        self.frame_thorlab = ttk.LabelFrame(master=self.master, text='CCS')
        self.frame_auto = ttk.LabelFrame(master=self.master, text='Auto Scan')
        self.frame_graph = ttk.LabelFrame(master=self.master, text='Spectrum')
        self.frame_hsc.grid(row=0, column=0, sticky='NESW')
        self.frame_thorlab.grid(row=1, column=0, sticky='NESW')
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
        self.button_stop = ttk.Button(master=self.frame_hsc, text='STOP', command=self.stage.stop_emergency, width=WIDTH, style='red.TButton')
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

        # frame_thorlab
        self.msg = tk.StringVar(value='CCS Mode')
        self.extension = tk.StringVar(value='.csv')
        self.label_msg = ttk.Label(master=self.frame_thorlab, textvariable=self.msg)
        self.label_exposure_time = ttk.Label(master=self.frame_thorlab, text='露光時間：')
        self.entry_exposure_time = ttk.Entry(master=self.frame_thorlab, width=WIDTH, justify=tk.CENTER)
        self.entry_exposure_time.insert(0, '10')
        self.label_second = ttk.Label(master=self.frame_thorlab, text='sec')
        self.button_acquire = ttk.Button(master=self.frame_thorlab, text='Acquire', command=self.create_and_start_thread_acq, width=WIDTH * 2)
        self.label_accumulation = ttk.Label(master=self.frame_thorlab, text='積算回数：')
        self.entry_accumulation = ttk.Entry(master=self.frame_thorlab, width=WIDTH, justify=tk.CENTER)
        self.entry_accumulation.insert(0, '1')
        self.label_times = ttk.Label(master=self.frame_thorlab, text='回')
        self.button_acquire = ttk.Button(master=self.frame_thorlab, text='Acquire', command=self.create_and_start_thread_acq, width=WIDTH * 2)
        self.progress_acq = tk.IntVar(value=0)
        self.progressbar_acq = ttk.Progressbar(master=self.frame_thorlab, orient=tk.HORIZONTAL, variable=self.progress_acq, maximum=10, length=200, mode='determinate')
        self.entry_filename = ttk.Entry(master=self.frame_thorlab, width=WIDTH, justify=tk.CENTER)
        self.entry_filename.insert(0, 'test01')
        self.combobox_extension = ttk.Combobox(master=self.frame_thorlab, values=tuple('.csv'), textvariable=self.extension, width=WIDTH, justify=tk.CENTER)
        self.combobox_extension.config(font=('游ゴシック', 20))
        self.button_save = ttk.Button(master=self.frame_thorlab, text='Save', command=self.save_as, width=WIDTH)
        self.label_msg.grid(row=0, column=0, columnspan=3)
        self.label_exposure_time.grid(row=1, column=0)
        self.entry_exposure_time.grid(row=1, column=1)
        self.label_second.grid(row=1, column=2)
        self.label_accumulation.grid(row=2, column=0)
        self.entry_accumulation.grid(row=2, column=1)
        self.label_times.grid(row=2, column=2)
        self.button_acquire.grid(row=3, column=0, columnspan=2)
        self.progressbar_acq.grid(row=3, column=2)
        self.entry_filename.grid(row=4, column=0)
        self.combobox_extension.grid(row=4, column=1)
        self.button_save.grid(row=4, column=2)

        # frame_auto
        self.label_step = ttk.Label(master=self.frame_auto, text='回数：')
        self.max_step = tk.IntVar(value=10)
        self.entry_step = ttk.Entry(master=self.frame_auto, textvariable=self.max_step, width=WIDTH, justify=tk.CENTER)
        self.button_start_auto = ttk.Button(master=self.frame_auto, text='START', command=self.start_auto, width=WIDTH, style='default.TButton')
        self.number = tk.IntVar(value=0)
        self.progressbar_auto = ttk.Progressbar(master=self.frame_auto, orient=tk.HORIZONTAL, variable=self.number, maximum=10, length=200, mode='determinate')
        self.state = tk.StringVar(value='Ready')
        self.label_state = ttk.Label(master=self.frame_auto, textvariable=self.state)
        self.label_step.grid(row=0, column=0)
        self.entry_step.grid(row=0, column=1)
        self.button_start_auto.grid(row=0, column=2)
        self.progressbar_auto.grid(row=0, column=3)
        self.label_state.grid(row=1, column=0, columnspan=4)

        # frame_graph
        self.fig = plt.figure(figsize=(5, 5))
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        # quit
        self.button_quit = ttk.Button(master=self.master, text='QUIT', command=self.quit, style='red.TButton')
        self.button_quit.grid(row=3, column=0, sticky=tk.NSEW)

    def update_graph(self):
        # グラフのアップデートはスレッドでは行えないのでmainloop内で定期実行する
        if self.data_accumulated is None:
            pass
        elif isinstance(self.data_accumulated, int) and self.data_accumulated == 0:
            pass
        else:
            self.draw()
        self.master.after(1000, self.update_graph)

    def draw(self):
        """
        スペクトルを描画
        Returns:
        """
        self.ax.cla()
        self.ax.plot(self.wavelengths, self.data_accumulated, linewidth=0.3)
        self.canvas.draw()

    def update_position(self):
        """
        threadで動かす関数
        config.jsonで指定されたFPSで動くように3軸ステージの座標をアップデートする
        Returns:
        """
        while True:
            x, y, z = self.stage.get_position()
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
        self.stage.move_linear([x, y, z])

    def prepare_acquisition(self):
        """
        測定のセットアップをする。と言っても露光時間の設定だけ。
        なぜかわからないが、露光時間を60秒に設定しようとするとスペクトルが得られないので
        安全をとって50秒をmaxにしている
        Returns:
        """
        # set integration time in  seconds, ranging from 1e-5 to 6e1
        exposure = float(self.entry_exposure_time.get())
        if exposure < 1e-5:
            print('exposure must be greater than 1e-5')
            exposure = 1e-5
        elif exposure > 50:
            print('exposure must be less than 50')
            exposure = 50
        self.entry_exposure_time.delete(0, tk.END)
        self.entry_exposure_time.insert(0, str(exposure))
        integration_time = ctypes.c_double(exposure)
        self.lib.tlccs_setIntegrationTime(self.ccs_handle, integration_time)

    def acquire(self):
        """
        実際の測定の部分
        startScanして、exposureの2倍の時間を待ってあげると確実にスペクトルが取得できる
        中身はほぼthorlabさんからもらったコードなので詳細は不明
        Returns:
        """
        accumulation_times = int(self.entry_accumulation.get())
        self.data_accumulated = 0
        for i in range(accumulation_times):
            if self.cl.mode == 'RELEASE':
                # start scan
                self.lib.tlccs_startScan(self.ccs_handle)
                time_to_wait = float(self.entry_exposure_time.get()) * 2.0  # exposureの2倍以上の時間を置かないとうまくシグナルが得られない
                self.wait(time_to_wait, i, accumulation_times)
                wavelengths = (ctypes.c_double * 3648)()
                self.lib.tlccs_getWavelengthData(self.ccs_handle, 0, ctypes.byref(wavelengths), ctypes.c_void_p(None), ctypes.c_void_p(None))
                self.wavelengths = np.array(wavelengths) - 10  # ざっくり -10 nm で合う
                # retrieve data
                data_array = (ctypes.c_double * 3648)()
                self.lib.tlccs_getScanData(self.ccs_handle, ctypes.byref(data_array))
                self.data_accumulated += np.array(data_array)
            elif self.cl.mode == 'DEBUG':
                print('acquiring')
                self.wait(float(self.entry_exposure_time.get()) * 2.0, i, accumulation_times)
                self.wavelengths = np.linspace(0, np.random.rand() * 10, 3000)
                self.data_accumulated += np.sin(self.wavelengths)
                print('acquired')

    def wait(self, time_to_wait, i, accumulation_times):
        """
        プログレスバーで進捗がわかるようにする
        Args:
            time_to_wait: 待ちたい時間
            i: accumulationの何回目か
            accumulation_times: 全部で何回accumulateするか
        Returns:
        """
        time_to_wait = math.ceil(time_to_wait)
        self.progress_acq.set(0)
        self.progressbar_acq.config(maximum=time_to_wait)
        for t in range(time_to_wait):
            self.msg.set(f'Acquiring... ({i + 1} / {accumulation_times}) {time_to_wait - t} seconds left')
            time.sleep(1)
            self.progress_acq.set(t + 1)
        self.msg.set('Acquisition Finished')

    def prepare_and_acquire(self):
        """
        buttonを連続で押せないようにしつつ、prepare, acquire, drawまで全てやる
        固まらないようthreadで実行する
        Returns:
        """
        self.entry_exposure_time.config(state=tk.DISABLED)
        self.entry_accumulation.config(state=tk.DISABLED)
        self.button_acquire.config(state=tk.DISABLED)
        self.button_save.config(state=tk.DISABLED)
        self.prepare_acquisition()
        self.acquire()
        self.entry_exposure_time.config(state=tk.ACTIVE)
        self.entry_accumulation.config(state=tk.ACTIVE)
        self.button_acquire.config(state=tk.ACTIVE)
        self.button_save.config(state=tk.ACTIVE)

    def save_as(self, filename=None):
        """
        スペクトルデータを保存する関数
        config.jsonでディレクトリを指定
        単発スキャンの時はエントリーボックスに入力されたファイル名で保存
        自動スキャンの時は、自動でファイル名が指定される
        Args:
            filename: ファイル名（ディレクトリは含まない）
        Returns:
        """
        if filename is None:
            # saveボタンから呼ばれた時
            directory = self.cl.folder
            path = os.path.join(directory, self.entry_filename.get())
        else:
            # 自動スキャンの時
            path = filename

        if self.extension.get() == '.csv':
            self.save_as_csv(path + '.csv')
        else:
            self.state.set('Invalid extension')

    def save_as_csv(self, path):
        """
        適切に形を整えてスペクトルをcsvファイルに格納する
        Args:
            path: 保存する(ディレクトリ+ファイル)名
        Returns:
        """
        if self.cl.mode == 'RELEASE':
            x = self.wavelengths.reshape(-1, 1)
            y = self.data_accumulated.reshape(-1, 1)
            spec = np.hstack([x, y])
            spec_str = list(map(lambda val: str(val[0]) + ',' + str(val[1]) + '\n', spec))
            with open(path, 'w') as f:
                f.writelines(spec_str)
        elif self.cl.mode == 'DEBUG':
            print(f'save to {path}')

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
        """
        自動スキャンのセットアップ
        初期設定が完了したらthreadで自動スキャンを開始する
        Returns:
        """
        if self.max_step.get() <= 0:
            self.state.set('Step must be greater than 0')
            return
        self.state.set('Setting up...')

        self.prepare_acquisition()

        self.stage.set_speed_max()
        # 座標計算
        self.start = np.array(self.get_start()).astype('float') / UM_PER_PULSE
        current = np.array(self.get_current()).astype('float') / UM_PER_PULSE
        self.goal = np.array(self.get_goal()).astype('float') / UM_PER_PULSE

        # start位置に移動
        self.stage.move_abs(self.start)
        distance = np.linalg.norm(np.array(current - self.start))
        time.sleep(distance / 40000 + 1)  # TODO: 到着を確認してから次に進む

        # ProgressBarの設定
        self.progressbar_auto.config(maximum=self.max_step.get())
        self.number.set(1)

        self.create_and_start_thread_auto()

    def auto_acquire_and_save(self):
        """
        自動スキャンの本体
        スレッド内で実行される関数
        Returns:
        """
        self.entry_exposure_time.config(state=tk.DISABLED)
        self.entry_accumulation.config(state=tk.DISABLED)
        self.button_acquire.config(state=tk.DISABLED)
        self.button_save.config(state=tk.DISABLED)
        self.button_start_auto.config(state=tk.DISABLED)

        number = 1
        step = self.max_step.get()
        while number <= step:
            time_left = math.ceil((step - number + 1) * float(self.entry_exposure_time.get()) * 2  * float(self.entry_accumulation.get()) / 60)
            self.state.set(f'Acquisition {number} of {step}... {time_left} minutes left')

            point = self.start + (self.goal - self.start) * (number - 1) / (step - 1)
            self.stage.move_abs(point)
            self.locations.append(point * UM_PER_PULSE)
            distance = np.linalg.norm(np.array(point - self.start))
            time.sleep(distance / 40000 + 1)  # TODO: 到着を確認してから次に進む

            self.acquire()

            self.save_as_csv(os.path.join(self.cl.folder, f'{number}of{step}.csv'))

            number += 1
            self.number.set(number)
            self.locations_to_csv()

        self.state.set('Auto Acquisition Finished')
        self.entry_exposure_time.config(state=tk.ACTIVE)
        self.entry_accumulation.config(state=tk.ACTIVE)
        self.button_acquire.config(state=tk.ACTIVE)
        self.button_save.config(state=tk.ACTIVE)
        self.button_start_auto.config(state=tk.ACTIVE)

    def locations_to_csv(self):
        """
        自動スキャンの測定場所を記録する
        Returns:
        """
        if self.cl.mode == 'RELEASE':
            filename = os.path.join(self.cl.folder, 'location.csv')
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(self.locations)
        else:
            print('locations saved')

    def quit(self):
        """
        アプリを終了する
        sys.exitすることでthreadを強制終了できる
        そうしないと永遠に終了しなくなるので苦肉の策
        Returns:
        """
        if self.cl.mode == 'RELEASE':
            self.lib.tlccs_close(self.ccs_handle)
            self.ser.close()
        self.master.destroy()
        sys.exit()  # デーモン化してあるスレッドはここで死ぬ


def main():
    root = tk.Tk()
    root.option_add("*font", FONT)
    root.protocol('WM_DELETE_WINDOW', (lambda: 'pass')())  # QUITボタン以外の終了操作を許可しない
    app = MinimalWindow(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
