class EmptyLib:
    def __init__(self):
        print('empty lib created')

    def tlccs_init(self, *args, **kwargs):
        print('initialized')

    def tlccs_setIntegrationTime(self, *args, **kwargs):
        print('setIntegrationTime')

    def tlccs_startScan(self, *args, **kwargs):
        print('startScan')

    def tlccs_getWavelengthData(self, *args, **kwargs):
        print('getWavelengthData')

    def tlccs_getScanData(self, *args, **kwargs):
        print('getScanData')

    def tlccs_close(self, *args, **kwargs):
        print('close')

