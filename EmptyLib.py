class EmptyLib:
    def __init__(self):
        print('empty lib created')

    def tlccs_init(self, *args, **kwargs):
        print('initialized', *args)

    def tlccs_setIntegrationTime(self, *args, **kwargs):
        print('setIntegrationTime', *args)

    def tlccs_startScan(self, *args, **kwargs):
        print('startScan', *args)

    def tlccs_getWavelengthData(self, *args, **kwargs):
        print('getWavelengthData', *args)

    def tlccs_getScanData(self, *args, **kwargs):
        print('getScanData', *args)

    def tlccs_close(self, *args, **kwargs):
        print('close', *args)

