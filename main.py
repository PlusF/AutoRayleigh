import tkinter as tk
from tkinter import ttk
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors, CameraCapabilities
from GUI import AndorWindow, SKWindow
import serial


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
        self.aw.grid(row=0, column=0, sticky='NESW')
        self.sw.grid(row=0, column=1, sticky='NESW')


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
