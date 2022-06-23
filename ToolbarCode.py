import sys
import spacy
import os
import re

from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QPushButton, QAbstractItemView, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QTextEdit, QWidget, QFileDialog
from PyQt6.QtGui import QAction
from itertools import *
import numpy as np
from collections import Counter
from tkinter import filedialog
from tmtoolkit.corpus import Corpus, print_summary, tokens_table, vocabulary_counts, vocabulary_size, doc_tokens, corpus_num_tokens, corpus_add_files
import string

def pre_process(txt):
        txt = re.sub(r'\bits\b', 'it s', txt)
        txt = re.sub(r'\bIts\b', 'It s', txt)
        txt = " ".join(txt.split())
        return(txt) 
def itemgetter(x):
    return lambda t : t[x]
def convert_totuple(tok):
    token_tuple = []
    for i in range(0,len(tok)):
        token_list = [x.lower() for x in list(tok.values())[i]['token']]
        iob_list = list(tok.values())[i]['ent_iob']
        iob_list = [x.replace('IS_DIGIT','B') for x in iob_list]
        iob_list = [x.replace('IS_ALPHA','I') for x in iob_list]
        iob_list = [x.replace('IS_ASCII','O') for x in iob_list]
        ent_list = list(tok.values())[i]['ent_type']
        iob_ent = list(map('-'.join, zip(iob_list, ent_list)))
        token_tuple.append(list(zip(token_list, list(tok.values())[i]['tag'], iob_ent)))
    return(token_tuple)
def count_tokens(tok, non_punct):
    token_list = []
    p = re.compile('^[a-z]+$')
    for i in range(0,len(tok)):
        tokens = [x[0] for x in tok[i]]
        # strip punctuation
        tokens = [x.translate(str.maketrans('', '', string.punctuation)) for x in tokens]
        # return only alphabetic strings
        tokens = [x for x in tokens if p.match(x)]
        token_list.append(tokens)
    token_range = []
    for i in range(0,len(tok)):
        token_range.append(list(set(token_list[i])))
    token_range = [x for xs in token_range for x in xs]
    token_range = Counter(token_range)
    token_range = sorted(token_range.items(), key=lambda pair: pair[0], reverse=False)
    token_list = [x for xs in token_list for x in xs]
    token_list = Counter(token_list)
    token_list = sorted(token_list.items(), key=lambda pair: pair[0], reverse=False)
    tokens = np.array([x[0] for x in token_list])
    token_freq = np.array([x[1] for x in token_list])
    total_tokens = sum(token_freq)
    # Note: using non_punct for normalization
    token_prop = np.array(token_freq)/non_punct*1000000
    token_prop = token_prop.round(decimals=2)
    token_range = np.array([x[1] for x in token_range])/len(tok)*100
    token_range = token_range.round(decimals=2)
    token_counts = list(zip(tokens.tolist(), token_freq.tolist(), token_prop.tolist(), token_range.tolist()))
    token_counts = list(token_counts)
    return(token_counts)

class Window(QMainWindow):
    def runSpacyModel(self):
        if self.documentViewAction.isChecked():
            doc = self.nlp(self.inputText.toPlainText())
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
                    self.corp = corpus_add_files(
                        self.corp,
                        self.openFilesToBeAdded,
                        doc_label_fmt='{basename}')
                self.openFilesToBeAdded = []
                #Corpus processing
                corpus_total = corpus_num_tokens(self.corp)
                corpus_types = vocabulary_size(self.corp)
                total_punct = 0
                for doc in self.corp:
                    total_punct += sum(self.corp[doc]['is_punct'])
                non_punct = corpus_total - total_punct
                docs = doc_tokens(self.corp, with_attr=True)
                tp = convert_totuple(docs)
                token_counts = count_tokens(tp, non_punct)
                #TODO: display these
                sortedTokens = sorted(token_counts, key=itemgetter(1), reverse=True)
                #visuals
                self._oTreeCount()
                for (word, count, prop, range) in sortedTokens :
                    QTreeWidgetItem(self.outputTree, [word, str(count)] )

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
            self._oTreeCount()
            self.visuals.removeWidget(self.inputText)
            self.inputText.deleteLater()

    def _oTreeCount(self):
        self.outputTree.setColumnCount(2)
        self.outputTree.setHeaderLabels(["Word", "Count", "Prop", "Range"])
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
        self._oTreeCount()
        self.visuals.addWidget(self.outputTree, 1)
        workspace.addLayout(self.visuals)

        runButton = QPushButton()
        runButton.setText("Run analyzer")
        runButton.clicked.connect(self.runSpacyModel)
        workspace.addWidget(runButton)

        leftBar = QVBoxLayout()
        self.openFileW = QListWidget()
        self.openFileW.itemDoubleClicked.connect(self.openListDoubleClick)
        self.openFileW.setSelectionMode(self.openFileW.SelectionMode.ExtendedSelection)
        self.currFileW = QListWidget()
        self.currFileW.itemDoubleClicked.connect(self.currListDoubleClick)
        self.currFileW.setSelectionMode(self.currFileW.SelectionMode.ExtendedSelection)
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
        self.openFilesToBeAdded = []
        self.currFileDict = {}
        self.corp = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
