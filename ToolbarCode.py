import sys

from PyQt6.QtCore import Qt 
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QMenu, QMenuBar, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QTextEdit, QPushButton, QWidget
from PyQt6.QtGui import QAction



class Window(QMainWindow):
    def runSpacyModel(self):
        print("TODO")

    def _createActions(self):
        self.newAction = QAction("&New", self)
        self.openAction = QAction("&Open", self)
        self.saveAction = QAction("&Save", self)
        self.exitAction = QAction("&Exit", self)
        self.copyAction = QAction("&Copy", self)
        self.pasteAction = QAction("&Paste", self)
        self.cutAction = QAction("&Cut", self)
        self.helpContentAction = QAction("&Help Content", self)
        self.aboutAction = QAction("&About", self)
    def _createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.exitAction)

        editMenu = menuBar.addMenu("&Edit")
        editMenu.addAction(self.copyAction)
        editMenu.addAction(self.pasteAction)
        editMenu.addAction(self.cutAction)

        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(self.helpContentAction)
        helpMenu.addAction(self.aboutAction)
    def _createMainView(self):
        mainView = QHBoxLayout()

        workspace = QVBoxLayout()

        workspace.addWidget(QTextEdit())

        runButton = QPushButton()
        runButton.setText("")
        runButton.clicked.connect(self.runSpacyModel)
        workspace.addWidget(runButton)

        fileListW = QListWidget()
        fileListW.addItem(QListWidgetItem("testing"))

        mainView.addWidget(fileListW)
        mainView.addLayout(workspace)
        return mainView

    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("BrownQt Work in Progress")
        self.resize(800, 400)
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self._createMainView())
        self.setCentralWidget(self.centralWidget)
        self._createActions()
        self._createMenuBar()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
