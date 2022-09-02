import sys
import spacy
import os
import re
import enum
#David Brown's NLP library. The functional part of this program
import docuscospacy.corpus_analysis as scoA

#PyQt Front end for gui
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QTreeView, QTextEdit, QWidget, QFileDialog, QMessageBox, QLineEdit, QButtonGroup, QToolButton
from PyQt6.QtGui import QAction, QActionGroup, QStandardItemModel, QStandardItem, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QRect, QSortFilterProxyModel

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

class ModeSwitch(QPushButton):
    """Rounded toggle switch used for various modes"""
    def __init__(self, leftOption, rightOption, width, parent = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumHeight(22)
        self.left = leftOption
        self.right = rightOption
        self.width = width
        self.setMinimumWidth(int(self.width*2.5))

    def paintEvent(self, event):
        label = self.left if self.isChecked() else self.right
        bg_color = QColor(180,180,180) if self.isChecked() else QColor(180,180,180)

        radius = 10
        center = self.rect().center()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(center)
        painter.setBrush(QColor(236,236,236))

        pen = QPen(QColor(86,86,86))
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRoundedRect(QRect(-self.width, -radius, 2*self.width, 2*radius), radius, radius)
        painter.setBrush(QBrush(bg_color))
        sw_rect = QRect(-radius, -radius, self.width + radius, 2*radius)
        if not self.isChecked():
            sw_rect.moveLeft(-self.width)
        painter.drawRoundedRect(sw_rect, radius, radius)
        painter.drawText(sw_rect, Qt.AlignmentFlag.AlignCenter, label)

class Window(QMainWindow):
    """Window for PyQtGui. Wraps all PyQt functionality"""
    def openSpan(self):
        """Opens the keyword input and ranges"""
        spanBar = QHBoxLayout()
        self.ng_span = QLineEdit("3")
        self.ng_span.setInputMask("D")
        spanBar.addWidget(QLabel("Span of the N-Gram"))
        spanBar.addWidget(self.ng_span)
        self.workspace.insertLayout(2, spanBar)
    def openKeyword(self):
        """Opens the keyword input and ranges"""
        keywordBar = QHBoxLayout()
        self.keyword = QLineEdit()
        keywordBar.addWidget(QLabel("Keyword:"))
        keywordBar.addWidget(self.keyword)
        keywordBar.addWidget(QLabel("Case sensitive: "))
        self.keywordIgnoreCase = ModeSwitch("Case Sensitive", "Ignore Case", 100)
        keywordBar.addWidget(self.keywordIgnoreCase)
        keywordBar.addWidget(QLabel("Globular Search: "))
        self.keywordGlob = ModeSwitch("Off", "On", 32)
        keywordBar.addWidget(self.keywordGlob)
        self.workspace.insertLayout(2, keywordBar)
    def openCollBar(self):
        """Opens the keyword input and ranges"""
        keywordBar = QHBoxLayout()
        self.keyword = QLineEdit("")
        self.lSpan = QLineEdit("4")
        self.lSpan.setInputMask("D")
        self.rSpan = QLineEdit("4")
        self.rSpan.setInputMask("D")
        self.collButton= QToolButton()
        self.collStat = QActionGroup(self.collButton)
        pmiAction = QAction("pmi")
        pmiAction.setCheckable(True)
        self.collStat.addAction(pmiAction)
        npmiAction = QAction("npmi")
        npmiAction.setCheckable(True)
        self.collStat.addAction(npmiAction)
        pmi2Action = QAction("pmi2")
        pmi2Action.setCheckable(True)
        self.collStat.addAction(pmi2Action)
        pmi3Action = QAction("pmi3")
        pmi3Action.setCheckable(True)
        self.collStat.addAction(pmi3Action)
        self.collStat.setExclusive(True)
        self.collStat.actions()[0].setChecked(True)
        self.collButton.setMinimumWidth(50)
        self.collButton.setText("pmi")
        self.collButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.collButton.setPopupMode(self.collButton.ToolButtonPopupMode.InstantPopup)
        self.collButton.setAutoRaise(True)
        self.collButton.addActions(self.collStat.actions())
        def changeText (action):
            self.collButton.setText(action.text())
        self.collButton.triggered.connect(changeText)
        keywordBar.addWidget(QLabel("Keyword:"))
        keywordBar.addWidget(self.keyword, 4)
        keywordBar.addWidget(QLabel("Left span:"))
        keywordBar.addWidget(self.lSpan, 1)
        keywordBar.addWidget(QLabel("Right span:"))
        keywordBar.addWidget(self.rSpan, 1)
        keywordBar.addWidget(QLabel("Frequency Normalization:"))
        keywordBar.addWidget(self.collButton, 1)
        self.workspace.insertLayout(2, keywordBar)

    def closeBar(self):
        """Closes the keyword input and ranges"""
        bar = self.workspace.takeAt(2)
        while bar.count() > 0:
            item = bar.takeAt(0)
            widget = item.widget()
            widget.deleteLater()

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
            self.modeButton.setToolTip("Click to change to Part of Speech tagging")
            self.posMode = "ds"
        elif self.posMode == "ds":
            self.modeButton.setToolTip("Click to change to Docuscope tagging")
            self.posMode = "pos"
        else:
            raise Exception("Error: unknown self.posMode")
        self._outputFromtokenDict()
        self.runProgress.setText("Done")

    def modeBarClicked (self, id, checked):
        def needsKeyword(m):
            return m == ViewMode.KWICCenter
        def needsSpan(m):
            return m == ViewMode.NGramTable
        def needsColl(m):
            return m == ViewMode.collacTable
        if checked:
            if   needsKeyword(id):
                self.openKeyword()
            elif needsSpan(id) :
                self.openSpan()
            elif needsColl(id):
                self.openCollBar()
        else:
            if needsKeyword(id) or needsSpan(id) or needsColl(id):
                self.closeBar()

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
        """TODO: replace CSV. Saves outputTree to token seperated values using pandas to json command"""
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
        removedFromExtra = False
        if not fnames: return
        for item in fnames:
            fname = item.toolTip()
            del self.openFileDict[fname]
            #Remove from currFile list as well
            addedVersions = self.currFileW.findItems(item.text(), Qt.MatchFlag.MatchExactly)
            for currItem in addedVersions:
                if currItem.toolTip() == item.toolTip():
                    removedFromCurr = True
                    del self.currFileDict[fname]
                    #update visuals
                    self.currFileW.takeItem(self.currFileW.row(currItem))
            #Remove from extraurrFile if it exists
            if self.addListButton.isChecked():
                addedVersions = self.extraCurrFileW.findItems(item.text(), Qt.MatchFlag.MatchExactly)
                for currItem in addedVersions:
                    if currItem.toolTip() == item.toolTip():
                        removedFromExtra = True
                        del self.extraCurrFileDict[fname]
                        #update visuals
                        self.extraCurrFileW.takeItem(self.extraCurrFileW.row(currItem))
            #Update openFileW
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
    def extraAdd(self):
        """
        Adds file from openFileDict to extraCurrFileDict
        """
        fnames = self.openFileW.selectedItems()
        if not fnames: return
        for item in fnames:
            fname = item.toolTip()
            if  (fname) not in self.extraCurrFileDict:
                self.extraCurrFileDict.update({fname : None})
                self.extraCurrFileW.addItem(QListWidgetItem(item))
        self.extraCurrFileW.sortItems()
    def remove(self):
        """
        Removes files from currFileDict. Undoes Add.
        Refreshes the openFilesToBeAdded so that a new corpus is made. 
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
    def extraRemove(self):
        """
        Removes files from extraCurrFileDict. Undoes extraAdd.
        """
        fnames = self.extraCurrFileW.selectedItems()
        if not fnames: return
        for item in fnames:
            fname = item.toolTip()
            del self.extraCurrFileDict[fname]
            #update visuals
            self.extraCurrFileW.takeItem(self.extraCurrFileW.row(item))
    def helpContent(self):
        """Logic for launching help goes here..."""
        self.runProgress.setText("<b>Help > Help Content...</b> clicked")
    def about(self):
        aboutBox =  QMessageBox(self)
        aboutBox.setText("About")
        aboutBox.setInformativeText("Made by:\nJonathan Wilson - Developer\nBenjamin Wilson - Developer\nDavid Brown - https://www.cmu.edu/dietrich/english/about-us/faculty/bios/david-brown.html\nDavid Kaufer - https://www.cmu.edu/dietrich/english/about-us/faculty/bios/david-kaufer.html\nSuguru Ishizaki - https://www.cmu.edu/dietrich/english/about-us/faculty/bios/suguru-ishizaki.html")
        aboutBox.setStandardButtons(QMessageBox.StandardButton.Ok)
        aboutBox.setDefaultButton(QMessageBox.StandardButton.Ok)
        aboutBox.setStyleSheet("QLabel{min-width: 700px;}")
        aboutBox.exec()

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
        Initializes the output tree according to the view mode
        Used in RunSpacyModel and after switching between part of speech and docuscope modes
        """
        if self.corp == None: return
        vMode = self.outputFormat.checkedId()
        self.outputFormat.buttons()[vMode].setChecked(True)
        self.pd = None
        if   vMode == ViewMode.freqTable:
            self.pd = scoA.frequency_table(self.tokenDict, self.non_punct, self.posMode)
        elif vMode == ViewMode.tagsTable:
            self.pd = scoA.tags_table(self.tokenDict, self.non_punct, self.posMode)
        elif vMode == ViewMode.tagsDTM:
            self.pd = scoA.tags_dtm(self.tokenDict, self.posMode)
        elif vMode == ViewMode.NGramTable:
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
        elif vMode == ViewMode.collacTable:
            self.pd = scoA.coll_table(self.tokenDict, self.keyword.text(), int(self.lSpan.text()), int(self.rSpan.text()), self.collStat.checkedAction().text(), self.posMode)
        elif vMode == ViewMode.KWICCenter:
            self.pd = scoA.kwic_center_node(self.corp, self.keyword.text(), not(self.keywordIgnoreCase.isChecked()), not (self.keywordGlob.isChecked()))
        elif vMode == ViewMode.keyNessTable:
            if len(self.extraCurrFileDict) > 0:
                self.runProgress.setText("Generating target frequency table")
                targetCounts = scoA.frequency_table(self.tokenDict, self.non_punct, self.posMode)
                self.runProgress.setText("Generating corpus from reference list")
                extraCorp = Corpus.from_files(
                    self.extraCurrFileDict.keys(),
                    spacy_instance=self.nlp,
                    raw_preproc=pre_process,
                    spacy_token_attrs=['tag', 'ent_iob', 'ent_type', 'is_punct'],
                    doc_label_fmt='{basename}', max_workers = 1)
                self.runProgress.setText("Converting corpus to token dictionary")
                extraDict = scoA.convert_corpus(extraCorp)
                refCounts = scoA.frequency_table(extraDict, self.non_punct, self.posMode)
                self.pd = scoA.keyness_table(targetCounts, refCounts)
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
            self.outputTree.setSortingEnabled(False)
            self.outputLbl.setText("Row Count: "+str(len(self.pd)))
            #Fill in data. Sorting should be off when inserting for performance
            for tup in self.pd.itertuples(False, None):
                items = []
                for ite in list(tup):
                    item = QStandardItem()
                    item.setData(str(ite), Qt.ItemDataRole.DisplayRole)
                    item.setData(ite, Qt.ItemDataRole.UserRole)
                    item.setEditable(False)
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

        modeBox = QHBoxLayout()
        self.outputFormat = QButtonGroup()
        #Makes the actions in a row. Need that first self arguement so class know which object to update
        modeBox.addWidget(QPushButton("Token Frequency"))
        modeBox.addWidget(QPushButton("Tag Frequency"))
        modeBox.addWidget(QPushButton("Document Term Matrix"))
        modeBox.addWidget(QPushButton("N-gram Frequencies"))
        modeBox.addWidget(QPushButton("Collacations"))
        modeBox.addWidget(QPushButton("KWIC Table"))
        modeBox.addWidget(QPushButton("Keyness Between Corpora"))
        for i in range(modeBox.count()):
            action = modeBox.itemAt(i).widget()
            action.setCheckable(True)
            self.outputFormat.addButton(action, i)
        self.outputFormat.setExclusive(True)
        self.outputFormat.buttons()[0].setChecked(True)
        self.outputFormat.idToggled.connect(self.modeBarClicked)
        self.workspace.addLayout(modeBox)

        self.visuals = QHBoxLayout()
        self.outputTree = QTreeView()
        self.outputModel = QStandardItemModel(None)
        self.outputModel.setHorizontalHeaderLabels(["Output Window"])
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSortRole(Qt.ItemDataRole.UserRole)
        self.proxyModel.setSourceModel(self.outputModel)
        self.outputTree.setModel(self.proxyModel)
        self.outputTree.setSelectionBehavior(self.outputTree.SelectionBehavior.SelectRows)
        self.outputTree.setColumnWidth(0, 200)
        self.outputTree.setUniformRowHeights(True)
        self.visuals.addWidget(self.outputTree, 1)
        self.workspace.addLayout(self.visuals)

        filterBox = QHBoxLayout()
        filterBox.addWidget(QLabel("Filter: "))
        self.searchbar = QLineEdit()
        def exactFilter(s):
            return self.proxyModel.setFilterRegularExpression("\A"+s.replace("_", ".*")+"\z")
        self.searchbar.textChanged.connect(exactFilter)
        filterBox.addWidget(self.searchbar, 3)
        filterBox.addWidget(QLabel("Column: "))
        self.filterColumnSelector = QLineEdit("1")
        self.filterColumnSelector.setInputMask("D")
        def filterGivenStr(s):
            if s != "":
                self.proxyModel.setFilterKeyColumn(int(s)-1)
        filterGivenStr(self.filterColumnSelector.text())
        self.filterColumnSelector.textChanged.connect(filterGivenStr)
        filterBox.addWidget(self.filterColumnSelector)
        self.workspace.addLayout(filterBox)

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
        self.modeButton = ModeSwitch("DS", "POS", 32)
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
        self.addListButton = QPushButton()
        self.addListButton.setText("Toggle Ref. Corpus")
        self.addListButton.setCheckable(True)
        # Functions for adding and removing list 2
        def openExtraBar():
                extraAddButton = QPushButton()
                extraAddButton.setText("Add")
                extraAddButton.clicked.connect(self.extraAdd)
                extraRemoveButton = QPushButton()
                extraRemoveButton.setText("Remove")
                extraRemoveButton.clicked.connect(self.extraRemove)
                extraAddAndRemoveBox = QHBoxLayout()
                extraAddAndRemoveBox.addWidget(QLabel("Reference corpus:"))
                extraAddAndRemoveBox.addWidget(extraAddButton)
                extraAddAndRemoveBox.addWidget(extraRemoveButton)
                self.extraCurrFileW = QListWidget()
                self.extraCurrFileW.setSelectionMode(self.extraCurrFileW.SelectionMode.ExtendedSelection)
                self.extraCurrFileDict = {}
                leftBar.addLayout(extraAddAndRemoveBox)
                leftBar.addWidget(self.extraCurrFileW)
        def closeExtraBar():
                bar = leftBar.takeAt(4)
                while bar.count() > 0:
                    item = bar.takeAt(0)
                    widget = item.widget()
                    widget.deleteLater()
                leftBar.removeWidget(self.extraCurrFileW)
                self.extraCurrFileW.deleteLater()
        def toggleExtraFileW(b):
            if b:
                openExtraBar()
            else:
                closeExtraBar()
        #End functions for adding and remocing list 2
        self.addListButton.clicked.connect(toggleExtraFileW)
        openAndCloseBox = QHBoxLayout()
        openAndCloseBox.addWidget(openButton)
        openAndCloseBox.addWidget(closeButton)
        openAndCloseBox.addWidget(self.addListButton)

        leftBar.addLayout(openAndCloseBox)
        leftBar.addWidget(self.openFileW)
        addButton = QPushButton()
        addButton.setText("Add")
        addButton.clicked.connect(self.add)
        removeButton = QPushButton()
        removeButton.setText("Remove")
        removeButton.clicked.connect(self.remove)
        addAndRemoveBox = QHBoxLayout()
        addAndRemoveBox.addWidget(QLabel("Target corpus:"), 0)
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
        self.setWindowTitle("Docuconc 1.0")
        self.resize(1280, 720)
        centralWidget = QWidget()
        centralWidget.setLayout(self._createMainView())
        self.setCentralWidget(centralWidget)
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
