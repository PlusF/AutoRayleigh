import SKStage
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors, CameraCapabilities
import matplotlib.pyplot as plt


def main():
    sc = SKStage.StageController('COM6', 9600)
    sdk = atmcd()
    codes = atmcd_codes


if __name__ == '__main__':
    main()
