import sys
from PyQt5 import QtWidgets
from pyDataVis import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("pyDataVis")
    app.setOrganizationName("Pierre Alphonse")
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
