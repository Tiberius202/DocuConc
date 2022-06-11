import sys
import spacy
import os

from PyQt6.QtCore import Qt 
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QTextEdit, QFileDialog, QWidget
from PyQt6.QtGui import QAction

#Begin ds_spacy Imports remember to have spacy 3.3 and pandas 
from spacy.training import offsets_to_biluo_tags, iob_to_biluo
from spacy import displacy
from itertools import *
from collections import Counter

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
    #Button Open File. Uses PyQtMenu
    def buttOpenFile(self):
        fDialog = QFileDialog()
        fDialog.getOpenFileNames()

    def runSpacyModel(self):
        doc = self.nlp(self.inputText.toPlainText())
        self.outputTree.clear()
        for token in doc:
            QTreeWidgetItem(self.outputTree, [token.text, token.tag_, token.ent_type_, token.ent_iob_] )

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
        self.openAction.triggered.connect(self.buttOpenFile)
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

        visuals = QHBoxLayout()
        self.inputText = QTextEdit()
        self.inputText.setAcceptRichText(False)
        visuals.addWidget(self.inputText, 1)
        self.outputTree = QTreeWidget()
        self.outputTree.setColumnCount(4)
        self.outputTree.setHeaderLabels(["Text", "Tag", "Entry Type", "Entry IOB"])
        visuals.addWidget(self.outputTree, 1)
        workspace.addLayout(visuals)

        runButton = QPushButton()
        runButton.setText("Run analyzer")
        runButton.clicked.connect(self.runSpacyModel)
        workspace.addWidget(runButton)

        fileListW = QListWidget()
        fileListW.addItem(QListWidgetItem("testing"))

        mainView.addWidget(fileListW, 1)
        mainView.addLayout(workspace, 4)
        return mainView
    def _createContextMenu(self):
        #self.centralWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
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
        
        super().__init__(parent)
        self.setWindowTitle("BrownQt Work in Progress")
        self.resize(1280, 720)
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self._createMainView())
        self.setCentralWidget(self.centralWidget)
        self.nlp = spacy.load(os.getcwd() + "\model-new")
        self._createActions()
        self._createMenuBar()
        self._createContextMenu()
        self._connectActions()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
