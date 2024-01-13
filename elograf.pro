#-------------------------------------------------
#
# Project created by QtCreator 2014-12-07T13:03:24
#
#-------------------------------------------------

QT       += core gui widgets

greaterThan(QT_MAJOR_VERSION, 5): 

TARGET = elograf
TEMPLATE = app


SOURCES += eloGraf/elograf.py \
            eloGraf/elograf_rc.py\
            eloGraf/languages.py

HEADERS  +=

FORMS    +=  \
    eloGraf/confirm.ui \
    eloGraf/advanced.ui \
    eloGraf/custom.ui

TRANSLATIONS     += eloGraf/translations/elograf_fr.ts
TRANSLATIONS     += eloGraf/translations/elograf_nb.ts
TRANSLATIONS     += eloGraf/translations/elograf_uk.ts

OTHER_FILES += 
