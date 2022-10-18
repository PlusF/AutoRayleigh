import tkinter as tk
from tkinter import ttk
import SKStage


UM_PER_PULSE = 0.01
WIDTH = 10


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
        self.update()

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
        self.x_go = tk.DoubleVar(value=0)
        self.y_go = tk.DoubleVar(value=0)
        self.z_go = tk.DoubleVar(value=0)

        self.label_x = ttk.Label(master=self, text='x [\u03bcm]')
        self.label_y = ttk.Label(master=self, text='y [\u03bcm]')
        self.label_z = ttk.Label(master=self, text='z [\u03bcm]')
        self.label_st = ttk.Label(master=self, text='start')
        self.label_cr = ttk.Label(master=self, text='current')
        self.label_gl = ttk.Label(master=self, text='goal')
        self.label_x_st = ttk.Label(master=self, textvariable=self.x_st)
        self.label_y_st = ttk.Label(master=self, textvariable=self.y_st)
        self.label_z_st = ttk.Label(master=self, textvariable=self.z_st)
        self.label_x = ttk.Label(master=self, textvariable=self.x_cr)
        self.label_y = ttk.Label(master=self, textvariable=self.y_cr)
        self.label_z = ttk.Label(master=self, textvariable=self.z_cr)
        self.label_x_gl = ttk.Label(master=self, textvariable=self.x_gl)
        self.label_y_gl = ttk.Label(master=self, textvariable=self.y_gl)
        self.label_z_gl = ttk.Label(master=self, textvariable=self.z_gl)
        self.entry_x = ttk.Entry(master=self, textvariable=self.x_go, width=WIDTH, justify=tk.CENTER)
        self.entry_y = ttk.Entry(master=self, textvariable=self.y_go, width=WIDTH, justify=tk.CENTER)
        self.entry_z = ttk.Entry(master=self, textvariable=self.z_go, width=WIDTH, justify=tk.CENTER)
        self.entry_x.config(font='游ゴシック 20')
        self.entry_y.config(font='游ゴシック 20')
        self.entry_z.config(font='游ゴシック 20')
        self.button_set_start = ttk.Button(master=self, text='Set Start', command=self.set_start, width=WIDTH, style='default.TButton')
        self.button_stop = ttk.Button(master=self, text='STOP', command=self.stop, width=WIDTH, style='red.TButton')
        self.button_set_goal = ttk.Button(master=self, text='Set Goal', command=self.set_goal, width=WIDTH, style='default.TButton')
        self.button_go = ttk.Button(master=self, text='GO', command=self.go, width=WIDTH, style='default.TButton')

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

    def update(self):
        coord = self.sc.get_pos()
        self.x_cr.set(round(coord[0] * UM_PER_PULSE, 2))
        self.y_cr.set(round(coord[1] * UM_PER_PULSE, 2))
        self.z_cr.set(round(coord[2] * UM_PER_PULSE, 2))
        self.master.after(100, self.update)

    def set_start(self):
        self.x_st.set(self.x_cr.get())
        self.y_st.set(self.y_cr.get())
        self.z_st.set(self.z_cr.get())

    def get_start(self):
        x = self.x_st.get()
        y = self.y_st.get()
        z = self.z_st.get()
        return [x, y, z]

    def set_goal(self):
        self.x_gl.set(self.x_cr.get())
        self.y_gl.set(self.y_cr.get())
        self.z_gl.set(self.z_cr.get())

    def get_goal(self):
        x = self.x_gl.get()
        y = self.y_gl.get()
        z = self.z_gl.get()
        return [x, y, z]

    def stop(self):
        self.sc.stop_emergency()

    def go(self):
        x = (float(self.entry_x.get()) - float(self.x_cr.get())) / UM_PER_PULSE
        y = (float(self.entry_y.get()) - float(self.y_cr.get())) / UM_PER_PULSE
        z = (float(self.entry_z.get()) - float(self.z_cr.get())) / UM_PER_PULSE
        self.sc.move_linear([x, y, z])
