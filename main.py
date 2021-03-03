import sys, os
from PyQt5.QtCore import Qt
from PyQt5 import QtGui, QtWidgets

from pyDataVis import MainWindow
from utils import getDataFromUrl


def run():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("pyDataVis")
    app.setOrganizationName("Pierre Alphonse")

    datapath = None
    # Find and possibly create the data folder
    home = os.path.expanduser("~")
    if os.access(home, os.W_OK):
        datapath = os.path.join(home, ".pyDataVis")
        if not os.path.exists(datapath):
            os.mkdir(datapath)

    pixmap = QtGui.QPixmap(500, 100)
    pixmap.fill()
    splash = QtWidgets.QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    font = splash.font()
    font.setPixelSize(18)
    font.setWeight(QtGui.QFont.Bold)
    splash.setFont(font)
    msg = "pyDataVis: starting ..."
    splash.showMessage(msg, Qt.AlignCenter)
    splash.show()
    app.processEvents()

    iconpath = os.path.join(datapath, "icons", "icon.ico")
    if not os.path.isfile(iconpath):
        # Try to load data files from GitHub
        msg = "pyDataVis: loading data from GitHub ..."
        splash.showMessage(msg, Qt.AlignCenter)
        app.processEvents()
        url = "https://github.com/pyDataVis/pyDataVis/archive/main.zip"
        errmsg = getDataFromUrl(url, datapath)
        if errmsg:
            splash.showMessage(errmsg, Qt.AlignCenter)
            
    main = MainWindow(datapath)
    main.show()
    splash.finish(main)
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()

