from logging import exception
from operator import truediv
from select import select
import sys
import spacy
import os
import re
import enum
import docuscospacy.corpus_analysis as scoA
import docuscospacy.corpus_utils as scoU
#Output of docuscospacy calls
import pandas

from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QAbstractItemView, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QTextEdit, QWidget, QFileDialog, QToolBar, QMenuBar, QMessageBox
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtCore import Qt
from itertools import *

from tmtoolkit.corpus import Corpus, vocabulary_size, doc_tokens, corpus_num_tokens, corpus_add_files
import corpusLibOverwrites

#Function to be passed into Corpus.from_Files
def pre_process(txt):
        txt = re.sub(r'\bits\b', 'it s', txt)
        txt = re.sub(r'\bIts\b', 'It s', txt)
        txt = " ".join(txt.split())
        return(txt)

@enum.unique
class ViewMode(enum.IntEnum):
    #Count of token frequencies
    freqTable = 0
    #Count of tags frequencies
    tagsTable = 1
    #Document-term matrix of raw tag counts
    tagsDTM = 2
    #Table of NGRAM frequencies
    NGramTable = 3
    #a table of collocations by association measure
    collacTable = 4
    #a KWIC table with the node word in the center column
    KWICCenter = 5
    #A keyness table comparing token frequencies from a taget and a reference corpus
    keyNessTable = 6

