import glob
import os.path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from calibration import Calibrator
from mayavi import mlab


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
    def __init__(self):
        self.df = None
        self.df_without_cosmic_ray = None
        self.num_data = 0
        self.wl_data = None
        self.peaks_found_wl = None
        self.wl_data_calibrated = None

        self.clb = None

    def load_data(self, path: str, center: float):
        self.wl_data = np.linspace(center - 65, center + 65, 1024)
        self.clb = Calibrator()
        self.clb.set_center(center)

        if isinstance(path, str):
            filenames = glob.glob(path + '/*.asc')
        else:
            print('Failed in loading data. Check the path.')
            return False

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
            filename_split = filename.split(os.path.sep)[-1]
            if 'calibration' in filename_split:
                self.clb.load_data_from_array(df.values)
            else:
                df.index = [filename_split]
                df_list.append(df)
                self.num_data += 1
            # if 'calibration' not in df.index[0]:
            #     self.num_data += 1
        self.df = pd.concat(df_list, axis=0)

    def calibrate(self, show=False):
        self.wl_data_calibrated = self.clb.calibrate(search_width=4)
        if show:
            self.clb.show_result()

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
        self.df_without_cosmic_ray = pd.concat(df_list, axis=0)

    def draw(self, cosmic_ray_removal=False, surface=True):
        df = self.df
        if cosmic_ray_removal:
            if self.df_without_cosmic_ray is None:
                self.remove_cosmic_ray(times=1)
            df = self.df_without_cosmic_ray

        if self.wl_data_calibrated is None:
            x = self.wl_data
        else:
            x = self.wl_data_calibrated

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


class WholeDataProcessor(DataProcessor):
    def __init__(self, path_list: list, center_list: list, show: bool = True, cosmic_ray_removal: int = 3):
        super().__init__()
        if len(path_list) != len(center_list):
            print('Path list and center list must have same length.')

        self.x = np.array([])
        df_list = []
        for path, center in zip(path_list, center_list):
            self.load_data(path, center)
            # self.calibrate(show=show)
            self.remove_cosmic_ray(times=cosmic_ray_removal)
            # self.x = np.hstack([self.x, self.wl_data_calibrated])
            self.x = np.hstack([self.x, self.wl_data])
            df_list.append(self.df_without_cosmic_ray)
        df = pd.concat(df_list, axis=1)
        self.y = np.arange(0, df.shape[0])
        self.z = df.values
        zmean = self.z.mean(keepdims=True)
        zstd = np.std(self.z, keepdims=True)
        self.z_scaled = (self.z - zmean) / zstd * 30

    def draw_3d(self):
        s = mlab.surf(self.x * 100, self.y, self.z_scaled)
        mlab.show()


def main():
    path_list = [
        r"G:\共有ドライブ\Laboratory\Individuals\kaneda\Data_M1\220619\data_500",
        r"G:\共有ドライブ\Laboratory\Individuals\kaneda\Data_M1\220616\data_630",
        r"G:\共有ドライブ\Laboratory\Individuals\kaneda\Data_M1\220617\data_760"
    ]
    path_list = [
        r"G:\共有ドライブ\Laboratory\Individuals\kaneda\Data_M1\221020\Rayleigh",
    ]
    path_list = [
        r"G:\共有ドライブ\Laboratory\Individuals\kaneda\Data_M1\221024\data",
    ]

    center_list = [500, 630, 760]
    center_list = [500]

    wdp = WholeDataProcessor(path_list=path_list, center_list=center_list, show=True, cosmic_ray_removal=3)
    wdp.draw_3d()


if __name__ == '__main__':
    main()
