import sys
import spacy
import os

from PyQt6.QtCore import Qt 
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QTextEdit, QFileDialog, QWidget
from PyQt6.QtGui import QAction

#Begin ds_spacy Imports remember to have spacy 3.3 and pandas 
from itertools import *

from tkinter import filedialog
#Processing helpers


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
        selectedFileNames = QFileDialog.getOpenFileNames(self, 
            "Select a File to Open", 
            os.getcwd(), "Text Files (*.txt);; All files (*)")
        if len(selectedFileNames) > 0:
            for fileName in selectedFileNames:
                fileName = str(fileName)
                #TODO: No duplicates
                self.openFileDict.update({fileName : open(fileName, "r")}) 
                listItem = QListWidgetItem()
                listItem.setToolTip(fileName)
                listItem.setText(fileName.replace("\\", "/").split("/")[-1])
                self.openFileW.addItem(listItem)
                self.openFileW.sortItems()
    def saveFile(self):
        selectedFileNames = filedialog.askopenfilename(initialdir = "/",
                                            title = "Select a File",
                                            filetypes = (("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        if len(selectedFileNames) > 0:                                                 
            f = open(selectedFileNames, "w")
            f.write("""TODO:Put the shit that we have open later in this place so we can save it""")
    def close(self):
        print("TODO: most likely replace with close all")
    def copyContent(self):
        # TODO: ALL of these are broken Logic for copying content goes here...
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
    def openListDoubleClick(self, item):
        #TODO: no duplicates
        self.currFileW.addItem(QListWidgetItem(item))
        self.currFileW.sortItems()
    def currListDoubleClick(self, item):
        if self.documentViewAction.isChecked():
            self.inputText.setText("TODO: Actual File" + item.toolTip())
    def toggleTextEditor(self):
        if self.documentViewAction.isChecked():
            self.inputText = QTextEdit()
            self.inputText.setAcceptRichText(False)
            self.inputText.setReadOnly(True)
            self.visuals.insertWidget(0, self.inputText, 1)
        else:
            self.visuals.removeWidget(self.inputText)
            self.inputText.deleteLater()
        
    def _createMenuBar(self):
        menuBar = self.menuBar()
        #File
        fileMenu = menuBar.addMenu("File")
        openAction = QAction("&Open Files", self)
        openAction.triggered.connect(self.openFile)
        fileMenu.addAction(openAction)

        saveAction = QAction("&Save", self)
        saveAction.triggered.connect(self.saveFile)
        fileMenu.addAction(saveAction)

        fileMenu.addSeparator()

        exitAction = QAction("Exit", self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)
        #Edit TODO Remove
        editMenu = menuBar.addMenu("Edit")
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
        findMenu = editMenu.addMenu("&Find and Replace")
        #View
        viewMenu = menuBar.addMenu("View")
        self.documentViewAction = QAction("&Document View", self)
        self.documentViewAction.setCheckable(True)
        self.documentViewAction.toggled.connect(self.toggleTextEditor)
        viewMenu.addAction(self.documentViewAction)
        #Settings
        settingsMenu = menuBar.addMenu("Settings")
        #Help TODO link webpages
        helpMenu = menuBar.addMenu("Help")
        helpContentAction = QAction("&Help Content", self)
        helpContentAction.triggered.connect(self.helpContent)
        helpMenu.addAction(helpContentAction)
        aboutAction = QAction("&About", self)
        aboutAction.triggered.connect(self.about)
        helpMenu.addAction(aboutAction)

    def _createMainView(self):
        mainView = QHBoxLayout()

        workspace = QVBoxLayout()

        self.visuals = QHBoxLayout()
        self.outputTree = QTreeWidget()
        self.outputTree.setColumnCount(4)
        self.outputTree.setHeaderLabels(["Text", "Tag", "Entry Type", "Entry IOB"])
        self.visuals.addWidget(self.outputTree, 1)
        workspace.addLayout(self.visuals)

        runButton = QPushButton()
        runButton.setText("Run analyzer")
        runButton.clicked.connect(self.runSpacyModel)
        workspace.addWidget(runButton)

        leftBar = QVBoxLayout()
        self.openFileW = QListWidget()
        self.openFileW.itemDoubleClicked.connect(self.openListDoubleClick)
        self.currFileW = QListWidget()
        self.currFileW.itemDoubleClicked.connect(self.currListDoubleClick)
        leftBar.addWidget(self.openFileW)
        leftBar.addWidget(self.currFileW)

        mainView.addLayout(leftBar, 1)
        mainView.addLayout(workspace, 4)
        return mainView

    # Creating Window
    def __init__(self, parent=None):
        #GUI setup
        super().__init__(parent)
        self.setWindowTitle("BrownQt Work in Progress")
        self.resize(1280, 720)
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self._createMainView())
        self.setCentralWidget(self.centralWidget)
        self._createMenuBar()
        #initialize model
        self.nlp = spacy.load(os.path.join(os.path.dirname(__file__) , "model-new"))
        #Functionality
        self.openFileDict = {}
        self.currFileDict = {}


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
