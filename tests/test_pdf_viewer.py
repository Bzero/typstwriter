from qtpy import QtPdfWidgets
from qtpy import QtPdf

import pytest
from unittest.mock import Mock
import logging
from fpdf import FPDF


from typstwriter import pdf_viewer
from typstwriter import util


@pytest.fixture()
def tmp_pdf(tmp_path, pdf_pages):
    """Create an pdf document with "pdf_pages" empty pages and return its location."""
    n_max = int(1e4)

    for n in range(n_max):
        path = tmp_path / f"tmp_pdf_{n:04d}.pdf"
        if not path.exists():
            break

    pdf = FPDF()
    pdf.set_font("Times", "", 12)
    for _ in range(pdf_pages):
        pdf.add_page()
    pdf.output(path, "F")

    with path.open() as f:
        pdf.write(f)

    return path


class TestZoomSelector:
    """Test pdf_viewer.ZoomSelector."""

    @pytest.mark.parametrize("zoom", [1.0, 0.5, 4.0])
    def test_numeric_user_input(self, qtbot, zoom):
        """Make sure the zoom factor can be set."""
        zoomselector = pdf_viewer.ZoomSelector(None)
        zoomselector.lineEdit().setText("")

        with qtbot.waitSignals(
            [(zoomselector.zoom_mode_changed, "zoom_mode_changed"), (zoomselector.zoom_factor_changed, "zoom_factor_changed")]
        ) as blocker:
            zoomselector.lineEdit().setText(f"{int(zoom * 100)}%")

        args = [s.args for s in blocker.all_signals_and_args]
        assert (zoom,) in args
        assert (QtPdfWidgets.QPdfView.ZoomMode.Custom,) in args

    @pytest.mark.parametrize(
        ("text", "mode"),
        [
            ("Fit Page Width", QtPdfWidgets.QPdfView.ZoomMode.FitToWidth),
            ("Fit Page Height", QtPdfWidgets.QPdfView.ZoomMode.FitInView),
        ],
    )
    def test_mode_user_input(self, qtbot, text, mode):
        """Make sure the zoom factor can be set."""
        zoomselector = pdf_viewer.ZoomSelector(None)
        zoomselector.lineEdit().setText("")

        with qtbot.waitSignal((zoomselector.zoom_mode_changed, "zoom_mode_changed")) as blocker:
            zoomselector.lineEdit().setText(text)
            print(f"{text!r}")
            print(f"{zoomselector.lineEdit().text()!r}")

        assert mode in blocker.args

    @pytest.mark.parametrize("zoom", [0.1, 0.5, 1.0, 1.5, 2])
    def test_set_zoom_factor(self, qtbot, zoom):
        """Make sure the zoom factor can be set."""
        zoomselector = pdf_viewer.ZoomSelector(None)

        with qtbot.waitSignals(
            [(zoomselector.zoom_mode_changed, "zoom_mode_changed"), (zoomselector.zoom_factor_changed, "zoom_factor_changed")]
        ) as blocker:
            zoomselector.set_zoom_factor(zoom)

        args = [s.args for s in blocker.all_signals_and_args]
        assert (zoom,) in args
        assert (QtPdfWidgets.QPdfView.ZoomMode.Custom,) in args

    def test_reset(self, qtbot):
        """Test reset functionality."""
        zoomselector = pdf_viewer.ZoomSelector(None)

        with qtbot.waitSignals(
            [(zoomselector.zoom_mode_changed, "zoom_mode_changed"), (zoomselector.zoom_factor_changed, "zoom_factor_changed")]
        ) as blocker:
            zoomselector.reset()

        args = [s.args for s in blocker.all_signals_and_args]
        assert (1.0,) in args
        assert (QtPdfWidgets.QPdfView.ZoomMode.Custom,) in args


