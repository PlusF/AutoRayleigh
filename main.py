import tkinter as tk
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors, CameraCapabilities
import matplotlib.pyplot as plt
import SKStage
from GUI import AndorWindow, SKWindow


class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__()
        self.master = master
        self.aw = AndorWindow(self.master)
        self.sw = SKWindow(self.master)
        self.aw.grid(row=0, column=0)
        self.sw.grid(row=0, column=1)


def main():
    root = tk.Tk()
    app = MainWindow(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
