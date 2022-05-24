import SKStage


def main():
    sc = SKStage.StageController('COM6', 38400)
    sc.move_rel([10, 0, 0])


if __name__ == '__main__':
    main()
