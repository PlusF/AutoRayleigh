from glob import glob
import os.path
import numpy as np
import pandas as pd
from mayavi import mlab


def main():
    folder = r"G:\共有ドライブ\Laboratory\Individuals\kaneda\Data_M1\221027\data"
    folder = r"G:\共有ドライブ\Laboratory\Individuals\kaneda\Data_M1\221102\Rayleigh\data"
    filenames = glob(os.path.join(folder, '*.csv'))

    df_list = []
    for filename in filenames:
        name = filename.split(os.sep)[-1].strip('.csv')
        if name == 'location':
            continue
        if name == 'ArHg':
            continue
        df_tmp = pd.read_csv(filename, header=None, index_col=0)
        df_list.append(df_tmp)
    df = pd.concat(df_list, axis=1)

    x = df.index.values
    y = np.arange(0, len(df.columns)).astype(float)
    z = df.values
    y *= (x.max() - x.min()) / y.max()
    z *= (x.max() - x.min()) / z.max()
    s = mlab.surf(x, y, z)
    mlab.show()


if __name__ == '__main__':
    main()
