from logging import exception
import sys
import spacy
import os
import re
import docuscospacy.corpus_analysis as scoA
import docuscospacy.corpus_utils as scoU

from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QAbstractItemView, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QTextEdit, QWidget, QFileDialog, QToolBar, QMenuBar
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtCore import Qt
from itertools import *
from tkinter import filedialog

from tmtoolkit.corpus import Corpus, vocabulary_size, doc_tokens, corpus_num_tokens, corpus_add_files
import corpusLibOverwrites

#Lambda to be used in Corpus.from_Files
def pre_process(txt):
        txt = re.sub(r'\bits\b', 'it s', txt)
        txt = re.sub(r'\bIts\b', 'It s', txt)
        txt = " ".join(txt.split())
        return(txt)

class Window(QMainWindow):
    def runSpacyModel(self):
        if self.documentViewAction.isChecked():
            doc = self.nlp(pre_process(self.inputText.toPlainText()))
            self._oTreeDoc()
            for token in doc:
                QTreeWidgetItem(self.outputTree, [token.text, token.tag_, token.ent_type_, token.ent_iob_] )
        else:
            if len(self.openFilesToBeAdded) > 0:
                if self.corp is None:
                    self.corp = Corpus.from_files(
                        self.openFilesToBeAdded,
                        spacy_instance=self.nlp, 
                        raw_preproc=pre_process, 
                        spacy_token_attrs=['tag', 'ent_iob', 'ent_type', 'is_punct'],
                        doc_label_fmt='{basename}', max_workers = 1)
                else:
                    corpus_add_files(
                        self.corp,
                        self.openFilesToBeAdded,
                        doc_label_fmt='{basename}')
                self.runProgress.setText("Post processing corpus")
                QApplication.processEvents()
                self.openFilesToBeAdded = []
                corpus_total = corpus_num_tokens(self.corp)
                corpus_types = vocabulary_size(self.corp)
                total_punct = 0
                for doc in self.corp:
                    total_punct += sum(self.corp[doc]['is_punct'])
                non_punct = corpus_total - total_punct
                #TODO: display these
                docs = doc_tokens(self.corp, with_attr=True)
                tp = scoU._convert_totuple(docs)
                #TODO: Compares strings. Consider enum
                outputFormat = self.outputFormat.checkedAction().text()
                self.runProgress.setText("Sorting tokens and building table")
                QApplication.processEvents()
                if   outputFormat == "Word List":
                    token_counts = scoU._count_tokens(tp, non_punct)
                    sortedTokens = sorted(token_counts, key= lambda x : x[1], reverse=True)
                    self._oWordList()
                elif outputFormat == "Part of Speech":
                    pos_counts = scoU._count_tags(tp, non_punct)
                    sortedTokens = sorted(pos_counts  , key= lambda x : x[1], reverse=True)
                    self._oPartOfSpeech()
                elif outputFormat == "Docuscope Tags":
                    ds_counts = scoU._count_ds(tp, non_punct)
                    sortedTokens = sorted(ds_counts   , key= lambda x : x[1], reverse=True)
                    self._oDocuscopeTags()
                else:
                    raise Exception("Unknown format. Should be impossible")
                #visuals
                self.runProgress.setText("Displaying output")
                QApplication.processEvents()
                for (word, count, prop, range) in sortedTokens :
                    QTreeWidgetItem(self.outputTree, [word, str(count), str(prop), str(range)])
                self.runProgress.setText("Done")

    # Action Functionality Placeholder
    def openFile(self):
        selectedFileNames = QFileDialog.getOpenFileNames(self, 'Open File', filter = "Text files (*.txt);; All Files (*)")
        #TODO add openFolders
        for fname in selectedFileNames[0]:
            if fname in self.openFileDict:
                self.openFileDict.update({fname : open(fname, "r")})
            else:
                self.openFileDict.update({fname : open(fname, "r")})
                listItem = QListWidgetItem()
                listItem.setToolTip(fname)
                listItem.setText(fname.replace("\\", "/").split("/")[-1])
                self.openFileW.addItem(listItem)
                #TODO: Make adding to current default but possibly add toggle
                #self.currFileDict.update({fname : None})
                #self.openFilesToBeAdded.append(fname)
                #self.currFileW.addItem(QListWidgetItem(listItem))
                #self.currFileW.sortItems()
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
    def add(self):
        fnames = self.openFileW.selectedItems()
        if not fnames: return
        for item in fnames:
            fname = item.toolTip()
            if  (fname) not in self.currFileDict:
                self.currFileDict.update({fname : None})
                self.openFilesToBeAdded.append(fname)
                #update visuals
                self.currFileW.addItem(fname)
                self.currFileW.sortItems()
    def remove(self):
        fnames = self.currFileW.selectedItems()
        if not fnames: return
        for item in fnames:
            # fname = item.toolTip()
            # del self.currFileDict[fname]
            #update visuals
            self.currFileW.takeItem(self.currFileW.row(item))
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
        fname = item.toolTip()
        if  (fname) not in self.currFileDict:
            self.currFileDict.update({fname : None})
            self.openFilesToBeAdded.append(fname)
            #update visuals
            self.currFileW.addItem(QListWidgetItem(item))
            self.currFileW.sortItems()
    def currListDoubleClick(self, item):
        if self.documentViewAction.isChecked():
            self.inputText.setText(self.openFileDict[item.toolTip()].read())
    def toggleTextEditor(self):
        if self.documentViewAction.isChecked():
            self._oTreeDoc()
            self.inputText = QTextEdit()
            self.inputText.setAcceptRichText(False)
            self.inputText.setReadOnly(True)
            self.visuals.insertWidget(0, self.inputText, 1)
        else:
            self._oWordList()
            self.visuals.removeWidget(self.inputText)
            self.inputText.deleteLater()

    def _oWordList(self):
        self.outputTree.setColumnCount(4)
        self.outputTree.setHeaderLabels(["Word", "Count", "Prop", "Range"])
        self.outputTree.clear()

    def _oPartOfSpeech(self):
        self.outputTree.setColumnCount(4)
        self.outputTree.setHeaderLabels(["POS Tag", "Count", "Prop", "Range"])
        self.outputTree.clear()

    def _oDocuscopeTags(self):
        self.outputTree.setColumnCount(4)
        self.outputTree.setHeaderLabels(["Docuscope Tag", "Count", "Prop", "Range"])
        self.outputTree.clear()
    
    def _oTreeDoc(self):
        self.outputTree.setColumnCount(4)
        self.outputTree.setHeaderLabels(["Text", "Tag", "Entry Type", "Entry IOB"])
        self.outputTree.clear()
        
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
        viewMenu.addSection("Output Format")
        self.outputFormat = QActionGroup(viewMenu)
        wordlistAction = QAction("Word List", self)
        partOfSpeech = QAction("Part of Speech", self)
        docuscope = QAction("Docuscope Tags", self)
        wordlistAction.setCheckable(True)
        partOfSpeech.setCheckable(True)
        docuscope.setCheckable(True)
        self.outputFormat.addAction(wordlistAction)
        self.outputFormat.addAction(partOfSpeech)
        self.outputFormat.addAction(docuscope)
        wordlistAction.setChecked(True)
        self.outputFormat.setExclusive(True)
        viewMenu.addAction(wordlistAction)
        viewMenu.addAction(partOfSpeech)
        viewMenu.addAction(docuscope)
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
        self.outputTree.setColumnWidth(0, 200)
        self._oWordList()
        self.visuals.addWidget(self.outputTree, 1)
        workspace.addLayout(self.visuals)

        runButton = QPushButton()
        runButton.setText("Run analyzer")
        runButton.clicked.connect(self.runSpacyModel)
        workspace.addWidget(runButton)

        self.runProgress = QLabel("Nothing Running")
        def newTextOutput(s : str):
            self.runProgress.setText(s)
            QApplication.processEvents()
        corpusLibOverwrites.textOutput = newTextOutput
        workspace.addWidget(self.runProgress, alignment=Qt.AlignmentFlag.AlignRight)

        #Used for managing files
        leftBar = QVBoxLayout()
        self.openFileW = QListWidget()
        self.openFileW.itemDoubleClicked.connect(self.openListDoubleClick)
        self.openFileW.setSelectionMode(self.openFileW.SelectionMode.ExtendedSelection)
        self.currFileW = QListWidget()
        self.currFileW.itemDoubleClicked.connect(self.currListDoubleClick)
        self.currFileW.setSelectionMode(self.currFileW.SelectionMode.ExtendedSelection)
        openButton = QPushButton()
        openButton.setText("Open")
        openButton.clicked.connect(self.openFile)
        closeButton = QPushButton()
        closeButton.setText("Close")
        closeButton.clicked.connect(self.close)
        openAndCloseBox = QHBoxLayout()
        openAndCloseBox.addWidget(openButton)
        openAndCloseBox.addWidget(closeButton)
        leftBar.addLayout(openAndCloseBox)
        leftBar.addWidget(self.openFileW)
        addButton = QPushButton()
        addButton.setText("Add")
        addButton.clicked.connect(self.add)
        removeButton = QPushButton()
        removeButton.setText("Remove")
        removeButton.clicked.connect(self.remove)
        addAndRemoveBox = QHBoxLayout()
        addAndRemoveBox.addWidget(addButton)
        addAndRemoveBox.addWidget(removeButton)
        leftBar.addLayout(addAndRemoveBox)
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
        centralWidget = QWidget()
        centralWidget.setLayout(self._createMainView())
        self.setCentralWidget(centralWidget)
        self._createMenuBar()
        #initialize model
        self.nlp = spacy.load(os.path.join(os.path.dirname(__file__) , "model-new"))
        #Functionality
        self.openFileDict = {}
        self.openFilesToBeAdded = []
        self.currFileDict = {}
        self.corp = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = Window()
    win.show()
    sys.exit(app.exec())
