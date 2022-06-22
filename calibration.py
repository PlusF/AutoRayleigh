import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score

PEAKS = [435.8335, 546.0750, 576.9610, 579.0670, 696.5431, 706.7218, 714.7042, 727.2936, 738.3980, 750.3869, 751.4652,
         763.5106, 772.3761, 794.8176, 800.6157, 801.4786, 810.3693, 811.5311]


class Calibrator:
    def __init__(self):
        self.center = 630
        self.peaks_target = []
        self.df = None
        self.pf = None
        self.x = None
        self.y = None
        self.indices_detected = None

    def load_data_from_path(self, path: str):
        if path.split('.')[-1] != 'asc':
            print('This program supports asc file.')
        filename = path
        self.df = pd.read_csv(filename, delimiter='\t', header=None)

    def load_data_from_array(self, arr: np.ndarray):
        arr = np.ravel(arr)
        if len(arr) != 1024:
            print('Wrong shape. Check the input array.')
            print(arr)
        self.df = pd.DataFrame(data=arr)

    def set_center(self, center: float):
        if center not in [500, 630, 760]:
            print('This program supports 500, 630 or 760 nm as center wavelength.')
            return False
        self.center = center
        degree = 3  # 何次方程式でフィッティングするか
        if self.center == 500:
            self.peaks_target = PEAKS[:2]
            degree = 1
        elif self.center == 630:
            self.peaks_target = PEAKS[2:5]
        elif self.center == 760:
            self.peaks_target = PEAKS[4:]

        self.pf = PolynomialFeatures(degree=degree)

    def calibrate(self, search_width=4):
        self.x = np.linspace(self.center - 65, self.center + 65, self.df.shape[0])
        self.y = np.ravel(self.df.values)
        indices_found, _ = find_peaks(self.y, prominence=40, distance=5)

        self.indices_detected = []
        x_found = self.x[indices_found]
        for i, peak_target in enumerate(self.peaks_target):
            if self.center == 760 and i in [5, 6, 10, 11, 12, 13, 14]:
                if i == 14:  # リスト末尾の0
                    continue
                else:  # 750付近、800付近、810付近では注意が必要
                    index_detected = self.process_760(i, indices_found, search_width=search_width)
            else:
                diff_array = np.abs(x_found - peak_target) - self.y[indices_found] * 0.001  # ピークの大きさで重みづけ．近くにあって，大きいピークを選ぶように
                index_detected = indices_found[diff_array == np.min(diff_array)]
            self.indices_detected += list(index_detected)

        self.indices_detected = sorted(list(set(self.indices_detected)))  # 重複削除

        if len(self.indices_detected) != len(self.peaks_target):
            print('Some peaks not detected. Check graph')
            return False

        print('\nキャリブレーションに使用するピーク: ')
        print('校正前\t->\t校正後')
        for i, index in enumerate(self.indices_detected):
            print(f'{round(self.x[index], 2)}\t->\t{round(self.peaks_target[i], 2)}')
        print()

        x_detected_t = self.x[self.indices_detected].reshape(self.x[self.indices_detected].size, 1)  # 特徴量ベクトルを転置
        x_detected_cubic = self.pf.fit_transform(x_detected_t)

        model = LinearRegression()  # 線形回帰
        model.fit(x_detected_cubic, self.peaks_target)

        print('-' * 50)
        print(f'回帰モデルの係数: {model.coef_}')
        peaks_pred = model.predict(x_detected_cubic)
        print(f'回帰モデルのスコア: {r2_score(self.peaks_target, peaks_pred)}')
        print('-' * 50)

        x_t = self.x.reshape(self.x.size, 1)
        x_cubic = self.pf.fit_transform(x_t)
        x_calibrated = model.predict(x_cubic)

        return x_calibrated

    def process_760(self, i: int, indices_found: np.ndarray, search_width :int = 4):
        peak_target = self.peaks_target[i]

        indices_around_target = np.array([])
        for index_found in indices_found:
            peak_found = self.x[index_found]
            diff = abs(peak_target - peak_found)
            if diff < search_width:
                indices_around_target = np.append(indices_around_target, index_found)

        indices_detected = []
        indices_around_target = list(indices_around_target.astype(int))

        if i in [5, 6]:  # 750付近
            if len(indices_around_target) in [1, 2]:
                indices_detected = indices_around_target  # 重複は許す
            elif len(indices_around_target) == 3:
                y_values = self.y[indices_around_target]  # ピークとして検出されたyの値
                y_values_sorted = y_values.sort()  # 昇順にソート
                index_750 = indices_around_target[y_values == y_values_sorted[2]][0]  # 一番大きいピークは750.3869
                index_751 = indices_around_target[y_values == y_values_sorted[1]][0]  # 二番目は751.465
                indices_detected = [index_750, index_751]  # 重複は許す
            else:
                print(f'Peak detection error at around {peak_target} nm')

        elif i in [10, 11]:  # 800付近
            if len(indices_around_target) == 2:  # 1番目、2番目のピークを800, 801に
                indices_detected = indices_around_target
            else:
                print(f'Peak detection error at around {peak_target} nm')

        elif i in [12, 13]:  # 810付近
            if len(indices_around_target) == 3:
                indices_detected = indices_around_target[1:]  # 2番目、3番目のピークを810, 811に
            else:
                print(f'Peak detection error at around {peak_target} nm')

        if len(indices_detected) == 0:
            print(f'No peaks detected for {peak_target} nm')

        return indices_detected

    def show_result(self):
        fig, ax = plt.subplots()
        ax.plot(self.x, self.y, color='k')
        ax.scatter(self.x[self.indices_detected], self.y[self.indices_detected], marker='x', color='r')
        for i, peak_target in enumerate(self.peaks_target):
            ax.text(self.x[self.indices_detected[i]], self.y[self.indices_detected[i]], peak_target)
        ax.set_title('Peaks detected as')
        plt.show()


def main():
    clb = Calibrator()
    clb.load_data_from_path(r"/Volumes/GoogleDrive/共有ドライブ/Laboratory/Individuals/kaneda/Data_M1/220616/data_630/calibration_630.asc")
    clb.set_center(630)
    clb.calibrate()
    clb.show_result()
    clb.load_data_from_path(r"/Volumes/GoogleDrive/共有ドライブ/Laboratory/Individuals/kaneda/Data_M1/220617/data_760/calibration_760.asc")
    clb.set_center(760)
    clb.calibrate()
    clb.show_result()


if __name__ == '__main__':
    main()
