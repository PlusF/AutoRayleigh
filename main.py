import tkinter as tk
from tkinter import ttk
import numpy as np
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors, CameraCapabilities
from AndorWindow import AndorWindow
from SKWindow import SKWindow
import serial


UM_PER_PULSE = 0.01
WIDTH = 10


def quit_me(root_window):
    root_window.quit()
    root_window.destroy()


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
        self.button_start = ttk.Button(master=self.frame_auto, text='START', command=self.auto_rayleigh, width=WIDTH, style='default.TButton')

        self.label_step.grid(row=0, column=0)
        self.entry_step.grid(row=0, column=1)
        self.button_start.grid(row=0, column=2)

    def auto_rayleigh(self):
        self.aw.entry_filename.delete(0, tk.END)
        self.aw.entry_filename.insert(0, 'background')
        self.aw.acquire()
        self.aw.save_as_sif()
        step = int(self.entry_step.get())
        start = [self.sw.x_st.get(), self.sw.y_st.get(), self.sw.z_st.get()]
        start = np.array(list(map(lambda x: float(x) / UM_PER_PULSE, start)))
        goal = [self.sw.x_gl.get(), self.sw.y_gl.get(), self.sw.z_gl.get()]
        goal = np.array(list(map(lambda x: float(x) / UM_PER_PULSE, goal)))
        for i in range(1, step + 1):
            print(f'{i} of {step}')
            self.sw.entry_x.delete(0, tk.END)
            self.sw.entry_y.delete(0, tk.END)
            self.sw.entry_z.delete(0, tk.END)
            point = start + (goal - start) * i / step
            self.sw.entry_x.insert(0, point[0])
            self.sw.entry_y.insert(0, point[1])
            self.sw.entry_z.insert(0, point[2])
            self.sw.go()

            self.aw.entry_filename.delete(0, tk.END)
            self.aw.entry_filename.insert(0, f'acquisition_{i}')
            self.aw.acquire()
            self.aw.save_as_sif()


def main():
    # sdk = atmcd()  ####
    # ser = serial.Serial('COM6', 38400)

    root = tk.Tk()
    root.protocol('WM_DELETE_WINDOW', lambda: quit_me(root))
    # app = MainWindow(master=root, sdk=sdk, ser=ser)  ####
    app = MainWindow(master=root)
    app.mainloop()

    # sdk.ShutDown()  ####
    # ser.close()


if __name__ == '__main__':
    main()
