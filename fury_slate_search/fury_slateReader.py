import nuke
import os
import pickle
import re

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui

from nukescripts import panels

pPath = '\\\\vfx\\fury\\tools\\lib\\hPath.pkl'

# just a quick subclass of the QLineEdit so that
# if you were to click in, it'll empty out the text.


class FocusClearLineEdit(QtGui.QLineEdit):

    def __init__(self, *args, **kwargs):
        super(FocusClearLineEdit, self).__init__(*args, **kwargs)
        self.inDefault = True
        self.default = args[0]

    def focusInEvent(self, event):
        if self.inDefault:
            self.setText(None)
            self.inDefault = False

    def reset_to_default(self):
        self.inDefault = True
        self.setText(self.default)


class SlateLookupWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(SlateLookupWindow, self).__init__(parent)

        # model section
        self._init_data()
        self._build_UI()

    def _init_data(self):
        self.results = {}
        self.database = pPath

    def load_file(self, *args):
        sels = [str(x.text()) for x in self.results_list.selectedItems()]
        sels = []
        for x in self.results_list.selectedItems():
            s = [x.text(), x.data(0), x.data(33), x.data(34), x.data(35)]
            sels.append(s)
        if len(sels) == 1:
            sel = sels[0]
            ln, lm, path, sf, ef = sel
            readNode = nuke.createNode('Read', inpanel=False)
            readNode['file'].fromUserText(path)
            if path.lower().endswith('.jpg'):
                readNode['first'].setValue(int(sf))
                readNode['last'].setValue(int(ef))
            self.last_action.setText('added ' + path + ' to node graph')

    def _build_UI(self):

        # this block defines the search area
        self.searchblockLayout = QtGui.QHBoxLayout()
        self.searchLabel = QtGui.QLabel('Slate Name:')
        self.searchBox = FocusClearLineEdit(
            'e.g. : X-231-N0021, or X_1_sxs_312')
        self.searchGo = QtGui.QPushButton('search!')

        self.searchblockLayout.addWidget(self.searchLabel)
        self.searchblockLayout.addWidget(self.searchBox)
        self.searchblockLayout.addWidget(self.searchGo)

        # just a simple text reminder string so we can se who is using it
        self.dbinuse = QtGui.QLabel('using: {db}'.format(db=self.database))
        self.dbinuse.setDisabled(True)  # just for that lovely light grey :P

        # this is the result area - we're using a simple QListWidget.

        self.last_action = QtGui.QLabel('')
        self.results_label = QtGui.QLabel('Results')
        self.results_label.setDisabled(True)
        self.results_list = QtGui.QListWidget()
        self.results_list.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        # assemble main layout from pieces
        # master layout is vertical stacking
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().addLayout(
            self.searchblockLayout, alignment=QtCore.Qt.AlignTop)
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().addWidget(self.last_action)
        self.layout().addWidget(self.results_label)
        self.layout().addWidget(self.results_list)
        self.layout().addWidget(self.dbinuse)

        # now assemble the event handlers
        self.searchGo.clicked.connect(self.do_search)
        self.searchBox.returnPressed.connect(self.searchGo.click)

        self.results_list.activated.connect(self.load_file)
        # activated covers doubleClicked
        # self.results_list.doubleClicked.connect(self.load_file)

    def do_search(self):
        # sanitise the search text
        # print 'start search'
        self.results_list.clear()
        x = QtGui.QListWidgetItem('searching.... one moment')
        self.results_list.addItem(x)
        self.results_list.update()
        self.results_list.repaint()

        searchTerm = self.searchBox.text().lstrip().rstrip()
        # this part is confusion: find dash or underscore and replace it with
        # the reg-ex of it
        searchTerm = re.sub("[-_]", "[-_]", searchTerm)
        hDict = {}
        if os.path.exists(pPath):
            fp = open(pPath, 'rb')
            hDict = pickle.load(fp)
            fp.close()

        self.results_list.clear()
        for full in hDict.keys():
            fName = ".".join(os.path.split(full)[1].split(".")[:-2])
            if re.search(searchTerm, full, re.IGNORECASE) and fName:
                #self.results[fName] = [full]+hDict[full]
                # print "hit:",
                # print fName
                # print full
                x = QtGui.QListWidgetItem()

                x.setData(0, fName)
                x.setData(33, full)
                x.setData(34, hDict[full][0])
                x.setData(35, hDict[full][1])
                x.setText(
                    fName + '  [ {start}-{end} ]'.format(start=hDict[full][0], end=hDict[full][1]))
                self.results_list.addItem(x)

        self.results_list.sortItems()
        self.last_action.setText('Searched for ' + searchTerm)


def standalone():
    x = SlateLookupWindow()
    x.show()
    return x

# panels.registerWidgetAsPanel('SlateLookupWindow', 'Slate Lookup', 'com.flamingwidget.furyfx.slatelookupwindow')
# x = SlateLookupWindow()
# x.show()
