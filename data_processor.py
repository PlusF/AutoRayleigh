import glob
import os.path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.signal import find_peaks
from sklearn.linear_model import LinearRegression


def modified_z_score(intensity):
    median_int = np.median(intensity)
    mad_int = np.median([np.abs(intensity - median_int)])
    modified_z_scores = 0.6745 * (intensity - median_int) / mad_int
    return modified_z_scores


def fixed_z(y, m):
    threshold = 7  # 閾値
    spikes = abs(np.array(modified_z_score(np.diff(y)))) > threshold
    y_out = y.copy()
    for i in np.arange(len(spikes)):
        if spikes[i]:  # If we have a spike in position i
            w = np.arange(i - m, i + 1 + m)  # スパイク周りの2 m + 1個のデータを取り出す
            w = w[0 <= w]  # 範囲を超えないようトリミング
            w = w[w < 1023]
            w2 = w[spikes[w] == False]  # スパイクでない値を抽出し，
            if len(w2) > 0:
                y_out[i] = np.mean(y[w2])  # 平均を計算し補完

    return y_out


class DataProcessor:
    def __init__(self, path, center_wl: float = 630):
        self.path = path
        self.df = None
        self.df_removed_cosmic_ray = None
        self.num_data = 0
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

        def sort_key(fn):
            fn_sep = fn.split(os.path.sep)[-1]
            if 'calibration' in fn_sep:
                return -1
            fn_sep = fn_sep.strip('acquisition')
            fn_sep = fn_sep[:fn_sep.find('of')]
            return int(fn_sep) + 1
        filenames.sort(key=sort_key)

        df_list = []
        for filename in filenames:
            df = pd.read_csv(filename, header=None).T
            df.index = [filename.split(os.path.sep)[-1]]
            df_list.append(df)
            if 'calibration' not in df.index[0]:
                self.num_data += 1
        self.df = pd.concat(df_list, axis=0)

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

    def remove_cosmic_ray(self, times: int = 0):
        df_list = []
        for name, data in self.df.iterrows():
            if 'calibration' in name:
                continue
            z = data.values
            for i in range(times):
                z = fixed_z(z, 3)
            df_new = pd.DataFrame(data=z).T
            df_new.index = [name]
            df_list.append(df_new)
        self.df_removed_cosmic_ray = pd.concat(df_list, axis=0)

    def draw(self, cosmic_ray_removal=False, surface=True):
        df = self.df
        if cosmic_ray_removal:
            if self.df_removed_cosmic_ray is None:
                self.remove_cosmic_ray(times=1)
            df = self.df_removed_cosmic_ray

        if self.wl_data_calibrated is None:
            x = self.wl_data
        else:
            x = self.wl_data_calibrated

        # extract = range(0, 1024, 100)
        # x = x[extract]
        # df = df.loc[:, extract]

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(projection='3d')

        y_surface = np.arange(0, self.num_data)
        z_surface = []
        for i, (filename, data) in enumerate(df.iterrows()):
            if 'calibration' in filename:
                continue
            y = [i] * df.shape[1]
            z = data.values
            if surface:
                z_surface.append(z)
            else:
                ax.plot(x, y, z, color=cm.gist_earth(i / self.num_data))

        if surface:
            x_mesh, y_mesh = np.meshgrid(x, y_surface)
            z_surface = np.array(z_surface)
            ax.plot_surface(x_mesh, y_mesh, z_surface, cmap='gist_earth', rcount=1, ccount=1000)
            ax.set_zlim(0, ax.get_zlim()[1])

        plt.show()


def main():
    path = r"G:\共有ドライブ\Laboratory\Individuals\kaneda\Data_M1\220616\SCANT"
    dp = DataProcessor(path=path)
    dp.quick_calibration(show=False)
    dp.remove_cosmic_ray(times=3)
    dp.draw(cosmic_ray_removal=True, surface=True)


if __name__ == '__main__':
    main()
