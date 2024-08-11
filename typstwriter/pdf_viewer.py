# This file is in part derived from the Qt for Python PDF Viewer Example
# (see https://doc.qt.io/qtforpython-6/examples/example_pdfwidgets_pdfviewer.html)
# Original Copyright (C) 2022 The Qt Company Ltd., originally licensed under BSD-3-Clause

from qtpy import QtPdf
from qtpy import QtPdfWidgets
from qtpy import QtWidgets
from qtpy import QtCore
from qtpy import QtGui

import os
from time import time

from typstwriter import util

from typstwriter import logging
from typstwriter import configuration
from typstwriter import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class ZoomSelector(QtWidgets.QComboBox):
    """ComboBox for zoom to numerical values or height/width fit."""

    zoom_mode_changed = QtCore.Signal(QtPdfWidgets.QPdfView.ZoomMode)
    zoom_factor_changed = QtCore.Signal(float)

    def __init__(self, parent):
        """Init and set zoom levels."""
        super().__init__(parent)
        self.setEditable(True)

        self.addItem("Fit Page Width")
        self.addItem("Fit Page Height")
        self.insertSeparator(2)
        self.addItem("12%")
        self.addItem("25%")
        self.addItem("33%")
        self.addItem("50%")
        self.addItem("66%")
        self.addItem("75%")
        self.addItem("100%")
        self.addItem("125%")
        self.addItem("150%")
        self.addItem("200%")
        self.addItem("400%")

        self.currentTextChanged.connect(self.on_current_text_changed)
        self.lineEdit().editingFinished.connect(self._editing_finished)

    @QtCore.Slot(float)
    def set_zoom_factor(self, zoom_factor):
        """Set Zoom."""
        percent = int(zoom_factor * 100)
        self.setCurrentText(f"{percent}%")

    @QtCore.Slot()
    def reset(self):
        """Reset Zoom."""
        self.setCurrentText("100%")

    @QtCore.Slot(str)
    def on_current_text_changed(self, text):
        """Handle change in ComboBox and set Zoom."""
        if text == "Fit Page Width":
            self.zoom_mode_changed.emit(QtPdfWidgets.QPdfView.ZoomMode.FitToWidth)
        elif text == "Fit Page Height":
            self.zoom_mode_changed.emit(QtPdfWidgets.QPdfView.ZoomMode.FitInView)
        elif text.endswith("%"):
            factor = 1.0
            zoom_level = int(text[:-1])
            factor = zoom_level / 100.0
            self.zoom_mode_changed.emit(QtPdfWidgets.QPdfView.ZoomMode.Custom)
            self.zoom_factor_changed.emit(factor)

    @QtCore.Slot()
    def _editing_finished(self):
        """Relay zoom level to on_current_text_changed."""
        self.on_current_text_changed(self.lineEdit().text())


