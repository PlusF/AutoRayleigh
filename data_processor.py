import glob
import os.path
import numpy as np
import pandas as pd
from mayavi import mlab


class DataProcessor:
    def __init__(self):
        self.df = None
        self.df_without_cosmic_ray = None
        self.wl_data = None

    def load_data(self, path: str):
        if isinstance(path, str):
            filenames = glob.glob(path + '/*.csv')
        else:
            print('Failed in loading data. Check the path.')
            return False

        def sort_key(fn):
            fn_split = fn.split(os.path.sep)[-1]
            if 'location' in fn_split or 'ArHg' in fn_split:
                return -1
            fn_split = fn_split.strip('acquisition')
            fn_split = fn_split[:fn_split.find('of')]
            return int(fn_split) + 1
        filenames.sort(key=sort_key)

        df_list = []
        for filename in filenames:
            df = pd.read_csv(filename, index_col=0, header=None)
            filename_split = filename.split(os.path.sep)[-1]
            if 'location' in filename_split or 'ArHg' in filename_split:
                continue
            else:
                df_list.append(df)

        self.df = pd.concat(df_list, axis=1)
        self.df = self.df.T
        self.df.index = np.arange(self.df.shape[0])

    def smoothing(self):
        self.df_smoothed = self.df.copy()
        window = 100  # 移動平均の範囲
        w = np.ones(window) / window

        for ind, row in self.df.iterrows():
             self.df_smoothed.loc[ind] = np.convolve(row.values, w, mode='same')

    def draw(self):
        x = self.df.index * 50
        y = self.df.columns
        z = self.df_smoothed.values * 500
        mlab.surf(x, y, z)
        mlab.show()


def main():
    path = r'/Volumes/GoogleDrive/共有ドライブ/Laboratory/Individuals/kaneda/Data_M1/221109/221109-RAS/1'
    dp = DataProcessor()
    dp.load_data(path)
    dp.smoothing()
    dp.draw()


if __name__ == '__main__':
    main()
