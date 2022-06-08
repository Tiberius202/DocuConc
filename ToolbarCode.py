import sys
#Begin PyQt Imports
from PyQt6.QtCore import Qt 
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QTextEdit, QPushButton, QWidget
from PyQt6.QtGui import QAction

#Begin ds_spacy Imports remember to have spacy 3.3 and pandas 
import spacy
from spacy.training import offsets_to_biluo_tags, iob_to_biluo
from spacy import displacy
from itertools import *
from collections import Counter

class Window(QMainWindow):
    def runSpacyModel(self):
        doc = self.nlp(self.inputText.toPlainText())
        outStr = ""
        for token in doc:
            outStr += "[" + token.text + "], " +"[" + token.tag_ + "], " +"["+ token.ent_type_ + "], "+"["+token.ent_iob_+"]\n"
        self.outputText.setText(outStr) 

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

        visuals = QHBoxLayout()
        self.inputText = QTextEdit()
        self.inputText.setAcceptRichText(False)
        visuals.addWidget(self.inputText, 1)
        self.outputText = QLabel("Analyzed code goes here")
        self.outputText.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        visuals.addWidget(self.outputText, 1)
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

    def __init__(self, parent=None):
        self.nlp = spacy.load('model-new')
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
