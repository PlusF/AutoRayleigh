import glob
import os.path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.signal import find_peaks
from sklearn.linear_model import LinearRegression


class DataProcessor:
    def __init__(self, path, center_wl=630):
        self.path = path
        self.df = None
        self.center_wl = center_wl
        self.wl_data = np.linspace(self.center_wl - 65, self.center_wl + 65, 1024)
        self.peaks_found_wl = None
        self.wl_data_calibrated = None

        if self.center_wl == 500:
            self.peaks = [435.833, 546.074]
        elif self.center_wl == 630:
            self.peaks = [576.96, 579.066, 696.543]
        elif self.center_wl == 760:
            self.peaks = [696.543]
        else:
            print('Choose from 500, 630, 760.')

        self.load_data()

    def load_data(self):
        filenames = glob.glob(self.path + '/*.asc')

        df_list = []
        for filename in filenames:
            df = pd.read_csv(filename, header=None).T
            df.index = [filename.split(os.path.sep)[-1]]
            df_list.append(df)
        self.df = pd.concat(df_list, axis=0)
        self.df = self.df.sort_index()

    def quick_calibration(self, show=False):
        data_calibration = self.df.filter(like='calibration', axis=0)
        if len(data_calibration) > 1:
            print('Many calibration files found. Choose one.')
            for i, name in enumerate(data_calibration.index):
                print(f'{i}: {name}')
            choice = int(input('which one? >'))
            data_calibration = data_calibration.iloc[choice]

        data_calibration = np.ravel(data_calibration.values)  # 2次元配列->1次元配列
        peaks_found, _ = find_peaks(data_calibration, distance=10, prominence=50)

        if show:
            plt.plot(range(0, 1024), data_calibration, color='k')
            plt.scatter(peaks_found, data_calibration[peaks_found], color='r')
            plt.show()

        if len(self.peaks) != len(peaks_found):
            print('Failed to find peaks')

        self.peaks_found_wl = self.wl_data[peaks_found]
        self.regression()

        print('Calibration succeed.')

    def regression(self):
        wl_data = np.array([self.wl_data, self.wl_data ** 2, self.wl_data ** 3])
        wl_data = wl_data.T

        peaks_found_wl = np.array(self.peaks_found_wl)
        peaks_found_wl = np.array([peaks_found_wl, peaks_found_wl ** 2, peaks_found_wl ** 3])
        peaks_found_wl = peaks_found_wl.T
        peaks = np.array(self.peaks)

        lr = LinearRegression()
        lr.fit(peaks_found_wl, peaks)
        self.wl_data_calibrated = lr.predict(wl_data)

    def draw(self):
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(projection='3d')
        if self.wl_data_calibrated is None:
            x = self.wl_data
        else:
            x = self.wl_data_calibrated

        for i, (filename, data) in enumerate(self.df.iterrows()):
            if 'calibration' in filename:
                continue

            y = [i] * 1024
            z = data.values
            ax.plot(x, y, z, color=cm.gist_earth(i / self.df.shape[0]))

        ax.set_zlim(0, 40000)
        plt.show()


def main():
    path = r"G:\共有ドライブ\Laboratory\Individuals\kaneda\Data_M1\220616\SCANT"
    dp = DataProcessor(path=path)
    dp.quick_calibration(show=True)
    dp.draw()


if __name__ == '__main__':
    main()
