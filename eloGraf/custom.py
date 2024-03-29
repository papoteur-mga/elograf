# Form implementation generated from reading ui file 'custom.ui'
#
# Created by: PyQt6 UI code generator 6.4.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(612, 277)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../icons/elograf/scalable/micro.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        Dialog.setWindowIcon(icon)
        self.verticalLayoutWidget = QtWidgets.QWidget(parent=Dialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 611, 271))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.pathLabel = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.pathLabel.setObjectName("pathLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.pathLabel)
        self.filePicker = QtWidgets.QPushButton(parent=self.verticalLayoutWidget)
        self.filePicker.setObjectName("filePicker")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.filePicker)
        self.nameLabel = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.nameLabel.setObjectName("nameLabel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.nameLabel)
        self.nameLineEdit = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.nameLineEdit)
        self.classLabel = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.classLabel.setObjectName("classLabel")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.classLabel)
        self.classLineEdit = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.classLineEdit.setObjectName("classLineEdit")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.classLineEdit)
        self.versionLabel = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.versionLabel.setObjectName("versionLabel")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.versionLabel)
        self.versionLineEdit = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.versionLineEdit.setObjectName("versionLineEdit")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.versionLineEdit)
        self.sizeLabel = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.sizeLabel.setObjectName("sizeLabel")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.sizeLabel)
        self.sizeLineEdit = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.sizeLineEdit.setEnabled(True)
        self.sizeLineEdit.setInputMask("")
        self.sizeLineEdit.setText("")
        self.sizeLineEdit.setReadOnly(True)
        self.sizeLineEdit.setObjectName("sizeLineEdit")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.sizeLineEdit)
        self.languageLabel = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.languageLabel.setObjectName("languageLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.languageLabel)
        self.languageLineEdit = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.languageLineEdit.setObjectName("languageLineEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.languageLineEdit)
        self.verticalLayout.addLayout(self.formLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=self.verticalLayoutWidget)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Select a custom model"))
        self.label.setText(_translate("Dialog", "<html><head/><body><p><span style=\" font-weight:600;\">Select a custom model</span></p></body></html>"))
        self.pathLabel.setText(_translate("Dialog", "Path"))
        self.filePicker.setText(_translate("Dialog", "Select the path of your model"))
        self.nameLabel.setToolTip(_translate("Dialog", "<html><head/><body><p>Give a name to your model</p></body></html>"))
        self.nameLabel.setText(_translate("Dialog", "Name"))
        self.classLabel.setToolTip(_translate("Dialog", "<html><head/><body><p>Indicate a class to your model like small, medium or big</p></body></html>"))
        self.classLabel.setText(_translate("Dialog", "Class"))
        self.versionLabel.setToolTip(_translate("Dialog", "<html><head/><body><p>Give a version number to your model</p></body></html>"))
        self.versionLabel.setText(_translate("Dialog", "Version"))
        self.sizeLabel.setText(_translate("Dialog", "Size"))
        self.languageLabel.setText(_translate("Dialog", "Language"))