class Window(QMainWindow):
    #Used to change the viewMode in other functions
    def setViewMode(self, mode : ViewMode):
        self.viewMode = mode
    #Class used to make many similiar viewmode functions for updating the variable
    class ViewModeAction(QAction):
        def __init__(self, win, text : str, parent, mode : ViewMode) -> None:
            super().__init__(text, parent)
            self.win = win
            self.mode = mode
        def fn (self, checked : bool) -> None:
            self.win.setViewMode(self.mode)
    def runSpacyModel(self):
        """
        Corpus Processing function. Called when run alyzer is clicked. 
        Uses functions from docuscospacy to do processing.
        """
        #Begin Corpus Processing
        if self.documentViewAction.isChecked():
            if not (self.docViewFile is None):
                self.corp = self.corp = Corpus.from_files(
                            [self.docViewFile],
                            spacy_instance=self.nlp, 
                            raw_preproc=pre_process, 
                            spacy_token_attrs=['tag', 'ent_iob', 'ent_type', 'is_punct'],
                            doc_label_fmt='{basename}', max_workers = 1)
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
                self.openFilesToBeAdded = []
        self.runProgress.setText("Calculating Sums for Corpus")
        QApplication.processEvents()
        #Calculate total number of tokens to normalize and display
        if not (self.corp is None):
            corpus_total = corpus_num_tokens(self.corp)
            total_punct = 0
            for doc in self.corp:
                total_punct += sum(self.corp[doc]['is_punct'])
            non_punct = corpus_total - total_punct
            #TODO: display these
            tokenDict = scoA.convert_corpus(self.corp)
            print("CT: "+str(corpus_total)+", TP: "+str(total_punct)+", NP: "+str(non_punct)+", DL: "+str(len(tokenDict)))
            
            self.runProgress.setText("Sorting "+str(non_punct)+" tokens and building table")
            QApplication.processEvents()
            #Handles final processing and output
            self._outputFromtokenDict(tokenDict, non_punct)
        self.runProgress.setText("Done")

    # Action Functionality Placeholder
    def openFile(self):
        selectedFileNames = QFileDialog.getOpenFileNames(self, 'Open File', filter = "Text files (*.txt);; All Files (*)")
        #TODO add openFolders
        for fname in selectedFileNames[0]:
            if fname in self.openFileDict:
                self.openFileDict.update({fname : None})
            else:
                self.openFileDict.update({fname : None})
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
        if self.pd is None:
            msgBox =  QMessageBox(self)
            msgBox.setText("No results to save");
            msgBox.setInformativeText("Load files with open files\nAdd them to the workspace\nRun the analyzer\nThen save the results");
            msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
            msgBox.setDefaultButton(QMessageBox.StandardButton.Ok)
            msgBox.exec()
        else:
            selectedFileName = QFileDialog.getSaveFileName(self, 'Save File', filter = "Comma Separated Values (*.csv)")
            self.pd.to_csv(selectedFileName[0])
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
                self.currFileW.addItem(QListWidgetItem(item))
                self.currFileW.sortItems()
    def remove(self):
        fnames = self.currFileW.selectedItems()
        if not fnames: return
        for item in fnames:
            fname = item.toolTip()
            del self.currFileDict[fname]
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
            self.docViewFile = item.toolTip()
            self.inputText.setText(open(item.toolTip(), "r").read())
    def toggleTextEditor(self):
        if self.documentViewAction.isChecked():
            self.inputText = QTextEdit()
            self.inputText.setAcceptRichText(False)
            self.inputText.setReadOnly(True)
            self.visuals.insertWidget(0, self.inputText, 1)
        else:
            self.visuals.removeWidget(self.inputText)
            self.inputText.deleteLater()

    def _outputFromtokenDict(self, tokenDict, elements):
        """
        Initializes the output tree according to self.viewmode
        """
        self.outputFormat.actions()[self.viewMode].setChecked(True)
        #TODO Define These
        ng_span = 3
        node_word = "analyze"
        self.pd = None
        if   self.viewMode == ViewMode.freqTable:
            self.pd = scoA.frequency_table(tokenDict, elements)
        elif self.viewMode == ViewMode.tagsTable:
            self.pd = scoA.tags_table(tokenDict, elements)
        elif self.viewMode == ViewMode.tagsDTM:
            self.pd = scoA.tags_dtm(tokenDict)
        elif self.viewMode == ViewMode.NGramTable:
            self.pd = scoA.ngrams_table(tokenDict, ng_span, elements)
        elif self.viewMode == ViewMode.collacTable:
            self.pd = scoA.coll_table(tokenDict, node_word)
        elif self.viewMode == ViewMode.KWICCenter:
            self.pd = scoA.kwic_center_node(self.corp, node_word)
        elif self.viewMode == ViewMode.keyNessTable:
            #TODO: pd = scoA.keyness_table(target_counts, ref_counts)
            pass
        else:
            raise Exception("Unknown format. Should be impossible")
        #visuals
        self.runProgress.setText("Displaying output")
        QApplication.processEvents()
        if self.pd is None:
            self.outputTree.clear()
        else:
            #Update the visuals
            headers = self.pd.head(1)
            self.outputTree.setColumnCount(len(headers))
            self.outputTree.setHeaderLabels(headers)
            self.outputTree.clear()
            for tup in self.pd.itertuples(False, None) :
                QTreeWidgetItem(self.outputTree, list(map(str, tup)))

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
        #Makes the actions in a row. Need that first self arguement so class know which object to update
        self.ViewModeAction(self, "Token Frequency",         self.outputFormat, ViewMode.freqTable)
        self.ViewModeAction(self, "Tag Frequency",           self.outputFormat, ViewMode.tagsTable)
        self.ViewModeAction(self, "Document Term Matrix",    self.outputFormat, ViewMode.tagsDTM)
        self.ViewModeAction(self, "N-gram Frequencies",      self.outputFormat, ViewMode.NGramTable)
        self.ViewModeAction(self, "Collacations",            self.outputFormat, ViewMode.collacTable)
        self.ViewModeAction(self, "KWIC Table",              self.outputFormat, ViewMode.KWICCenter)
        self.ViewModeAction(self, "Keyness Between Corpora", self.outputFormat, ViewMode.keyNessTable)
        for action in self.outputFormat.actions():
            action.setCheckable(True)
            action.toggled.connect(action.fn)
            viewMenu.addAction(action)
        self.viewMode = ViewMode.freqTable
        self.outputFormat.setExclusive(True)
        self.outputFormat.actions()[self.viewMode].setChecked(True)

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
        self.outputTree.setHeaderLabels([""])
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
        barHolder = QHBoxLayout()

        extraLeftBar = QVBoxLayout()
        self.extraOpenFileW = QListWidget()
        self.extraOpenFileW.itemDoubleClicked.connect(self.openListDoubleClick)
        self.extraOpenFileW.setSelectionMode(self.extraOpenFileW.SelectionMode.ExtendedSelection)
        self.extraCurrFileW = QListWidget()
        self.extraCurrFileW.itemDoubleClicked.connect(self.currListDoubleClick)
        self.extraCurrFileW.setSelectionMode(self.extraCurrFileW.SelectionMode.ExtendedSelection)
        extraOpenButton = QPushButton()
        extraOpenButton.setText("Open")
        extraOpenButton.clicked.connect(self.openFile)
        extraCloseButton = QPushButton()
        extraCloseButton.setText("Close")
        extraCloseButton.clicked.connect(self.close)
        extraOpenAndCloseBox = QHBoxLayout()
        extraOpenAndCloseBox.addWidget(extraOpenButton)
        extraOpenAndCloseBox.addWidget(extraCloseButton)
        extraLeftBar.addLayout(extraOpenAndCloseBox)
        extraLeftBar.addWidget(self.extraOpenFileW)
        extraAddButton = QPushButton()
        extraAddButton.setText("Add")
        extraAddButton.clicked.connect(self.add)
        extraRemoveButton = QPushButton()
        extraRemoveButton.setText("Remove")
        extraRemoveButton.clicked.connect(self.remove)
        extraAddAndRemoveBox = QHBoxLayout()
        extraAddAndRemoveBox.addWidget(extraAddButton)
        extraAddAndRemoveBox.addWidget(extraRemoveButton)
        extraLeftBar.addLayout(extraAddAndRemoveBox)
        extraLeftBar.addWidget(self.extraCurrFileW)

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
        addListButton = QPushButton()
        addListButton.setText("Toggle List 2")
        global extraBarOn
        extraBarOn = 1
        # Delete Layout Functions
        def deleteItemsOfLayout(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
                    else:
                        deleteItemsOfLayout(item.layout())
        def boxdelete(self, box):
            for i in range(self.extraLeftBar.count()):
                layout_item = self.extraLeftBar.itemAt(i)
                if layout_item.barHolder() == box:
                    deleteItemsOfLayout(layout_item.layout())
                    self.extraLeftBar.removeItem(layout_item)
                    break

        def toggleList2(self):
            global extraBarOn
            if (extraBarOn == 0):
                """extraOpenAndCloseBox.addWidget(openButton)
                extraOpenAndCloseBox.addWidget(closeButton)
                # extraLeftBar.addWidget(self.extraOpenFileW)
                extraAddAndRemoveBox.addWidget(addButton)
                extraAddAndRemoveBox.addWidget(removeButton)
                # extraLeftBar.addWidget(self.extraCurrFileW)"""
                barHolder.addLayout(extraLeftBar)
                extraBarOn = 1
            else:
                extraOpenAndCloseBox.removeWidget(openButton)
                extraOpenAndCloseBox.removeWidget(closeButton)
                # extraLeftBar.removeWidget(self.extraOpenFileW)
                extraAddAndRemoveBox.removeWidget(addButton)
                extraAddAndRemoveBox.removeWidget(removeButton)
                # extraLeftBar.removeWidget(self.currFileW)
                barHolder.removeItem(extraLeftBar)
                extraBarOn = 0
        addListButton.clicked.connect(toggleList2)
        openAndCloseBox = QHBoxLayout()
        openAndCloseBox.addWidget(openButton)
        openAndCloseBox.addWidget(closeButton)
        openAndCloseBox.addWidget(addListButton)
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

        """extraOpenAndCloseBox = QHBoxLayout()
        extraOpenAndCloseBox.addWidget(openButton)
        extraOpenAndCloseBox.addWidget(closeButton)
        extraLeftBar.addLayout(extraOpenAndCloseBox)
        extraLeftBar.addWidget(self.openFileW)
        extraAddAndRemoveBox = QHBoxLayout()
        extraAddAndRemoveBox.addWidget(addButton)
        extraAddAndRemoveBox.addWidget(removeButton)
        extraLeftBar.addLayout(extraAddAndRemoveBox)
        extraLeftBar.addWidget(self.currFileW)"""

        barHolder.addLayout(leftBar)
        barHolder.addLayout(extraLeftBar)
        mainView.addLayout(barHolder, 1)
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
        self.viewMode = ViewMode.freqTable
        self._createMenuBar()
        #initialize model
        self.nlp = spacy.load(os.path.join(os.path.dirname(__file__) , "model-new"))
        #Functionality
        #Functional part of Open File List. Other argument is None 
        self.openFileDict = {}
        #Used when a docView file is open. stores which file it is
        self.docViewFile = None
        #Keeps track of additions to the Current File List. Added when analyzer is run
        self.openFilesToBeAdded = []
        #Functional part of Open File List. Other argument is None 
        self.currFileDict = {}
        self.corp = None
        #panda object. What is shown in outputTree when made in _outputFromtokenDict
        self.pd = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = Window()
    win.show()
    sys.exit(app.exec())
