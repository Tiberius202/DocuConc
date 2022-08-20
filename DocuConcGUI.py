from ast import keyword
import sys
import spacy
import os
import re
import enum
#David Brown's NLP library. The functional part of this program
import docuscospacy.corpus_analysis as scoA

#PyQt Front end for gui
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QTreeView, QHeaderView, QTextEdit, QWidget, QFileDialog, QMessageBox, QLineEdit
from PyQt6.QtGui import QAction, QActionGroup, QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

#TMToolkit for managing corpora. Used by docuscospacy
from tmtoolkit.corpus import Corpus, corpus_num_tokens, corpus_add_files
#The following file overwrites tmtoolkit functions in order to display the loading progress
import corpusLibOverwrites

def pre_process(txt):
    """Function to be passed into Corpus.from_Files"""
    txt = re.sub(r'\bits\b', 'it s', txt)
    txt = re.sub(r'\bIts\b', 'It s', txt)
    txt = " ".join(txt.split())
    return(txt)

@enum.unique
class ViewMode(enum.IntEnum):
    """Enum used to handle which mode and form of analysis is"""
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
    """Window for PyQtGui. Wraps all PyQt functionality"""
    def setViewMode(self, mode : ViewMode):
        """Used to change the viewMode in other functions"""
        self.viewMode = mode

    def openKeyword(self):
        """Opens the keyword input and ranges"""
        keywordBar = QHBoxLayout()
        self.keyword = QLineEdit("Keyword")
        self.ng_span = QLineEdit("3")
        self.ng_span.setInputMask("D")
        keywordBar.addWidget(self.keyword, 4)
        keywordBar.addWidget(self.ng_span, 1)
        self.workspace.insertLayout(2, keywordBar)

    def closeKeyword(self):
        """Closes the keyword input and ranges"""
        bar = self.workspace.takeAt(2)
        while bar.count() > 0:
            item = bar.takeAt(0)
            widget = item.widget()
            widget.deleteLater()

    class ViewModeAction(QAction):
        """Class used to make many similiar viewmode functions for updating the variable"""
        def __init__(self, win, text : str, parent, mode : ViewMode) -> None:
            super().__init__(text, parent)
            self.win = win
            self.mode = mode
        def fn (self, checked : bool) -> None:
            if checked:
                def needsKeyword(m):
                    return m == ViewMode.collacTable or m == ViewMode.KWICCenter
                def needsSpan(m):
                    return m == ViewMode.NGramTable
                if       needsKeyword(self.mode) and not needsKeyword(self.win.viewMode):
                    self.win.openKeyword()
                elif not needsKeyword(self.mode) and     needsKeyword(self.win.viewMode):
                    self.win.closeKeyword()
                if       needsSpan(self.mode) and not needsSpan(self.win.viewMode):
                    self.win.openKeyword()
                elif not needsSpan(self.mode) and     needsSpan(self.win.viewMode):
                    self.win.closeKeyword()
                self.win.setViewMode(self.mode)

    def runSpacyModel(self):
        """
        Corpus Processing function. Called when run analyzer is clicked. 
        Uses from_files and add_files from TMToolkit to do processing.
        """
        #Begin Corpus Processing
        if self.documentViewAction.isChecked():
            if not (self.docViewFile is None):
                self.corp = Corpus.from_files(
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
            self.non_punct = corpus_total - total_punct
            self.tokenDict = scoA.convert_corpus(self.corp)
            self.tokenLbl.setText("Token Count: " + str(corpus_total))
            self.wordLbl.setText("Word Count: " + str(self.non_punct))
            self.docLbl.setText("Documents analyzed: " + str(len(self.tokenDict)))
            
            self.runProgress.setText("Sorting "+str(self.non_punct)+" tokens and building table")
            QApplication.processEvents()
            #Handles docuscospacy processing and output
            self._outputFromtokenDict()
        self.runProgress.setText("Done")

    def toggleMode(self):
        """Used by the modeButton. changes posMode"""
        if self.posMode == "pos":
            self.modeButton.setText("Docuscope Tags")
            self.modeButton.setToolTip("Click to change to Part of Speech tagging")
            self.posMode = "ds"
        elif self.posMode == "ds":
            self.modeButton.setText("Part of Speech")
            self.modeButton.setToolTip("Click to change to Docuscope tagging")
            self.posMode = "pos"
        else:
            raise Exception("Error: unknown self.posMode")
        self._outputFromtokenDict()

    def openFile(self):
        """Opens files to the openFileDict and openFileW"""
        selectedFileNames = QFileDialog.getOpenFileNames(self, 'Open File', filter = "Text files (*.txt);; All Files (*)")
        for fname in selectedFileNames[0]:
            if fname in self.openFileDict:
                self.openFileDict.update({fname : None})
            else:
                self.openFileDict.update({fname : None})
                listItem = QListWidgetItem()
                listItem.setToolTip(fname)
                listItem.setText(fname.replace("\\", "/").split("/")[-1])
                self.openFileW.addItem(listItem)
        self.openFileW.sortItems()
    def saveFile(self):
        """Saves outputTree to csv using pandas to csv command"""
        if self.pd is None:
            msgBox =  QMessageBox(self)
            msgBox.setText("No results to save")
            msgBox.setInformativeText("Load files with open files\nAdd them to the workspace\nRun the analyzer\nThen save the results")
            msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
            msgBox.setDefaultButton(QMessageBox.StandardButton.Ok)
            msgBox.exec()
        else:
            selectedFileName = QFileDialog.getSaveFileName(self, 'Save File', filter = "Comma Separated Values (*.csv)")
            self.pd.to_csv(selectedFileName[0])
    def close(self):
        """Closes selected files. Removes from all lists and fileDicts"""
        fnames = self.openFileW.selectedItems()
        self.runProgress.setText("Closing "+str(len(fnames))+" files")
        removedFromCurr = False
        if not fnames: return
        for item in fnames:
            fname = item.toolTip()
            del self.openFileDict[fname]
            #update visuals
            addedVersions = self.currFileW.findItems(item.text(), Qt.MatchFlag.MatchExactly)
            for currItem in addedVersions:
                if currItem.toolTip() == item.toolTip():
                    removedFromCurr = True
                    del self.currFileDict[fname]
                    #update visuals
                    self.currFileW.takeItem(self.currFileW.row(currItem))
            self.openFileW.takeItem(self.openFileW.row(item))
        if removedFromCurr:
            self.openFilesToBeAdded = []
            self.corp = None
            for item in self.currFileDict.keys():
                self.openFilesToBeAdded.append(item)
        self.runProgress.setText("Nothing running")
    def add(self):
        """
        Adds file from openFileDict to currFileDict
        Updates files to be added so that they are included on next run of the analyzer
        """
        fnames = self.openFileW.selectedItems()
        if not fnames: return
        for item in fnames:
            fname = item.toolTip()
            if  (fname) not in self.currFileDict:
                self.currFileDict.update({fname : None})
                self.openFilesToBeAdded.append(fname)
                self.currFileW.addItem(QListWidgetItem(item))
        self.currFileW.sortItems()
    def remove(self):
        """
        Removes files from currFileDict. Undoes Add.
        Refreshes the currFileDict so that a new corpus is made. 
        Tmtoolkit does not have remove from files, but does have add.
        """
        fnames = self.currFileW.selectedItems()
        if not fnames: return
        for item in fnames:
            fname = item.toolTip()
            del self.currFileDict[fname]
            #update visuals
            self.currFileW.takeItem(self.currFileW.row(item))
        self.openFilesToBeAdded = []
        self.corp = None
        for item in self.currFileDict.keys():
            self.openFilesToBeAdded.append(item)
    def helpContent(self):
        """Logic for launching help goes here..."""
        self.runProgress.setText("<b>Help > Help Content...</b> clicked")
    def about(self):
        """Logic for showing an about dialog content goes here..."""
        self.runProgress.setText("<b>Help > About...</b> clicked")
    def openListDoubleClick(self, item):
        """Used when an item of the openListW is clicked. Adds file to currFileW"""
        fname = item.toolTip()
        if  (fname) not in self.currFileDict:
            self.currFileDict.update({fname : None})
            self.openFilesToBeAdded.append(fname)
            #update visuals
            self.currFileW.addItem(QListWidgetItem(item))
            self.currFileW.sortItems()
    def currListDoubleClick(self, item):
        """Used whan an item of the currListW is clicked. Opens to the right if in docViewMode"""
        if self.documentViewAction.isChecked():
            self.docViewFile = item.toolTip()
            self.inputText.setText(open(item.toolTip(), "r").read())
    def toggleTextEditor(self):
        """Opens and closes docViewMode"""
        if self.documentViewAction.isChecked():
            self.inputText = QTextEdit()
            self.inputText.setAcceptRichText(False)
            self.inputText.setReadOnly(True)
            self.visuals.insertWidget(0, self.inputText, 1)
        else:
            self.visuals.removeWidget(self.inputText)
            self.inputText.deleteLater()

    def _outputFromtokenDict(self):
        """
        Initializes the output tree according to self.viewmode
        Used in RunSpacyModel and after switching between part of speech and docuscope modes
        """
        self.outputFormat.actions()[self.viewMode].setChecked(True)
        self.pd = None
        if   self.viewMode == ViewMode.freqTable:
            self.pd = scoA.frequency_table(self.tokenDict, self.non_punct, self.posMode)
        elif self.viewMode == ViewMode.tagsTable:
            self.pd = scoA.tags_table(self.tokenDict, self.non_punct, self.posMode)
        elif self.viewMode == ViewMode.tagsDTM:
            self.pd = scoA.tags_dtm(self.tokenDict, self.posMode)
        elif self.viewMode == ViewMode.NGramTable:
            span = int(self.ng_span.text())
            if span < 2:
                msgBox = QMessageBox(self)
                msgBox.setText("Span must be between 2 and 5 inclusive")
                msgBox.setInformativeText("Rerun the analyzer with correct span between 2 and 5 inclusive.\nAnalyzer has been run with span of 2")
                msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
                msgBox.setDefaultButton(QMessageBox.StandardButton.Ok)
                msgBox.exec()
                span = 2
                self.ng_span.setText(str(span))
            if span > 5:
                msgBox = QMessageBox(self)
                msgBox.setText("Span must be between 2 and 5 inclusive")
                msgBox.setInformativeText("Rerun the analyzer with correct span between 2 and 5 inclusive.\nAnalyzer has been run with span of 5")
                msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
                msgBox.setDefaultButton(QMessageBox.StandardButton.Ok)
                msgBox.exec()
                span = 5
                self.ng_span.setText(str(span))
            self.pd = scoA.ngrams_table(self.tokenDict, span, self.non_punct, self.posMode)
        elif self.viewMode == ViewMode.collacTable:
            self.pd = scoA.coll_table(self.tokenDict, self.keyword.text(), count_by=self.posMode)
        elif self.viewMode == ViewMode.KWICCenter:
            self.pd = scoA.kwic_center_node(self.corp, self.keyword.text())
        elif self.viewMode == ViewMode.keyNessTable:
            #TODO: pd = scoA.keyness_table(target_counts, ref_counts)
            pass
        else:
            raise Exception("Unknown format. Should be impossible")
        #Update the visuals
        self.runProgress.setText("Displaying output")
        QApplication.processEvents()
        self.outputModel.clear()
        if self.pd is None:
            self.outputLbl.setText("Row Count: 0")
        else:
            headers = self.pd.columns
            self.outputModel.setHorizontalHeaderLabels(headers)
            self.outputModel.setColumnCount(len(headers))
            self.outputTree.header().setSortIndicatorShown(True)
            self.outputTree.setSortingEnabled(False)
            self.outputLbl.setText("Row Count: "+str(len(self.pd)))
            #Fill in data. Sorting should be off when inserting for performance
            for tup in self.pd.itertuples(False, None):
                items = []
                for ite in list(tup):
                    item = QStandardItem()
                    item.setData(str(ite), Qt.ItemDataRole.DisplayRole)
                    item.setData(ite, Qt.ItemDataRole.UserRole)
                    items.append(item)
                self.outputModel.appendRow(items)
            self.outputTree.setSortingEnabled(True)

    def _createMenuBar(self):
        """
        Called on initialization to create the menu bar
        Has four menus, File, View, Settings, and About
        """
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
        #ViewMode related functionality
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

        settingsMenu = menuBar.addMenu("Settings")
        helpMenu = menuBar.addMenu("Help")
        helpContentAction = QAction("&Help Content", self)
        helpContentAction.triggered.connect(self.helpContent)
        helpMenu.addAction(helpContentAction)
        aboutAction = QAction("&About", self)
        aboutAction.triggered.connect(self.about)
        helpMenu.addAction(aboutAction)

    def _createMainView(self):
        """
        Called on initialization to create the main view Where all of the interactables are
        """
        mainView = QHBoxLayout()

        self.workspace = QVBoxLayout()

        self.visuals = QHBoxLayout()
        self.outputTree = QTreeView()
        self.outputModel = QStandardItemModel(None)
        self.outputModel.setSortRole(Qt.ItemDataRole.UserRole)
        self.outputTree.setModel(self.outputModel)
        self.outputTree.setColumnWidth(0, 200)
        header = QHeaderView(Qt.Orientation.Horizontal)
        self.outputModel.setHorizontalHeaderLabels(["Output Window"])
        self.outputTree.setUniformRowHeights(True)
        self.visuals.addWidget(self.outputTree, 1)
        self.workspace.addLayout(self.visuals)

        countsBox = QHBoxLayout()
        self.outputLbl = QLabel("Row Count: 0")
        self.outputLbl.setToolTip("The number of unique elements analyzed. i.e. the rows of the above table")
        countsBox.addWidget(self.outputLbl)
        self.tokenLbl = QLabel("Token Count: 0")
        self.tokenLbl.setToolTip("A count of the total tokens analyzed")
        countsBox.addWidget(self.tokenLbl)
        self.wordLbl = QLabel("Word Count: 0")
        self.wordLbl.setToolTip("A count of the total tokens analyzed minus the punctuation")
        countsBox.addWidget(self.wordLbl)
        self.docLbl = QLabel("Documents analyzed: 0")
        self.docLbl.setToolTip("Total number of files analyzed")
        countsBox.addWidget(self.docLbl)
        self.workspace.addLayout(countsBox)

        analButtons = QHBoxLayout()
        runButton = QPushButton()
        runButton.setText("Run analyzer")
        runButton.clicked.connect(self.runSpacyModel)
        self.modeButton = QPushButton()
        self.modeButton.setText("Part of Speech")
        self.modeButton.setToolTip("Click to change to Docuscope tagging")
        self.modeButton.clicked.connect(self.toggleMode)
        analButtons.addWidget(runButton, 3)
        analButtons.addWidget(self.modeButton, 1)
        self.workspace.addLayout(analButtons)

        self.runProgress = QLabel("Nothing Running")
        def newTextOutput(s : str):
            self.runProgress.setText(s)
            QApplication.processEvents()
        corpusLibOverwrites.textOutput = newTextOutput
        self.workspace.addWidget(self.runProgress, alignment=Qt.AlignmentFlag.AlignRight)

        #Used for managing files
        barHolder = QHBoxLayout()

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

        barHolder.addLayout(leftBar)
        mainView.addLayout(barHolder, 1)
        mainView.addLayout(self.workspace, 4)
        return mainView

    def __init__(self, parent=None):
        """Creates Window. Initializes PyQt app"""
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
        self.nlp = spacy.load(os.path.join(os.path.dirname(__file__) , "spacy-model"))
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
        #posTagging vs docuscope tagging mode
        self.posMode = "pos"

if __name__ == "__main__":
    """Boilerplate for running PyQt App. Uses Window class"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = Window()
    win.show()
    sys.exit(app.exec())
