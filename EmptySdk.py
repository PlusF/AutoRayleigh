import os
if os.name == 'nt':
    from pyAndorSDK2 import atmcd_codes, atmcd_errors
import numpy as npf


class EmptySdk:
    def __init__(self):
        self.theta = 0

    def handle_return(self, *args):
        print('handle_return:', args)
        return 0

    def Initialize(self, arg):
        print('Initialize', arg)
        return atmcd_errors.Error_Codes.DRV_SUCCESS

    def SetTemperature(self, temperature):
        print('Set temperature', temperature)

    def CoolerON(self):
        print('Cooler on')

    def GetTemperature(self):
        return atmcd_errors.Error_Codes.DRV_TEMP_STABILIZED, 0

    def SetAcquisitionMode(self, arg):
        print('SetAcquisitionMode')

    def SetReadMode(self, arg):
        print('SetReadMode')

    def SetTriggerMode(self, arg):
        print('SetTriggerMode')

    def GetDetector(self):
        print('GetDetector')
        return None, None, None

    def SetExposureTime(self, exposure_time):
        print('SetExposureTime', exposure_time)

    def PrepareAcquisition(self):
        print('PrepareAcquisition')

    def StartAcquisition(self):
        print('StartAcquisition')

    def WaitForAcquisition(self):
        print('WaitForAcquisition')

    def GetImages16(self, *args):
        self.theta += 0.1
        val_range = np.linspace(0, 4, 100)
        print('GetImages16')
        return None, np.sin(val_range + self.theta), None, None

    def SaveAsSif(self, path):
        print('SaveAsSif', path)
