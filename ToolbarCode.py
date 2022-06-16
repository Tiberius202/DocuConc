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
    #TODO: AXE OR NOT. Button Open File. Uses PyQtMenu
    #def buttOpenFile(self):
    #   fDialog = QFileDialog()
    #   fDialog.getOpenFileNames() 

    def runSpacyModel(self):
        doc = self.nlp(self.inputText.toPlainText())
        self.outputTree.clear()
        for token in doc:
            QTreeWidgetItem(self.outputTree, [token.text, token.tag_, token.ent_type_, token.ent_iob_] )

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
    def close(self):
        print("TODO: most likely replace with close all")
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
    def _createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        openAction = QAction("&Open", self)
        openAction.triggered.connect(self.openFile)
        fileMenu.addAction(openAction)

        saveAction = QAction("&Save", self)
        saveAction.triggered.connect(self.saveFile)
        fileMenu.addAction(saveAction)

        fileMenu.addSeparator()

        exitAction = QAction("&Exit", self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        editMenu = menuBar.addMenu("&Edit")
        copyAction = QAction("&Copy", self)
        copyAction.triggered.connect(self.copyContent)
        editMenu.addAction(copyAction)

        pasteAction = QAction("&Paste", self)
        pasteAction.triggered.connect(self.pasteContent)
        editMenu.addAction(pasteAction)

        cutAction = QAction("&Cut", self)
        cutAction.triggered.connect(self.cutContent)
        editMenu.addAction(cutAction)
        editMenu.addSeparator()
        findMenu = editMenu.addMenu("Find and Replace")

        settingsMenu = menuBar.addMenu("&Settings")

        helpMenu = menuBar.addMenu("&Help")
        helpContentAction = QAction("&Help Content", self)
        helpContentAction.triggered.connect(self.helpContent)
        helpMenu.addAction(helpContentAction)
        aboutAction = QAction("&About", self)
        aboutAction.triggered.connect(self.about)
        helpMenu.addAction(aboutAction)

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

        leftBar = QVBoxLayout()
        openFileW = QListWidget()
        currFileW = QListWidget()
        openFileW.addItem(QListWidgetItem("testing"))
        leftBar.addWidget(openFileW)
        leftBar.addWidget(currFileW)

        mainView.addLayout(leftBar, 1)
        mainView.addLayout(workspace, 4)
        return mainView
#    def _createContextMenu(self):
#        #self.centralWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
#        self.centralWidget.addAction(self.openAction)
#        self.centralWidget.addAction(self.saveAction)
#        separator = QAction(self)
#        separator.setSeparator(True)
#        self.centralWidget.addAction(separator)
#        self.centralWidget.addAction(self.copyAction)
#        self.centralWidget.addAction(self.pasteAction)
#        self.centralWidget.addAction(self.cutAction)

    # Creating Window
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BrownQt Work in Progress")
        self.resize(1280, 720)
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self._createMainView())
        self.setCentralWidget(self.centralWidget)
        self.nlp = spacy.load(os.path.join(os.getcwd(), "model-new"))
        self._createMenuBar()
        #self._createContextMenu()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
