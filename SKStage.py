import serial


class StageController:
    def __init__(self, port, baud_rate):
        # self.ser = serial.Serial(port, baud_rate)
        self.end = '\r\n'

    def move_rel(self, values: list):
        order = 'M:'
        for i, v in enumerate(values):
            if v < 0:
                order += '-' + str(-v) + ','
            else:
                order += '+' + str(v) + ','
        order = order[:-1] + self.end
        # self.ser.write(order.encode())
        print(order)

    def close(self):
        pass
        # self.ser.close()
