import sys

from PyQt6.QtCore import Qt 
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QMenu, QMenuBar, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QTextEdit, QPushButton, QWidget
from PyQt6.QtGui import QAction

from tkinter import *
from tkinter import filedialog

class Window(QMainWindow):
    """Main Window."""
    # Variables
    global currentFileName
    currentFileName = False

    # Action Functionality Placeholder
    def openFile(self):
        currentFileName = filedialog.askopenfilename(initialdir = "/",
                                            title = "Select a File",
                                            filetypes = (("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        f = open(currentFileName, "r")
        print(f.read()) 
        f.close()
    def saveFile(self):
        currentFileName = filedialog.askopenfilename(initialdir = "/",
                                            title = "Select a File",
                                            filetypes = (("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        f = open(currentFileName, "w")
        f.write("""Put the shit that we have open later in this place so we can save it""")
        f.close()
    def copyContent(self):
        # Logic for copying content goes here...
        self.centralWidget.setText("<b>Edit > Copy</b> clicked")
    def pasteContent(self):
        # Logic for pasting content goes here...
        self.centralWidget.setText("<b>Edit > Paste</b> clicked")
    def cutContent(self):
        # Logic for cutting content goes here...
        self.centralWidget.setText("<b>Edit > Cut</b> clicked")
    def helpContent(self):
        # Logic for launching help goes here...
        self.centralWidget.setText("<b>Help > Help Content...</b> clicked")
    def about(self):
        # Logic for showing an about dialog content goes here...
        self.centralWidget.setText("<b>Help > About...</b> clicked")

    def _connectActions(self):
        # Connect File actions
        self.openAction.triggered.connect(self.openFile)
        self.saveAction.triggered.connect(self.saveFile)
        self.exitAction.triggered.connect(self.close)
        # Connect Edit actions
        self.copyAction.triggered.connect(self.copyContent)
        self.pasteAction.triggered.connect(self.pasteContent)
        self.cutAction.triggered.connect(self.cutContent)
        # Connect Help actions
        self.helpContentAction.triggered.connect(self.helpContent)
        self.aboutAction.triggered.connect(self.about)

    # Populating Buttons with Actions
    def _createActions(self):
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
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

        editMenu = menuBar.addMenu("&Edit")
        editMenu.addAction(self.copyAction)
        editMenu.addAction(self.pasteAction)
        editMenu.addAction(self.cutAction)
        editMenu.addSeparator()
        findMenu = editMenu.addMenu("Find and Replace")

        settingsMenu = menuBar.addMenu("&Settings")

        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(self.helpContentAction)
        helpMenu.addAction(self.aboutAction)
    def _createMainView(self):
        mainView = QHBoxLayout()

        workspace = QVBoxLayout()
        workspace.addWidget(QTextEdit())
        workspace.addWidget(QPushButton())

        fileListW = QListWidget()
        fileListW.addItem(QListWidgetItem("testing"))

        mainView.addWidget(fileListW)
        mainView.addLayout(workspace)
        return mainView
    def _createContextMenu(self):
        self.centralWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.centralWidget.addAction(self.openAction)
        self.centralWidget.addAction(self.saveAction)
        separator = QAction(self)
        separator.setSeparator(True)
        self.centralWidget.addAction(separator)
        self.centralWidget.addAction(self.copyAction)
        self.centralWidget.addAction(self.pasteAction)
        self.centralWidget.addAction(self.cutAction)

    # Creating Window
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("BrownQt Work in Progress")
        self.resize(400, 200)
        self.centralWidget = QWidget()
        self.centralWidget.setLayout = self._createMainView()
        self.setCentralWidget(self.centralWidget)
        self._createActions()
        self._createMenuBar()
        self._createContextMenu()
        self._connectActions()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
