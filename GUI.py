import tkinter as tk
from tkinter import ttk


class AndorWindow(tk.Frame):
    def __init__(self, master=None, sdk=None, codes=None, errors=None):
        super().__init__(master)
        self.master = master
        self.sdk = sdk
        self.codes = codes
        self.errors = errors

    def create_widgets(self):
        pass


class SKWindow(tk.Frame):
    def __init__(self, master=None, ser=None):
        super().__init__(master)
        self.master = master
        self.ser = ser

    def create_widgets(self):
        pass
