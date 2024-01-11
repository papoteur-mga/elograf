/********************************************************************************
** Form generated from reading UI file 'advanced.ui'
**
** Created by: Qt User Interface Compiler version 6.4.1
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef ADVANCED_H
#define ADVANCED_H

#include <QtCore/QVariant>
#include <QtWidgets/QAbstractButton>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDialog>
#include <QtWidgets/QDialogButtonBox>
#include <QtWidgets/QGridLayout>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QSlider>

QT_BEGIN_NAMESPACE

class Ui_Dialog
{
public:
    QGridLayout *gridLayout_2;
    QGridLayout *gridLayout;
    QLineEdit *precommand;
    QComboBox *tool_cb;
    QComboBox *deviceName;
    QLabel *label_8;
    QLabel *label_2;
    QHBoxLayout *horizontalLayout_2;
    QSlider *timeout;
    QLabel *timeoutDisplay;
    QLineEdit *env;
    QHBoxLayout *horizontalLayout;
    QSlider *idleTime;
    QLabel *idleDisplay;
    QLabel *label_6;
    QLabel *label_5;
    QLabel *label_9;
    QLineEdit *sampleRate;
    QCheckBox *digits;
    QCheckBox *useSeparator;
    QLabel *label_13;
    QLabel *label_7;
    QLineEdit *freecommand;
    QLineEdit *postcommand;
    QLabel *label_3;
    QLabel *label_12;
    QCheckBox *fullSentence;
    QLabel *label_11;
    QLabel *label_10;
    QLabel *label;
    QDialogButtonBox *buttonBox;
    QLabel *label_4;
    QHBoxLayout *horizontalLayout_3;
    QSlider *punctuate;
    QLabel *punctuateDisplay;
    QLabel *label_14;
    QLineEdit *keyboard_le;

    void setupUi(QDialog *Dialog)
    {
        if (Dialog->objectName().isEmpty())
            Dialog->setObjectName("Dialog");
        Dialog->resize(659, 372);
        QSizePolicy sizePolicy(QSizePolicy::Preferred, QSizePolicy::Preferred);
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(Dialog->sizePolicy().hasHeightForWidth());
        Dialog->setSizePolicy(sizePolicy);
        gridLayout_2 = new QGridLayout(Dialog);
        gridLayout_2->setObjectName("gridLayout_2");
        gridLayout = new QGridLayout();
        gridLayout->setObjectName("gridLayout");
        precommand = new QLineEdit(Dialog);
        precommand->setObjectName("precommand");

        gridLayout->addWidget(precommand, 0, 1, 1, 1);

        tool_cb = new QComboBox(Dialog);
        tool_cb->addItem(QString());
        tool_cb->addItem(QString());
        tool_cb->setObjectName("tool_cb");

        gridLayout->addWidget(tool_cb, 12, 1, 1, 1);

        deviceName = new QComboBox(Dialog);
        deviceName->setObjectName("deviceName");

        gridLayout->addWidget(deviceName, 3, 1, 1, 1);

        label_8 = new QLabel(Dialog);
        label_8->setObjectName("label_8");

        gridLayout->addWidget(label_8, 9, 0, 1, 1);

        label_2 = new QLabel(Dialog);
        label_2->setObjectName("label_2");

        gridLayout->addWidget(label_2, 4, 0, 1, 1);

        horizontalLayout_2 = new QHBoxLayout();
        horizontalLayout_2->setObjectName("horizontalLayout_2");
        timeout = new QSlider(Dialog);
        timeout->setObjectName("timeout");
        timeout->setOrientation(Qt::Horizontal);

        horizontalLayout_2->addWidget(timeout);

        timeoutDisplay = new QLabel(Dialog);
        timeoutDisplay->setObjectName("timeoutDisplay");
#if QT_CONFIG(accessibility)
        timeoutDisplay->setAccessibleName(QString::fromUtf8(""));
#endif // QT_CONFIG(accessibility)

        horizontalLayout_2->addWidget(timeoutDisplay);


        gridLayout->addLayout(horizontalLayout_2, 5, 1, 1, 1);

        env = new QLineEdit(Dialog);
        env->setObjectName("env");

        gridLayout->addWidget(env, 2, 1, 1, 1);

        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setObjectName("horizontalLayout");
        idleTime = new QSlider(Dialog);
        idleTime->setObjectName("idleTime");
        idleTime->setMaximum(500);
        idleTime->setValue(100);
        idleTime->setOrientation(Qt::Horizontal);

        horizontalLayout->addWidget(idleTime);

        idleDisplay = new QLabel(Dialog);
        idleDisplay->setObjectName("idleDisplay");
#if QT_CONFIG(accessibility)
        idleDisplay->setAccessibleName(QString::fromUtf8(""));
#endif // QT_CONFIG(accessibility)

        horizontalLayout->addWidget(idleDisplay);


        gridLayout->addLayout(horizontalLayout, 6, 1, 1, 1);

        label_6 = new QLabel(Dialog);
        label_6->setObjectName("label_6");

        gridLayout->addWidget(label_6, 7, 0, 1, 1);

        label_5 = new QLabel(Dialog);
        label_5->setObjectName("label_5");

        gridLayout->addWidget(label_5, 6, 0, 1, 1);

        label_9 = new QLabel(Dialog);
        label_9->setObjectName("label_9");

        gridLayout->addWidget(label_9, 10, 0, 1, 1);

        sampleRate = new QLineEdit(Dialog);
        sampleRate->setObjectName("sampleRate");

        gridLayout->addWidget(sampleRate, 4, 1, 1, 1);

        digits = new QCheckBox(Dialog);
        digits->setObjectName("digits");

        gridLayout->addWidget(digits, 9, 1, 1, 1);

        useSeparator = new QCheckBox(Dialog);
        useSeparator->setObjectName("useSeparator");

        gridLayout->addWidget(useSeparator, 10, 1, 1, 1);

        label_13 = new QLabel(Dialog);
        label_13->setObjectName("label_13");

        gridLayout->addWidget(label_13, 12, 0, 1, 1);

        label_7 = new QLabel(Dialog);
        label_7->setObjectName("label_7");

        gridLayout->addWidget(label_7, 8, 0, 1, 1);

        freecommand = new QLineEdit(Dialog);
        freecommand->setObjectName("freecommand");

        gridLayout->addWidget(freecommand, 11, 1, 1, 1);

        postcommand = new QLineEdit(Dialog);
        postcommand->setObjectName("postcommand");

        gridLayout->addWidget(postcommand, 1, 1, 1, 1);

        label_3 = new QLabel(Dialog);
        label_3->setObjectName("label_3");

        gridLayout->addWidget(label_3, 11, 0, 1, 1);

        label_12 = new QLabel(Dialog);
        label_12->setObjectName("label_12");

        gridLayout->addWidget(label_12, 2, 0, 1, 1);

        fullSentence = new QCheckBox(Dialog);
        fullSentence->setObjectName("fullSentence");

        gridLayout->addWidget(fullSentence, 8, 1, 1, 1);

        label_11 = new QLabel(Dialog);
        label_11->setObjectName("label_11");

        gridLayout->addWidget(label_11, 1, 0, 1, 1);

        label_10 = new QLabel(Dialog);
        label_10->setObjectName("label_10");

        gridLayout->addWidget(label_10, 0, 0, 1, 1);

        label = new QLabel(Dialog);
        label->setObjectName("label");

        gridLayout->addWidget(label, 3, 0, 1, 1);

        buttonBox = new QDialogButtonBox(Dialog);
        buttonBox->setObjectName("buttonBox");
        buttonBox->setOrientation(Qt::Horizontal);
        buttonBox->setStandardButtons(QDialogButtonBox::Cancel|QDialogButtonBox::Ok);

        gridLayout->addWidget(buttonBox, 14, 1, 1, 1);

        label_4 = new QLabel(Dialog);
        label_4->setObjectName("label_4");

        gridLayout->addWidget(label_4, 5, 0, 1, 1);

        horizontalLayout_3 = new QHBoxLayout();
        horizontalLayout_3->setObjectName("horizontalLayout_3");
        punctuate = new QSlider(Dialog);
        punctuate->setObjectName("punctuate");
        punctuate->setOrientation(Qt::Horizontal);

        horizontalLayout_3->addWidget(punctuate);

        punctuateDisplay = new QLabel(Dialog);
        punctuateDisplay->setObjectName("punctuateDisplay");
#if QT_CONFIG(accessibility)
        punctuateDisplay->setAccessibleName(QString::fromUtf8(""));
#endif // QT_CONFIG(accessibility)

        horizontalLayout_3->addWidget(punctuateDisplay);


        gridLayout->addLayout(horizontalLayout_3, 7, 1, 1, 1);

        label_14 = new QLabel(Dialog);
        label_14->setObjectName("label_14");

        gridLayout->addWidget(label_14, 13, 0, 1, 1);

        keyboard_le = new QLineEdit(Dialog);
        keyboard_le->setObjectName("keyboard_le");

        gridLayout->addWidget(keyboard_le, 13, 1, 1, 1);

        gridLayout->setColumnStretch(1, 2);

        gridLayout_2->addLayout(gridLayout, 0, 0, 1, 1);


        retranslateUi(Dialog);
        QObject::connect(buttonBox, &QDialogButtonBox::accepted, Dialog, qOverload<>(&QDialog::accept));
        QObject::connect(buttonBox, &QDialogButtonBox::rejected, Dialog, qOverload<>(&QDialog::reject));

        QMetaObject::connectSlotsByName(Dialog);
    } // setupUi

    void retranslateUi(QDialog *Dialog)
    {
        Dialog->setWindowTitle(QCoreApplication::translate("Dialog", "Advanced parameters", nullptr));
        tool_cb->setItemText(0, QCoreApplication::translate("Dialog", "XDOTOOL", nullptr));
        tool_cb->setItemText(1, QCoreApplication::translate("Dialog", "DOTOOL", nullptr));

        tool_cb->setCurrentText(QCoreApplication::translate("Dialog", "XDOTOOL", nullptr));
        deviceName->setCurrentText(QString());
#if QT_CONFIG(tooltip)
        label_8->setToolTip(QCoreApplication::translate("Dialog", "Convert numbers into digits instead of using whole words", nullptr));
#endif // QT_CONFIG(tooltip)
        label_8->setText(QCoreApplication::translate("Dialog", "Numbers as digits", nullptr));
#if QT_CONFIG(tooltip)
        label_2->setToolTip(QCoreApplication::translate("Dialog", "The sample rate to use for recording (in Hz). Defaults to 44100", nullptr));
#endif // QT_CONFIG(tooltip)
        label_2->setText(QCoreApplication::translate("Dialog", "Sample rate (Hz)", nullptr));
        timeoutDisplay->setText(QCoreApplication::translate("Dialog", "TextLabel", nullptr));
        idleDisplay->setText(QCoreApplication::translate("Dialog", "TextLabel", nullptr));
#if QT_CONFIG(tooltip)
        label_6->setToolTip(QCoreApplication::translate("Dialog", "The time-out in seconds for detecting the state of dictation from the previous recording,\n"
"this can be useful so punctuation it is added before entering the dictation (zero disables)", nullptr));
#endif // QT_CONFIG(tooltip)
        label_6->setText(QCoreApplication::translate("Dialog", "Punctuate from previous timeout (s)", nullptr));
#if QT_CONFIG(tooltip)
        label_5->setToolTip(QCoreApplication::translate("Dialog", "Time to idle between processing audio from the recording.\n"
"Setting to zero is the most responsive at the cost of high CPU usage.\n"
"The default value is 0.1 (processing 10 times a second),\n"
"which is quite responsive in practice", nullptr));
#endif // QT_CONFIG(tooltip)
        label_5->setText(QCoreApplication::translate("Dialog", "Idle time (ms)", nullptr));
#if QT_CONFIG(tooltip)
        label_9->setToolTip(QCoreApplication::translate("Dialog", "Use a comma separators for numbers", nullptr));
#endif // QT_CONFIG(tooltip)
        label_9->setText(QCoreApplication::translate("Dialog", "Use separator for numbers", nullptr));
        digits->setText(QString());
        useSeparator->setText(QString());
        label_13->setText(QCoreApplication::translate("Dialog", "Input simulate tool", nullptr));
#if QT_CONFIG(tooltip)
        label_7->setToolTip(QCoreApplication::translate("Dialog", "Capitalize the first character.\n"
"This is also used to add either a comma or a full stop when dictation is performed according to previous delay", nullptr));
#endif // QT_CONFIG(tooltip)
        label_7->setText(QCoreApplication::translate("Dialog", "Full sentence", nullptr));
#if QT_CONFIG(tooltip)
        label_3->setToolTip(QCoreApplication::translate("Dialog", "Add option to add on the comamnd line of the dictation tool", nullptr));
#endif // QT_CONFIG(tooltip)
        label_3->setText(QCoreApplication::translate("Dialog", "Free option", nullptr));
        label_12->setText(QCoreApplication::translate("Dialog", "Environment variables", nullptr));
        fullSentence->setText(QString());
#if QT_CONFIG(tooltip)
        label_11->setToolTip(QCoreApplication::translate("Dialog", "Command to execute after the dictation is stopped", nullptr));
#endif // QT_CONFIG(tooltip)
        label_11->setText(QCoreApplication::translate("Dialog", "Postcommand", nullptr));
#if QT_CONFIG(tooltip)
        label_10->setToolTip(QCoreApplication::translate("Dialog", "Command to execute before launching the dictation", nullptr));
#endif // QT_CONFIG(tooltip)
        label_10->setText(QCoreApplication::translate("Dialog", "Precommand", nullptr));
#if QT_CONFIG(tooltip)
        label->setToolTip(QCoreApplication::translate("Dialog", "The name of the pulse-audio device to use for recording. \n"
"See the output of \"pactl list sources\" to find device names (using the identifier following \"Name:\")", nullptr));
#endif // QT_CONFIG(tooltip)
        label->setText(QCoreApplication::translate("Dialog", "Pulse device name", nullptr));
#if QT_CONFIG(tooltip)
        label_4->setToolTip(QCoreApplication::translate("Dialog", "Time out recording when no speech is processed for the time in seconds.\n"
"This can be used to avoid having to explicitly exit\n"
"(zero disables)", nullptr));
#endif // QT_CONFIG(tooltip)
        label_4->setText(QCoreApplication::translate("Dialog", "Timeout (s)", nullptr));
        punctuateDisplay->setText(QCoreApplication::translate("Dialog", "TextLabel", nullptr));
        label_14->setText(QCoreApplication::translate("Dialog", "Keyboard layout", nullptr));
#if QT_CONFIG(tooltip)
        keyboard_le->setToolTip(QCoreApplication::translate("Dialog", "<html><head/><body><p>This is used for DOTOOL method</p></body></html>", nullptr));
#endif // QT_CONFIG(tooltip)
    } // retranslateUi

};

namespace Ui {
    class Dialog: public Ui_Dialog {};
} // namespace Ui

QT_END_NAMESPACE

#endif // ADVANCED_H