class TestPDFViewer:
    """Test pdf_viewer.PDFViewer."""

    @pytest.mark.parametrize("pdf_pages", [1, 2])
    def test_open_file_fail(self, qtbot, tmp_path, tmp_pdf, caplog):
        """Test opening a path that does not exist."""
        caplog.set_level(logging.INFO)
        pdf_v = pdf_viewer.PDFViewer()

        # Failure
        document = tmp_path / "document.pdf"
        pdf_v.open(str(document))
        assert pdf_v.m_document.status() == QtPdf.QPdfDocument.Status.Null
        assert "not a valid file" in caplog.text

        caplog.clear()

        # Success
        pdf_v.open(str(tmp_pdf))
        assert pdf_v.m_document.status() == QtPdf.QPdfDocument.Status.Ready
        assert "not a valid file" not in caplog.text

        # TODO: Test opening non pdf file

    @pytest.mark.parametrize("pdf_pages", [1, 2])
    def test_reload(self, qtbot, caplog, tmp_pdf):
        """Test reloading a pdf file."""
        caplog.set_level(logging.DEBUG)
        pdf_v = pdf_viewer.PDFViewer()

        pdf_v.open(str(tmp_pdf))

        sb = pdf_v.pdfView.verticalScrollBar()
        sb.setValue((sb.maximum() - sb.minimum()) / 2)
        pos = sb.value()

        pdf_v.reload()
        assert pdf_v.m_document.status() == QtPdf.QPdfDocument.Status.Ready
        assert "Reloaded from disk" in caplog.text
        assert pos == sb.value()

    @pytest.mark.parametrize("zoom", [0.6, 0.9, 1.2, 2.4])
    @pytest.mark.parametrize("pdf_pages", [1, 2])
    def test_zoom(self, qtbot, caplog, tmp_pdf, zoom):
        """Test reloading a pdf file."""
        caplog.set_level(logging.DEBUG)
        pdf_v = pdf_viewer.PDFViewer()

        pdf_v.open(str(tmp_pdf))

        pdf_v.m_zoomSelector.setCurrentText(f"{int(zoom * 100)}%")
        assert pdf_v.m_zoomSelector.currentText() == f"{int(zoom * 100)}%"
        assert pdf_v.pdfView.zoomFactor() == zoom

        pdf_v.m_zoomSelector.setCurrentText(f"{int(zoom * 100)}%")
        pdf_v.actionZoom_Out.trigger()
        assert pdf_v.m_zoomSelector.currentText() == f"{int(zoom * 100 / 1.2)}%"
        assert pdf_v.pdfView.zoomFactor() == zoom / 1.2

        pdf_v.m_zoomSelector.setCurrentText(f"{int(zoom * 100)}%")
        pdf_v.actionZoom_In.trigger()
        assert pdf_v.m_zoomSelector.currentText() == f"{int(zoom * 100 * 1.2)}%"
        assert pdf_v.pdfView.zoomFactor() == zoom * 1.2

        # TODO: test fit width
        # TODO; test fit height

    @pytest.mark.parametrize("pdf_pages", [1, 4, 10])
    def test_page_movement(self, qtbot, caplog, tmp_pdf, pdf_pages):
        """Test reloading a pdf file."""
        caplog.set_level(logging.DEBUG)
        pdf_v = pdf_viewer.PDFViewer()

        pdf_v.open(str(tmp_pdf))

        assert pdf_v.m_maxPage.text() == f" of {pdf_pages}"

        assert pdf_v.m_pageSelector.text() == str(min(1, pdf_pages))
        assert pdf_v.pdfView.pageNavigator().currentPage() + 1 == min(1, pdf_pages)

        pdf_v.actionPrevious_Page.trigger()
        assert pdf_v.m_pageSelector.text() == str(min(1, pdf_pages))
        assert pdf_v.pdfView.pageNavigator().currentPage() + 1 == min(1, pdf_pages)

        pdf_v.actionNext_Page.trigger()
        assert pdf_v.m_pageSelector.text() == str(min(2, pdf_pages))
        assert pdf_v.pdfView.pageNavigator().currentPage() + 1 == min(2, pdf_pages)

        pdf_v.m_pageSelector.setValue(4)
        assert pdf_v.m_pageSelector.text() == str(min(4, pdf_pages))
        assert pdf_v.pdfView.pageNavigator().currentPage() + 1 == min(4, pdf_pages)

        pdf_v.actionPrevious_Page.trigger()
        assert pdf_v.m_pageSelector.text() == str(min(3, pdf_pages))
        assert pdf_v.pdfView.pageNavigator().currentPage() + 1 == min(3, pdf_pages)

        # TODO: Test scrolling

    @pytest.mark.parametrize("pdf_pages", [1, 2])
    def test_open_in_external_viewer(self, qtbot, caplog, tmp_pdf, monkeypatch):
        """Test opening a pdf file with an external viewer."""
        external_program = Mock()
        monkeypatch.setattr(util, "open_with_external_program", external_program)

        caplog.set_level(logging.INFO)
        pdf_v = pdf_viewer.PDFViewer()

        pdf_v.actionOpen_External.trigger()
        assert "Attempted to open external PDF viewer but no file is loaded." in caplog.text
        external_program.assert_not_called()

        pdf_v.open(str(tmp_pdf))

        pdf_v.actionOpen_External.trigger()
        external_program.assert_called_once()
