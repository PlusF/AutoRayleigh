import tkinter as tk
from tkinter import ttk
import os, time, serial, threading
import numpy as np
from pyAndorSDK2 import atmcd
from AndorWindow import AndorWindow
from SKWindow import SKWindow
from ConfigLoader import ConfigLoader


UM_PER_PULSE = 0.01
WIDTH = 10


class MainWindow(tk.Frame):
    def __init__(self, master=None, sdk=None, ser=None):
        super().__init__()

        s = ttk.Style()
        s.theme_use('winnative')
        s.configure('TLabel', font=('游ゴシック', 20))
        s.configure('TEntry', font=('游ゴシック', 20))
        s.configure('default.TButton', font=('游ゴシック', 20))
        s.configure('red.TButton', font=('游ゴシック', 20), background='#ff0000', foreground='#ff0000')

        self.master = master
        self.aw = AndorWindow(self.master, sdk)
        self.sw = SKWindow(self.master, ser)
        self.frame_auto = ttk.LabelFrame(master=self.master, text='Auto')
        self.aw.grid(row=0, column=0, sticky='NESW')
        self.sw.grid(row=0, column=1, sticky='NESW')
        self.frame_auto.grid(row=1, column=0, columnspan=2, sticky='NESW')

        self.label_step = ttk.Label(master=self.frame_auto, text='回数：')
        self.entry_step = ttk.Entry(master=self.frame_auto, width=WIDTH, justify=tk.CENTER)
        self.entry_step.insert(0, '10')
        self.entry_step.config(font=('游ゴシック', 20))
        self.button_start = ttk.Button(master=self.frame_auto, text='START', command=self.start_auto, width=WIDTH, style='default.TButton')
        self.number = tk.IntVar(value=0)
        self.progressbar = ttk.Progressbar(master=self.frame_auto, orient=tk.HORIZONTAL, variable=self.number, maximum=10, length=200, mode='determinate')
        self.state = tk.StringVar(value='キャリブレーション用ファイル保存しましたか？')
        self.label_state = ttk.Label(master=self.frame_auto, textvariable=self.state)

        self.label_step.grid(row=0, column=0)
        self.entry_step.grid(row=0, column=1)
        self.button_start.grid(row=0, column=2)
        self.progressbar.grid(row=0, column=3)
        self.label_state.grid(row=0, column=4)

        self.button_quit = ttk.Button(master=self.master, text='QUIT', command=self.quit, width=WIDTH*10, style='default.TButton')
        self.button_quit.grid(row=2, columnspan=2)

        self.thread = threading.Thread(target=self.auto)
        self.thread_working = False

    def start_auto(self):
        if self.thread_working:
            self.state.set('Still working')
            return
        self.aw.prepare_acquisition()
        self.sw.sc.set_speed_max()

        # 座標計算
        self.start = self.sw.get_start()
        self.start = np.array(list(map(lambda x: float(x) / UM_PER_PULSE, self.start)))
        self.goal = self.sw.get_goal()
        self.goal = np.array(list(map(lambda x: float(x) / UM_PER_PULSE, self.goal)))

        # ProgressBarの設定
        step = int(self.entry_step.get())
        self.progressbar.config(maximum=step + 1)
        self.number.set(0)

        # start位置に移動
        self.sw.sc.move_abs(self.start)
        distance = np.linalg.norm(np.array(self.sw.sc.get_pos()) - np.array(self.sw.get_start()))
        interval = distance / 1000  # set_speed_max()で20000um/s以上になっているはず・・・だがうまくいっていない
        time.sleep(max([1, interval]))  # 距離が近くても念のため1秒は待つ
        self.interval = np.linalg.norm(np.array(self.sw.get_goal()) - np.array(self.sw.get_start())) / 1000

        self.thread.start()
        self.thread_working = True

    def auto(self):
        step = int(self.entry_step.get())
        number = self.number.get()
        self.state.set(f'Acquisition {number} of {step}')
        point = self.start + (self.goal - self.start) * number / step
        self.sw.sc.move_abs(point)
        time.sleep(max([1, self.interval]))  # 距離が近くても念のため1秒は待つ

        self.aw.acquire()
        self.aw.save_as_asc(os.getcwd() + f'/data/acquisition{number}of{step}.asc')

        if number <= step:
            self.number.set(number + 1)
            self.master.after(100, self.auto)
        else:
            self.state.set('Acquisition Finished')
            self.thread_working = False

    def quit(self):
        # mainloop内でthreadを作っているので、mainloop内でjoinさせないとバグる
        if self.thread_working:
            print('Thread is still working. Please wait.')
            self.thread.join()
        else:
            self.master.destroy()


def main():
    cl = ConfigLoader('./config.json')
    if cl.mode == 'RELEASE':
        sdk = atmcd()
        ser = serial.Serial('COM6', 38400)
    elif cl.mode == 'DEBUG':
        sdk = ser = None
    else:
        raise ValueError('Error with config.json. mode must be DEBUG or RELEASE.')

    root = tk.Tk()
    root.protocol('WM_DELETE_WINDOW', (lambda: 'pass')())  # QUITボタン以外の終了操作を許可しない
    app = MainWindow(master=root, sdk=sdk, ser=ser)
    app.mainloop()

    if cl.mode == 'RELEASE':
        sdk.ShutDown()
        ser.close()


if __name__ == '__main__':
    main()
