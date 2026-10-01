import json
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from local_pdf_editor.tools import M2_TOOLS
from test_gui import app, window, await_job
from test_m2 import document, form


@pytest.mark.parametrize('tool', [tool.id for tool in M2_TOOLS])
def test_m2_tools_use_shared_gui_real_jobs(window, app, tmp_path, tool):
    source = form(tmp_path / 'source.pdf') if tool == 'pdf_forms' else document(tmp_path / 'source.pdf')
    second = document(tmp_path / 'second.pdf', text='CHANGED')
    if tool == 'pdf_unlock':
        from local_pdf_editor.processing import run_job
        from local_pdf_editor.tools import Options
        encrypted = run_job('pdf_protect', [source], tmp_path / 'protected', Options(new_password='correct'))
        assert not encrypted.errors
        source = encrypted.outputs[0]
    window.select_tool(tool)
    if tool == 'pdf_unlock': window.password.setText('correct')
    window.add_files([source, second] if tool == 'pdf_compare' else [source])
    if tool == 'pdf_watermark': window.watermark.setText('REVIEW')
    if tool == 'pdf_protect':
        window.new_password.setText('correct')
        window.confirm_password.setText('correct')
    if tool == 'pdf_signature':
        image = tmp_path / 'signature.png'
        Image.new('RGB', (80, 20), 'red').save(image)
        window.signature_path.setText(str(image))
    if tool == 'pdf_redact':
        window.redactions.setPlainText('1:10,20,220,35')
    if tool == 'pdf_forms':
        assert window.form_table.rowCount() == 4
        row = next(i for i, f in enumerate(window.form_schema) if f['name'] == 'name')
        window.form_table.item(row, 2).setText('GUI Filled')
    window.output.setText(str(tmp_path / 'output'))
    QTest.mouseClick(window.process_button, Qt.MouseButton.LeftButton)
    assert window.worker
    assert not window.password.text() and not window.new_password.text() and not window.confirm_password.text()
    result = await_job(app, window)
    assert not result.errors, result.errors
    assert result.outputs and window.results.count() == len(result.outputs)
    if tool == 'pdf_forms':
        assert PdfReader(result.outputs[0]).get_fields()['name']['/V'] == 'GUI Filled'
    if tool == 'pdf_compare':
        assert not json.loads(result.outputs[-1].read_text())['identical_visuals']


def test_visual_redaction_rectangle_and_page_preview(window, app, tmp_path):
    source = document(tmp_path / 'source.pdf')
    window.select_tool('pdf_redact')
    window.add_files([source])
    window.pages_list.setCurrentRow(1)
    app.processEvents()
    area = window.preview.area()
    from PySide6.QtCore import QPointF
    start = (area.topLeft() + QPointF(area.width() * .1, area.height() * .1)).toPoint()
    end = (area.topLeft() + QPointF(area.width() * .6, area.height() * .4)).toPoint()
    QTest.mousePress(window.preview, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(window.preview, end)
    QTest.mouseRelease(window.preview, Qt.MouseButton.LeftButton, pos=end)
    options = window.get_options()
    assert len(options.redactions) == 1 and options.redactions[0][0] == 2
    _, left, top, width, height = options.redactions[0]
    assert 0 <= left < 30 and 0 <= top < 30 and width > 100 and height > 40
    window.output.setText(str(tmp_path / 'output'))
    window.start_job()
    result = await_job(app, window)
    assert not result.errors
    reader = PdfReader(result.outputs[0])
    assert not reader.pages[0].extract_text().strip() and not reader.pages[1].extract_text().strip()


def test_password_mismatch_and_wrong_password_leave_no_output(window, app, tmp_path):
    source = document(tmp_path / 'source.pdf')
    window.select_tool('pdf_protect')
    window.add_files([source])
    window.new_password.setText('one'); window.confirm_password.setText('two')
    window.start_job()
    assert not window.worker and 'do not match' in window.status.text()
    window.confirm_password.setText('one')
    window.output.setText(str(tmp_path / 'output'))
    window.start_job()
    protected = await_job(app, window).outputs[0]
    window.select_tool('pdf_unlock')
    window.password.setText('incorrect')
    window.add_files([protected])
    window.start_job()
    result = await_job(app, window)
    assert result.errors and not result.outputs
    assert 'incorrect' not in window.errors.toPlainText()


def test_forms_flatten_and_hidden_m2_fields_do_not_break_m1(window, app, tmp_path):
    source = form(tmp_path / 'form.pdf')
    window.select_tool('pdf_forms')
    window.add_files([source])
    window.flatten.setChecked(True)
    window.output.setText(str(tmp_path / 'output'))
    window.start_job()
    result = await_job(app, window)
    assert not result.errors and not PdfReader(result.outputs[0]).get_fields()
    window.select_tool('pdf_crop')
    window.margins.setText('invalid')
    window.position.setText('invalid')
    window.redactions.setPlainText('invalid')
    window.select_tool('pdf_split')
    window.add_files([source])
    window.start_job()
    result = await_job(app, window)
    assert not result.errors and result.outputs


def test_redaction_marks_do_not_transfer_to_a_replacement_file(window, app, tmp_path):
    a = document(tmp_path / 'first.pdf')
    b = document(tmp_path / 'replacement.pdf')
    window.select_tool('pdf_redact')
    window.add_files([a])
    window.redactions.setPlainText('1:10,20,100,30')
    window.files.setCurrentRow(0)
    window.remove_files()
    window.add_files([b])
    assert not window.redactions.toPlainText()
    window.start_job()
    assert not window.worker and 'at least one' in window.status.text()
