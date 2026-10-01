import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from pypdf import PdfReader

from local_pdf_editor.tools import M3_TOOLS
from test_gui import app, await_job, window
from test_m2 import document


@pytest.mark.parametrize('tool', [t.id for t in M3_TOOLS])
def test_all_m3_tools_run_in_shared_workspace(window, app, tmp_path, tool):
    source = document(tmp_path / 'source.pdf')
    if tool == 'html_pdf':
        source = tmp_path / 'local.html';source.write_text('<h1>GUI HTML</h1>')
    window.select_tool(tool)
    window.add_files([source])
    window.dpi.setValue(144)
    window.output.setText(str(tmp_path / 'out'))
    assert not window.page_group.isVisible()
    if tool == 'html_pdf': assert 'Local HTML' in window.preview.text()
    QTest.mouseClick(window.process_button, Qt.MouseButton.LeftButton)
    assert window.worker
    result = await_job(app, window)
    assert not result.errors and result.outputs
    assert window.results.count() == 1 and PdfReader(result.outputs[0]).pages


def test_compression_and_ocr_options_remain_tool_specific(window, app):
    window.select_tool('pdf_compress')
    assert not window.option_rows['quality'][1].isVisible()
    window.compress_images.setChecked(True)
    assert window.option_rows['quality'][1].isVisible()
    window.image_max_dimension.setValue(600)
    assert window.get_options().compress_images and window.get_options().image_max_dimension == 600
    window.select_tool('pdf_ocr')
    assert window.option_rows['tesseract'][1].isVisible()
    window.ocr_language.setText('eng+kor')
    window.ocr_psm.setCurrentIndex(1)
    assert window.get_options().ocr_language == 'eng+kor' and window.get_options().ocr_psm == 6
    window.select_tool('pdf_merge')
    assert not window.option_rows['tesseract'][1].isVisible()
    assert not window.get_options().compress_images


def test_missing_ocr_engine_shows_error_and_allows_retry(window, app, tmp_path):
    source = document(tmp_path / 'source.pdf')
    window.select_tool('pdf_ocr');window.add_files([source])
    window.output.setText(str(tmp_path / 'out'))
    window.tesseract_path.setText('/missing/engine')
    window.start_job()
    result = await_job(app, window)
    assert result.errors and not result.outputs and 'Install local' in window.errors.toPlainText()
    assert window.controls.isEnabled() and window.process_button.isEnabled()
    window.tesseract_path.clear();window.start_job()
    assert not await_job(app, window).errors