class PDFViewer(QtWidgets.QFrame):
    """A PDF Viewer."""

    def __init__(self):
        """Populate the PDF Viewer and create document store."""
        QtWidgets.QFrame.__init__(self)
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)

        # Action Zoom In
        self.actionZoom_In = QtGui.QAction(self)
        self.actionZoom_In.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ZoomIn, QtGui.QIcon(util.icon_path("plus.svg"))))
        self.actionZoom_In.setText("Zoom In")
        self.actionZoom_In.setShortcut(QtGui.QKeySequence.ZoomIn)

        # Action Zoom Out
        self.actionZoom_Out = QtGui.QAction(self)
        self.actionZoom_Out.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ZoomOut, QtGui.QIcon(util.icon_path("minus.svg"))))
        self.actionZoom_Out.setText("Zoom Out")
        self.actionZoom_Out.setShortcut(QtGui.QKeySequence.ZoomOut)

        # Action Previous Page
        self.actionPrevious_Page = QtGui.QAction(self)
        self.actionPrevious_Page.setIcon(
            QtGui.QIcon.fromTheme(QtGui.QIcon.GoPrevious, QtGui.QIcon(util.icon_path("larrow.svg")))
        )
        self.actionPrevious_Page.setText("Previous Page")

        # Action Next Page
        self.actionNext_Page = QtGui.QAction(self)
        self.actionNext_Page.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.GoNext, QtGui.QIcon(util.icon_path("rarrow.svg"))))
        self.actionNext_Page.setText("Next Page")
        self.actionPrevious_Page.setShortcut("PgUp")

        # Action External Viewer
        self.actionOpen_External = QtGui.QAction(self)
        self.actionOpen_External.setIcon(QtGui.QIcon.fromTheme("viewpdf", QtGui.QIcon(util.icon_path("pdf.svg"))))
        self.actionOpen_External.setText("External Viewer")
        self.actionNext_Page.setShortcut("PgDown")

        # Layout
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.verticalLayout.addWidget(self.toolbar)

        # PDF view
        self.pdfView = QtPdfWidgets.QPdfView(self)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(10)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.pdfView.sizePolicy().hasHeightForWidth())
        self.pdfView.setSizePolicy(size_policy)
        self.verticalLayout.addWidget(self.pdfView)

        # Connect Signals and Slots
        self.actionZoom_In.triggered.connect(self.zoom_in_triggered)
        self.actionZoom_Out.triggered.connect(self.zoom_out_triggered)
        self.actionPrevious_Page.triggered.connect(self.previous_page_triggered)
        self.actionNext_Page.triggered.connect(self.next_page_triggered)
        self.actionOpen_External.triggered.connect(self.open_in_external_viewer)

        self.m_zoomSelector = ZoomSelector(self)
        self.m_pageSelector = QtWidgets.QSpinBox(self)
        self.m_maxPage = QtWidgets.QLabel(self)
        self.m_document = QtPdf.QPdfDocument(self)

        self.m_zoomSelector.setMaximumWidth(150)

        self.toolbarspacer1 = QtWidgets.QWidget()
        self.toolbarspacer1.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.toolbarspacer2 = QtWidgets.QWidget()
        self.toolbarspacer2.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        # Populate toolbar
        self.toolbar.addAction(self.actionZoom_Out)
        self.toolbar.addWidget(self.m_zoomSelector)
        self.toolbar.addAction(self.actionZoom_In)
        self.toolbar.addWidget(self.toolbarspacer1)
        self.toolbar.addAction(self.actionPrevious_Page)
        self.toolbar.addWidget(self.m_pageSelector)
        self.toolbar.addWidget(self.m_maxPage)
        self.toolbar.addAction(self.actionNext_Page)
        self.toolbar.addWidget(self.toolbarspacer2)
        self.toolbar.addAction(self.actionOpen_External)

        self.m_pageSelector.valueChanged.connect(lambda n: self.page_selected(n - 1))
        nav = self.pdfView.pageNavigator()
        nav.currentPageChanged.connect(lambda n: self.m_pageSelector.setValue(n + 1))
        self.m_pageSelector.setMinimum(1)
        # nav.backAvailableChanged.connect(self.actionBack.setEnabled)
        # nav.forwardAvailableChanged.connect(self.actionForward.setEnabled)

        self.m_maxPage.setText(f" of {self.m_document.pageCount()}")

        self.m_zoomSelector.zoom_mode_changed.connect(self.pdfView.setZoomMode)
        self.m_zoomSelector.zoom_factor_changed.connect(self.pdfView.setZoomFactor)
        self.m_zoomSelector.reset()

        self.pdfView.setDocument(self.m_document)
        self.pdfView.zoomFactorChanged.connect(self.m_zoomSelector.set_zoom_factor)
        self.pdfView.setPageMode(QtPdfWidgets.QPdfView.PageMode.MultiPage)

        self.docpath = None

    @QtCore.Slot(QtCore.QUrl)
    def open(self, path):
        """Open and display a file."""
        self.docpath = path
        if os.path.exists(path):
            self.m_document.load(path)
            self.page_selected(0)
            self.m_pageSelector.setMaximum(self.m_document.pageCount())
            self.m_maxPage.setText(f" of {self.m_document.pageCount()}")
        else:
            self.m_document.close()
            logger.warning("{!r} is not a valid file", path)

    @QtCore.Slot()
    def reload(self):
        """Reload file."""
        if self.docpath and os.path.exists(self.docpath):
            # get current scroll position
            pos = self.pdfView.verticalScrollBar().value()

            # reload
            t1 = time()
            self.m_document.load(self.docpath)
            t2 = time()

            # update pages
            self.m_pageSelector.setMaximum(self.m_document.pageCount())
            self.m_maxPage.setText(f" of {self.m_document.pageCount()}")

            # scroll back to same point
            self.pdfView.verticalScrollBar().setValue(pos)

            logger.debug("Reloaded from disk in {:.2f}ms.", (t2 - t1) * 1000)
        else:
            logger.debug("Attempted to reload PDF but no valid file found at {!r}.", self.docpath)

    @QtCore.Slot(int)
    def page_selected(self, page):
        """Jump to page."""
        nav = self.pdfView.pageNavigator()
        nav.jump(page, QtCore.QPointF(), nav.currentZoom())

    @QtCore.Slot()
    def zoom_in_triggered(self):
        """Zoom in."""
        factor = self.pdfView.zoomFactor() * 1.2
        self.pdfView.setZoomFactor(factor)

    @QtCore.Slot()
    def zoom_out_triggered(self):
        """Zoom out."""
        factor = self.pdfView.zoomFactor() / 1.2
        self.pdfView.setZoomFactor(factor)

    @QtCore.Slot()
    def previous_page_triggered(self):
        """Switch to previous page."""
        nav = self.pdfView.pageNavigator()
        nav.jump(max(nav.currentPage() - 1, 0), QtCore.QPointF(), nav.currentZoom())

    @QtCore.Slot()
    def next_page_triggered(self):
        """Switch to next page."""
        nav = self.pdfView.pageNavigator()
        nav.jump(min(nav.currentPage() + 1, self.pdfView.document().pageCount() - 1), QtCore.QPointF(), nav.currentZoom())

    @QtCore.Slot()
    def open_in_external_viewer(self):
        """Open the pdf file in an external viewer."""
        if self.docpath:
            util.open_with_external_program(self.docpath)
        else:
            logger.warning("Attempted to open external PDF viewer but no file is loaded.")
