import SKStage


def main():
    sc = SKStage.StageController('COM6', 38400)
    sc.move_rel([10, 0, 0])
    sc.move_abs([100, 100, 100])
    sc.stop_emergency()


if __name__ == '__main__':
    main()
