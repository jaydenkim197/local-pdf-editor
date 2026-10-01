import time
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter
from PySide6.QtCore import Qt, QMimeData, QUrl, QPointF
from PySide6.QtGui import QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from local_pdf_editor.app import Window
from local_pdf_editor.tools import M1_TOOLS, TOOLS


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    widget = Window()
    widget.show()
    app.processEvents()
    yield widget
    if widget.worker:
        widget.worker.cancel.set()
        assert widget.worker.wait(10000)
        app.processEvents()
    widget.close()
    app.processEvents()


def await_job(app, window):
    deadline = time.monotonic() + 15
    while window.worker and time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(5)
    app.processEvents()
    assert window.worker is None
    assert window.last_result is not None
    return window.last_result


def make_pdf(path):
    with PdfWriter() as writer:
        writer.add_blank_page(100, 100)
        writer.add_blank_page(200, 100)
        writer.write(path)


def test_cards_categories_and_shared_workspace(window, app):
    window.category.setCurrentText('PDF Optimization')
    assert window.empty.isVisible()
    assert all(not card.isVisible() for _, card in window.card_widgets)
    window.category.setCurrentText('All')
    for tool, card in window.card_widgets:
        assert card.isVisible()
        QTest.mouseClick(card, Qt.MouseButton.LeftButton)
        assert window.tool.id == tool.id
        assert window.stack.currentWidget() is window.workspace
        QTest.mouseClick(window.back_button, Qt.MouseButton.LeftButton)
    assert len(M1_TOOLS) == 14


def test_gui_drag_drop_resize_job_and_open_local(window, app, tmp_path, monkeypatch):
    source = tmp_path / '한글 사진.png'
    Image.new('RGB', (80, 40), 'red').save(source)
    window.select_tool('image_resize')
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(source))])
    event = QDropEvent(QPointF(10, 10), Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    window.files.dropEvent(event)
    assert window.file_paths() == [source]
    assert not window.preview.pixmap().isNull()
    window.percent.setCurrentText('50')
    window.output.setText(str(tmp_path / '결과'))
    QTest.mouseClick(window.process_button, Qt.MouseButton.LeftButton)
    assert not window.controls.isEnabled()
    result = await_job(app, window)
    assert not result.errors
    assert window.results.count() == 1
    assert window.progress_bar.value() == 100
    assert window.controls.isEnabled()
    with Image.open(result.outputs[0]) as image:
        assert image.size == (40, 20)
    opened = []
    monkeypatch.setattr(window, 'open_local', lambda path: opened.append(path))
    QTest.mouseClick(window.open_button, Qt.MouseButton.LeftButton)
    QTest.mouseClick(window.folder_button, Qt.MouseButton.LeftButton)
    assert opened == [result.outputs[0], result.outputs[0].parent]


def test_gui_file_order_remove_and_page_order(window, app, tmp_path):
    a, b = tmp_path / 'a.pdf', tmp_path / 'b.pdf'
    make_pdf(a)
    make_pdf(b)
    window.select_tool('pdf_merge')
    window.add_files([a, b])
    window.files.setCurrentRow(1)
    window.move_file(-1)
    assert window.file_paths() == [b, a]
    window.remove_files()
    assert window.file_paths() == [a]
    window.select_tool('pdf_reorder')
    window.add_files([a])
    assert window.pages_list.count() == 2
    first = window.pages_list.takeItem(0)
    window.pages_list.addItem(first)
    window.use_page_order()
    assert window.pages.text() == '2,1'
    window.output.setText(str(tmp_path / 'out'))
    window.start_job()
    result = await_job(app, window)
    assert not result.errors
    assert [int(p.mediabox.width) for p in PdfReader(result.outputs[0]).pages] == [200, 100]


def test_gui_invalid_input_and_retry(window, app, tmp_path):
    bad = tmp_path / 'bad.pdf'
    bad.write_bytes(b'bad pdf')
    window.select_tool('pdf_split')
    window.add_files([bad])
    window.output.setText(str(tmp_path / 'out'))
    window.start_job()
    result = await_job(app, window)
    assert result.errors and window.errors.isVisible()
    assert window.process_button.isEnabled()
    good = tmp_path / 'good.pdf'
    make_pdf(good)
    window.files.clear()
    window.add_files([good])
    window.start_job()
    assert not await_job(app, window).errors


def test_gui_cancel_and_close_waits_for_thread(window, app, tmp_path):
    path = tmp_path / 'many.pdf'
    with PdfWriter() as writer:
        for _ in range(300):
            writer.add_blank_page(100, 100)
        writer.write(path)
    window.select_tool('pdf_png')
    window.add_files([path])
    window.output.setText(str(tmp_path / 'out'))
    window.start_job()
    window.close()
    assert window.close_when_done
    result = await_job(app, window)
    assert result.cancelled
    assert not window.isVisible()


def test_hidden_resize_fields_do_not_break_pdf_tool(window, tmp_path):
    window.select_tool('image_resize')
    window.percent.setCurrentText('invalid')
    window.select_tool('pdf_split')
    assert window.get_options().percent == 100


@pytest.mark.parametrize('tool', [t.id for t in M1_TOOLS])
def test_every_tool_through_shared_gui(window, app, tmp_path, tool):
    pdf = tmp_path / 'input.pdf'
    other = tmp_path / 'other.pdf'
    make_pdf(pdf)
    make_pdf(other)
    png, jpeg = tmp_path / 'image.png', tmp_path / 'image.jpg'
    Image.new('RGB', (40, 20), 'green').save(png)
    Image.new('RGB', (40, 20), 'green').save(jpeg)
    heic = Path(__file__).parent / 'fixtures/sample.heic'
    window.select_tool(tool)
    if tool == 'pdf_merge' or tool == 'pdf_import':
        inputs = [pdf, other]
    elif tool.startswith('pdf_'):
        inputs = [pdf]
    elif tool.startswith('heic_'):
        inputs = [heic]
    elif tool == 'jpeg_png':
        inputs = [jpeg]
    else:
        inputs = [png]
    window.add_files(inputs)
    if tool == 'pdf_delete':
        window.pages.setText('1')
    if tool == 'pdf_reorder':
        window.pages.setText('2,1')
    if tool == 'image_resize':
        window.resize_mode.setCurrentText('Dimensions')
        window.width.setValue(20)
        window.height.setValue(20)
    window.output.setText(str(tmp_path / 'output'))
    QTest.mouseClick(window.process_button, Qt.MouseButton.LeftButton)
    result = await_job(app, window)
    assert not result.errors, result.errors
    assert result.outputs and window.results.count() == len(result.outputs)
    assert window.open_button.isEnabled()
