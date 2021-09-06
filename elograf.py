#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 08:15:47 2021

@author: papoteur
@license: GPL v3.0
"""

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from subprocess import Popen
import os
import elograf_rc
MODEL_BASE_PATH = '/usr/share/vosk-model'

class ConfigPopup (QtWidgets.QDialog):
    def __init__(self, currentModel, precommand, parent=None):
        super(ConfigPopup, self).__init__(parent)
        self.setWindowTitle("Elograf")
        self.setWindowIcon(QtGui.QIcon(":/icons/elograf/24/micro.png"))
        layout = QtWidgets.QVBoxLayout(self)
        dirList = [name for name in os.listdir(MODEL_BASE_PATH) if not os.path.isfile(name)]
        numberModels = len(dirList)
        self.table = QtWidgets.QTableWidget(numberModels, 5, self)
        precommandlayout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(precommandlayout)
        label = QtWidgets.QLabel("Precommand:")
        self.precommand = QtWidgets.QLineEdit()
        precommandlayout.addWidget(label)
        precommandlayout.addWidget(self.precommand)
        self.precommand.setText(precommand)
        layout.addWidget(self.table)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setHorizontalHeaderLabels(["Language", "Name","Description", "Size","License"])
        i = 0
        selectedLine = None
        for dirModel in dirList:
            descriptionPath = os.path.join(MODEL_BASE_PATH, dirModel, "description.txt")
            if os.path.isfile(descriptionPath):
                name, language, description, size, license = self.readDesc(descriptionPath)
            else:
                name = dirModel
                language = "Not provided"
                description = "Not provided"
                size = "Not provided"
                license = "Not provided"
            item = QtWidgets.QTableWidgetItem(language)
            self.table.setItem(i, 0,item)
            item = QtWidgets.QTableWidgetItem(name)
            self.table.setItem(i, 1,item)
            item = QtWidgets.QTableWidgetItem(description)
            self.table.setItem(i, 2,item)
            item = QtWidgets.QTableWidgetItem(size)
            self.table.setItem(i, 3,item)
            item = QtWidgets.QTableWidgetItem(license)
            self.table.setItem(i, 4,item)
            if currentModel == name:
                selectedLine = i
                self.table.setCurrentItem(item)
            i += 1
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.close)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.resizeColumnsToContents()
        self.table.verticalHeader().hide()
        self.resize(self.table.horizontalHeader().length() + 24,
                    self.precommand.sizeHint().height() +
                    self.table.verticalHeader().length() +
                    self.table.horizontalHeader().sizeHint().height() +
                    buttonBox.sizeHint().height()  + 40)
        self.returnValue = None

    def readDesc(self, path):
        with open(path,'r') as f:
             name = f.readline().rstrip()
             language =  f.readline().rstrip()
             description = f.readline().rstrip()
             size = f.readline().rstrip()
             license = f.readline().rstrip()
             return name, language, description, size, license

    def accept(self):
        i = 0
        for item in self.table.selectedItems():
            if item.text() and i == 1:
                self.returnValue = [item.text(), self.precommand.text()]
            i += 1
        self.close()

    def cancel(self):
        self.close()

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
       QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
       menu = QtWidgets.QMenu(parent)
       exitAction = menu.addAction("Exit")
       configAction = menu.addAction("Configuration")
       self.setContextMenu(menu)
       exitAction.triggered.connect(self.exit)
       configAction.triggered.connect(self.config)
       self.nomicro = QtGui.QIcon(":/icons/elograf/24/nomicro.png")
       self.micro = QtGui.QIcon(":/icons/elograf/24/micro.png")
       self.activated.connect(self.commute)
       self.dictating = False

       self.settings = QtCore.QSettings("Elograf","Elograf")
       if self.settings.contains("Model/name"):
            self.currentModel = self.settings.value("Model/name")
       else:
           self.currentModel = None

    def exit(self):
        self.stop_dictate()
        QtCore.QCoreApplication.exit()

    def dictate(self):
        while not self.currentModel :
            dialog = ConfigPopup("", self.settings.value("Precommand"))
            dialog.exec_()
            if dialog.returnValue:
                self.currentModel = dialog.returnValue[0]
                precommand = dialog.returnValue[1]
                if precommand == "":
                    self.settings.remove("Precommand")
                else:
                    self.settings.setValue("Precommand", precommand)
        if self.settings.contains("Precommand"):
            Popen(self.settings.value("Precommand").split())

        Popen(['nerd-dictation',
                        'begin',
                       f"--vosk-model-dir={os.path.join(MODEL_BASE_PATH, self.currentModel)}",
                        '--full-sentence',
                        '--punctuate-from-previous-timeout=10'])
        self.setIcon(self.micro)

    def stop_dictate(self):
        Popen(['nerd-dictation','end',])
        self.setIcon(self.nomicro)

    def commute(self):
        if self.dictating:
            self.stop_dictate()
        else:
            self.dictate()
        self.dictating = not self.dictating

    def config(self):
        dialog = ConfigPopup(self.currentModel, self.settings.value("Precommand"))
        dialog.exec_()
        if dialog.returnValue:
            self.setModel(dialog.returnValue[0])
            precommand = dialog.returnValue[1]
            if precommand == "":
                self.settings.remove("Precommand")
            else:
                self.settings.setValue("Precommand", precommand)

    def setModel(self, model):
        self.currentModel = model
        self.settings.setValue("Model/name", model)
        if self.dictating:
            self.stop_dictate()
            self.dictate()

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    w = QtWidgets.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon(":/icons/elograf/24/nomicro.png"), w)

    trayIcon.show()
    exit(app.exec_())

if __name__ == '__main__':
    main()
