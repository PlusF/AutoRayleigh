import serial


def val2str(values: list):
    s = ''
    for value in values:
        if value < 0:
            s += '-' + str(-value) + ','
        else:
            s += '+' + str(value) + ','
    return s[:-1]


class StageController:
    def __init__(self, port, baud_rate):
        self.ser = serial.Serial(port, baud_rate)
        self.end = '\r\n'

    def send_recv(self, order):
        print(order)
        order += self.end
        self.ser.write(order.encode)
        msg = self.ser.readline()
        msg.strip(self.end)
        print(f'\t-> {msg}')
        return msg

    def get_pos(self):
        order = 'Q:'
        msg = self.send_recv(order)
        if msg == 'OK':
            return True
        else:
            return False

    def move_rel(self, values: list):
        if len(values) != 3:
            self.close()
            print("move value list must content three values")
            raise ValueError
        order = 'M:' + val2str(values)
        msg = self.send_recv(order)
        if msg == 'OK':
            return True
        else:
            return False

    def move_abs(self, values: list):
        if len(values) != 3:
            self.close()
            print('move value list must content three values')
            raise ValueError
        order = 'A:' + val2str(values)
        msg = self.send_recv(order)
        if msg == 'OK':
            return True
        else:
            return False

    def stop_emergency(self):
        order = 'L:E'
        msg = self.send_recv(order)
        if msg == 'OK':
            return True
        else:
            return False

    def set_speed(self, axis: int, slow: float, fast: float, rate: float):
        if axis not in [0, 1, 2, 3]:
            self.close()
            print('axis number must be 0 ~ 3')
            raise ValueError
        if slow < 1 or 500000 < slow or fast < 1 or 500000 < fast or rate < 0 or 1000 < rate:
            self.close()
            print('speed value out of range.\n1<=slow<=500000, 1<=fast<=500000, 0<=rate<=1000.')
            raise ValueError
        if axis == 0:
            order = 'D:WS' + str(abs(slow)) + 'F' + str(abs(fast)) + 'R' + str(abs(rate))
        else:
            order = 'D:' + str(axis) + 'S' + str(abs(slow)) + 'F' + str(abs(fast)) + 'R' + str(abs(rate))
        msg = self.send_recv(order)
        if msg == 'OK':
            return True
        else:
            return False

    def go_machine_org(self):
        order = 'H:1'
        msg = self.send_recv(order)
        if msg == 'OK':
            return True
        else:
            return False

    def go_logical_org(self):
        order = 'R:1'
        msg = self.send_recv(order)
        if msg == 'OK':
            return True
        else:
            return False

    def set_logical_org(self):
        pass

    def close(self):
        self.ser.close()
        print('closed')
        return True
