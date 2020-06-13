import os
import random
import sys
import webbrowser

import numpy as np

try:
    from PyQt5.QtCore import QStringListModel, QUrl, QSize, QAbstractItemModel, QAbstractListModel, QObject, pyqtProperty, \
    pyqtSignal, pyqtSlot, QTimer
    from PyQt5.QtGui import QFont, QColor
    from PyQt5.QtQuickWidgets import QQuickWidget
    from PyQt5.QtWidgets import QMainWindow, QApplication
except ImportError:
    print('PyQt5 is not installed. Qt VBI Viewer not available.')

from teletext.gui.qthelpers import build_menu
from teletext.parser import Parser


class Palette(object):

    def __init__(self, context):
        self._context = context
        self._palette = [
            QColor(0, 0, 0),
            QColor(255, 0, 0),
            QColor(0, 255, 0),
            QColor(255, 255, 0),
            QColor(0, 0, 255),
            QColor(255, 0, 255),
            QColor(0, 255, 255),
            QColor(255, 255, 255),
        ]
        self._context.setContextProperty('ttpalette', self._palette)

    def __getitem__(self, item):
        return (self._palette[item].red(), self._palette[item].green(), self._palette[item].blue())

    def __setitem__(self, item, value):
        self._palette[item].setRed(value[0])
        self._palette[item].setGreen(value[1])
        self._palette[item].setBlue(value[2])
        self._context.setContextProperty('ttpalette', self._palette)


class ParserQML(Parser):

    def __init__(self, tt, row, cells):
        self._row = row
        self._cells = cells
        super().__init__(tt)

    def emitcharacter(self, c):
        self._cells[self._cell].setProperty('c', c)
        self._cells[self._cell].setProperty('fg', 4)
        for state, value in self._state.items():
            self._cells[self._cell].setProperty(state, value)
        if self._cell > 1:
            self._cells[self._cell].setProperty('visible', not self._cells[self._cell-1].property('dw'))
        self._cell += 1

    def parse(self):
        self._cell = 0
        super().parse()


class Decoder(QQuickWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setResizeMode(QQuickWidget.SizeViewToRootObject)

        self._fonts = [
            [
                [self.make_font(100), self.make_font(50)],
                [self.make_font(200), self.make_font(100)]
            ],
            [
                [self.make_font(120), self.make_font(60)],
                [self.make_font(240), self.make_font(120)]
            ]
        ]

        self.rootContext().setContextProperty('ttfonts', self._fonts)
        self._palette = Palette(self.rootContext())

        qml_file = os.path.join(os.path.dirname(__file__), 'decoder.qml')
        self.setSource(QUrl.fromLocalFile(qml_file))

        self._rows = [self.rootObject().findChild(QObject, 'teletext').findChild(QObject, 'rows').itemAt(x) for x in range(25)]
        self._cells = [[r.findChild(QObject, 'cols').itemAt(x) for x in range(40)] for r in self._rows]
        self._data = np.zeros((25, 40), dtype=np.uint8)
        self._parsers = [ParserQML(self._data[x], self._rows[x], self._cells[x]) for x in range(25)]

        self.zoom = 2

    def __setitem__(self, item, value):
        self._data[item] = value
        if isinstance(item, tuple):
            item = item[0]
        if isinstance(item, int):
            self._parsers[item].parse()
        else:
            for p in self._parsers[item]:
                p.parse()

    def __getitem__(self, item):
        return self._data[item]

    def randomize(self):
        self[1:] = np.random.randint(0, 256, size=(24, 40), dtype=np.uint8)

    def make_font(self, stretch):
        font = QFont('teletext2')
        font.setStyleStrategy(QFont.NoSubpixelAntialias)
        font.setHintingPreference(QFont.PreferNoHinting)
        font.setStretch(stretch)
        return font

    @property
    def palette(self):
        return self._palette

    @property
    def zoom(self):
        return self.rootObject().property('zoom')

    @zoom.setter
    def zoom(self, zoom):
        self._fonts[0][0][0].setPixelSize(zoom * 10)
        self._fonts[0][0][1].setPixelSize(zoom * 20)
        self._fonts[0][1][0].setPixelSize(zoom * 10)
        self._fonts[0][1][1].setPixelSize(zoom * 20)
        self._fonts[1][0][0].setPixelSize(zoom * 10)
        self._fonts[1][0][1].setPixelSize(zoom * 20)
        self._fonts[1][1][0].setPixelSize(zoom * 10)
        self._fonts[1][1][1].setPixelSize(zoom * 20)
        self.rootContext().setContextProperty('ttfonts', self._fonts)
        self.rootObject().setProperty('zoom', zoom)
        self.setFixedSize(self.sizeHint())

    @property
    def crteffect(self):
        return self.rootObject().property('crteffect')

    @crteffect.setter
    def crteffect(self, crteffect):
        self.rootObject().setProperty('crteffect', crteffect)

    def sizeHint(self):
        sf = self.rootObject().size()
        return QSize(int(sf.width()), int(sf.height()))

    def setEffect(self, e):
        self._effect = bool(e)
        self.rootContext().setContextProperty('tteffect', self._effect)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Teletext Viewer')

        self._tt = Decoder()

        build_menu(self, self.menuBar(), [
            ('&File', [], None),
            ('&Edit', [
                ('Randomize', lambda x: self._tt.randomize(), 'Ctrl+r'),
            ], None),
            ('&View', [
                ('1x', lambda x: self.setZoom(1), 'Ctrl+1'),
                ('2x', lambda x: self.setZoom(2), 'Ctrl+2'),
                ('3x', lambda x: self.setZoom(3), 'Ctrl+3'),
                ('4x', lambda x: self.setZoom(4), 'Ctrl+4'),
                ('CRT simulation', lambda x: setattr(self._tt, 'crteffect', True), None),
                ('Regular', lambda x: setattr(self._tt, 'crteffect', False), None),
            ], None),
            ('&Settings', [], None),
            ('&Help', [
                ('&Website', lambda x: webbrowser.open_new_tab('https://github.com/ali1234/vhs-teletext'), None),
                ('&About', None, None),
            ], None),
        ])

        #self.statusBar().showMessage('Ready')

        self.setCentralWidget(self._tt)
        self.show()

    def setZoom(self, zoom):
        self._tt.zoom = zoom
        self.setFixedSize(QSize(self.centralWidget().width(), self.centralWidget().height() + self.menuWidget().height()))

    def quit(self, checked):
        self.close()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()