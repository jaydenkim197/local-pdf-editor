"""One shared Qt workspace for all local M1 tools."""
import sys
from pathlib import Path
from threading import Event

import pypdfium2 as pdfium
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QComboBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QProgressBar, QPushButton,
    QScrollArea, QSpinBox, QStackedWidget, QTextEdit, QVBoxLayout, QWidget, QCheckBox,
)

from .processing import Result, open_image, read_pdf, run_job
from .tools import CATEGORIES, Options, TOOLS, TOOL_BY_ID
from contextlib import ExitStack


class FileList(QListWidget):
    dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setMinimumHeight(110)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            self.dropped.emit([Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()])
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class JobThread(QThread):
    progress = Signal(int, str)
    result = Signal(object)

    def __init__(self, tool, files, folder, options):
        super().__init__()
        self.tool, self.files, self.folder, self.options = tool, files, folder, options
        self.cancel = Event()

    def run(self):
        self.result.emit(run_job(self.tool, self.files, self.folder, self.options,
                                 self.cancel, self.progress.emit))


def button(text, callback):
    widget = QPushButton(text)
    widget.clicked.connect(callback)
    return widget


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local PDF & Image Utilities")
        self.resize(1080, 850)
        self.tool = None
        self.worker = None
        self.last_result = None
        self.close_when_done = False
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.home = self.make_home()
        self.workspace = self.make_workspace()
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.workspace)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f7f8fb; color: #17243b; font-size: 13px; }
            QLabel#title { font-size: 26px; font-weight: bold; }
            QPushButton { background: white; border: 1px solid #cad3e2; border-radius: 7px; padding: 9px 14px; }
            QPushButton:hover { border-color: #356ce5; background: #edf3ff; }
            QPushButton:disabled { color: #8c96a8; }
            QPushButton#primary { background: #245bd8; color: white; font-weight: bold; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QListWidget, QTextEdit { background: white; border: 1px solid #cad3e2; padding: 5px; }
            QGroupBox { border: 1px solid #d9e0eb; border-radius: 6px; margin-top: 12px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; }
        """)

    def make_home(self):
        home = QWidget()
        layout = QVBoxLayout(home)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Your files. Your computer.")
        title.setObjectName("title")
        layout.addWidget(title)
        layout.addWidget(QLabel("PDF and image utilities • Offline processing • Originals preserved"))
        self.category = QComboBox()
        self.category.addItems(CATEGORIES)
        layout.addWidget(self.category)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cards = QWidget()
        self.cards = QGridLayout(cards)
        self.card_widgets = []
        for tool in TOOLS:
            card = button(f"{tool.title}\n\n{tool.hint}", lambda checked=False, t=tool.id: self.select_tool(t))
            card.setMinimumHeight(115)
            self.card_widgets.append((tool, card))
        self.empty = QLabel("No M1 tools in this category. Choose All to see available tools.")
        self.cards.addWidget(self.empty, 0, 0)
        scroll.setWidget(cards)
        layout.addWidget(scroll)
        self.category.currentTextChanged.connect(self.filter_cards)
        self.filter_cards("All")
        return home

    def filter_cards(self, category):
        visible = 0
        for tool, card in self.card_widgets:
            self.cards.removeWidget(card)
            show = category == "All" or category == tool.category
            card.setVisible(show)
            if show:
                self.cards.addWidget(card, visible // 2, visible % 2)
                visible += 1
        self.empty.setVisible(visible == 0)

    def make_workspace(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contents = QWidget()
        layout = QVBoxLayout(contents)
        layout.setContentsMargins(24, 18, 24, 18)
        self.back_button = button("← All tools", lambda: self.stack.setCurrentWidget(self.home))
        layout.addWidget(self.back_button)
        self.heading = QLabel()
        self.heading.setObjectName("title")
        self.hint = QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.heading)
        layout.addWidget(self.hint)
        self.controls = QWidget()
        controls_layout = QVBoxLayout(self.controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(QLabel("Drop files below, or choose files. Drag list items to change the order."))
        self.files = FileList()
        self.files.dropped.connect(self.add_files)
        self.files.currentItemChanged.connect(self.preview_current)
        self.files.model().rowsMoved.connect(self.refresh_pages)
        controls_layout.addWidget(self.files)
        file_actions = QHBoxLayout()
        file_actions.addWidget(button("Choose files…", self.pick_files))
        file_actions.addWidget(button("Remove selected", self.remove_files))
        file_actions.addWidget(button("Move up", lambda: self.move_file(-1)))
        file_actions.addWidget(button("Move down", lambda: self.move_file(1)))
        controls_layout.addLayout(file_actions)
        preview_row = QHBoxLayout()
        self.preview = QLabel("Select a file to preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(180, 130)
        self.preview.setMaximumHeight(160)
        preview_row.addWidget(self.preview)
        self.page_group = QGroupBox("PDF pages — drag to reorder, select to choose")
        page_layout = QVBoxLayout(self.page_group)
        self.pages_list = QListWidget()
        self.pages_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.pages_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.pages_list.setMaximumHeight(120)
        page_layout.addWidget(self.pages_list)
        page_actions = QHBoxLayout()
        page_actions.addWidget(button("Use selected pages", self.use_selected_pages))
        page_actions.addWidget(button("Use displayed order", self.use_page_order))
        page_layout.addLayout(page_actions)
        preview_row.addWidget(self.page_group, 2)
        controls_layout.addLayout(preview_row)
        self.options_group = QGroupBox("Tool options")
        form = QFormLayout(self.options_group)
        self.option_rows = {}
        self.pages = QLineEdit()
        self.pages.setPlaceholderText("Blank = all pages. Examples: 1,3-5 or 3,1,2")
        self.rotation = QComboBox()
        self.rotation.addItems(["90", "180", "270"])
        self.dpi = QSpinBox()
        self.dpi.setRange(36, 600)
        self.dpi.setValue(144)
        self.insert_after = QSpinBox()
        self.insert_after.setRange(0, 100000)
        self.resize_mode = QComboBox()
        self.resize_mode.addItems(["Percentage", "Dimensions"])
        self.percent = QComboBox()
        self.percent.setEditable(True)
        self.percent.addItems(["25", "50", "75", "100"])
        self.percent.setCurrentText("100")
        self.width, self.height = QSpinBox(), QSpinBox()
        for spin in (self.width, self.height):
            spin.setRange(0, 40000)
            spin.setSpecialValueText("Auto")
        self.aspect = QCheckBox("Maintain aspect ratio")
        self.aspect.setChecked(True)
        self.format = QComboBox()
        self.format.addItems(["PNG", "JPEG"])
        self.quality = QSpinBox()
        self.quality.setRange(1, 100)
        self.quality.setValue(90)
        for key, label, widget in [
            ("pages", "Pages (1-based)", self.pages), ("rotation", "Clockwise degrees", self.rotation),
            ("dpi", "Render DPI", self.dpi), ("insert", "Insert after page (0 = beginning)", self.insert_after),
            ("mode", "Resize mode", self.resize_mode), ("percent", "Percentage", self.percent),
            ("width", "Width in pixels", self.width), ("height", "Height in pixels", self.height),
            ("aspect", "Aspect ratio", self.aspect), ("format", "Output format", self.format),
            ("quality", "JPEG quality", self.quality),
        ]:
            label_widget = QLabel(label)
            form.addRow(label_widget, widget)
            self.option_rows[key] = (label_widget, widget)
        self.resize_mode.currentTextChanged.connect(self.show_options)
        controls_layout.addWidget(self.options_group)
        output_row = QHBoxLayout()
        self.output = QLineEdit(str(Path.home() / "Documents" / "Local PDF Outputs"))
        output_row.addWidget(QLabel("Output folder"))
        output_row.addWidget(self.output, 1)
        output_row.addWidget(button("Browse…", self.pick_output))
        controls_layout.addLayout(output_row)
        layout.addWidget(self.controls)
        actions = QHBoxLayout()
        self.process_button = button("Process locally", self.start_job)
        self.process_button.setObjectName("primary")
        self.cancel_button = button("Cancel", self.cancel_job)
        self.cancel_button.setEnabled(False)
        actions.addWidget(self.process_button)
        actions.addWidget(self.cancel_button)
        layout.addLayout(actions)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.status = QLabel("Ready")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.results = QListWidget()
        self.results.setMaximumHeight(120)
        self.results.itemDoubleClicked.connect(self.open_result)
        layout.addWidget(self.results)
        self.errors = QTextEdit()
        self.errors.setReadOnly(True)
        self.errors.setMaximumHeight(90)
        self.errors.hide()
        layout.addWidget(self.errors)
        result_actions = QHBoxLayout()
        self.open_button = button("Open selected output", self.open_result)
        self.folder_button = button("Open output folder", self.open_folder)
        self.open_button.setEnabled(False)
        self.folder_button.setEnabled(False)
        result_actions.addWidget(self.open_button)
        result_actions.addWidget(self.folder_button)
        layout.addLayout(result_actions)
        scroll.setWidget(contents)
        return scroll

    def select_tool(self, tool_id):
        if self.worker:
            return
        self.tool = TOOL_BY_ID[tool_id]
        self.files.clear()
        self.pages_list.clear()
        self.pages.clear()
        self.results.clear()
        self.errors.clear()
        self.errors.hide()
        self.last_result = None
        self.open_button.setEnabled(False)
        self.folder_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status.setText("Ready — outputs will never overwrite existing files.")
        self.heading.setText(self.tool.title)
        note = " Structural PDF changes can invalidate existing digital signatures." if tool_id.startswith('pdf_') and tool_id not in ('pdf_png', 'pdf_jpeg') else ""
        self.hint.setText(self.tool.hint + note)
        self.show_options()
        self.stack.setCurrentWidget(self.workspace)

    def show_options(self, *_):
        if not self.tool:
            return
        tool = self.tool.id
        keys = set()
        if tool.startswith('pdf_') and tool != 'pdf_merge':
            keys.add('pages')
        if tool == 'pdf_rotate': keys.add('rotation')
        if tool == 'pdf_import': keys.add('insert')
        if tool in ('pdf_png', 'pdf_jpeg'): keys.add('dpi')
        if tool.endswith('jpeg'): keys.add('quality')
        if tool == 'image_resize':
            keys.update(('mode', 'format', 'quality'))
            keys.update(('percent',) if self.resize_mode.currentText() == 'Percentage' else ('width', 'height', 'aspect'))
        for key, widgets in self.option_rows.items():
            for widget in widgets:
                widget.setVisible(key in keys)
        self.options_group.setVisible(bool(keys))
        self.page_group.setVisible(tool.startswith('pdf_') and tool != 'pdf_merge')

    def file_paths(self):
        return [Path(self.files.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.files.count())]

    def add_files(self, paths):
        if self.worker or not self.tool:
            return
        errors = []
        current = set(self.file_paths())
        for path in paths:
            path = Path(path).resolve()
            if not path.is_file() or path.suffix.lower() not in self.tool.extensions:
                errors.append(f"Unsupported input: {path.name}")
                continue
            if path in current:
                continue
            if self.tool.maximum is not None and self.files.count() >= self.tool.maximum:
                errors.append(f"This tool accepts at most {self.tool.maximum} file(s). Remove a file to replace it.")
                break
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.files.addItem(item)
            current.add(path)
        if errors:
            self.status.setText("\n".join(errors))
        self.refresh_pages()
        if self.files.count():
            self.files.setCurrentRow(0)

    def pick_files(self):
        extensions = ' '.join('*' + e for e in self.tool.extensions)
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose input files", "", f"Supported files ({extensions})")
        self.add_files(paths)

    def remove_files(self):
        for item in self.files.selectedItems():
            self.files.takeItem(self.files.row(item))
        self.refresh_pages()

    def move_file(self, direction):
        row = self.files.currentRow()
        new_row = row + direction
        if row >= 0 and 0 <= new_row < self.files.count():
            item = self.files.takeItem(row)
            self.files.insertItem(new_row, item)
            self.files.setCurrentRow(new_row)
            self.refresh_pages()

    def refresh_pages(self, *_):
        self.pages_list.clear()
        paths = self.file_paths()
        if not paths or not self.tool.id.startswith('pdf_'):
            return
        path = paths[1] if self.tool.id == 'pdf_import' and len(paths) == 2 else paths[0]
        try:
            with ExitStack() as stack:
                reader = read_pdf(stack, path)
                for number, page in enumerate(reader.pages, 1):
                    item = QListWidgetItem(f"Page {number}  •  {int(page.mediabox.width)} × {int(page.mediabox.height)} pt  •  {page.rotation}°")
                    item.setData(Qt.ItemDataRole.UserRole, number)
                    self.pages_list.addItem(item)
        except Exception as e:
            self.status.setText(f"Cannot inspect {path.name}: {e}")

    def use_selected_pages(self):
        numbers = [str(item.data(Qt.ItemDataRole.UserRole)) for item in self.pages_list.selectedItems()]
        if numbers:
            self.pages.setText(','.join(numbers))

    def use_page_order(self):
        self.pages.setText(','.join(str(self.pages_list.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.pages_list.count())))

    def preview_current(self, item=None, *_):
        self.preview.clear()
        if item is None or self.worker:
            self.preview.setText("Select a file to preview")
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        image = None
        try:
            if path.suffix.lower() == '.pdf':
                with ExitStack() as stack:
                    read_pdf(stack, path)
                with pdfium.PdfDocument(str(path)) as doc:
                    page = doc[0]
                    try:
                        w, h = page.get_size()
                        if w <= 0 or h <= 0:
                            raise ValueError("Invalid page dimensions")
                        bitmap = page.render(scale=min(180 / w, 130 / h))
                        try:
                            image = bitmap.to_pil().copy()
                        finally:
                            bitmap.close()
                    finally:
                        page.close()
            else:
                with open_image(path) as opened:
                    image = opened.copy()
                    image.thumbnail((180, 130))
            rgba = image.convert('RGBA')
            try:
                qimage = QImage(rgba.tobytes(), rgba.width, rgba.height, rgba.width * 4, QImage.Format.Format_RGBA8888).copy()
                self.preview.setPixmap(QPixmap.fromImage(qimage))
            finally:
                rgba.close()
        except Exception as e:
            self.preview.setText(f"Preview unavailable:\n{e}")
        finally:
            if image is not None:
                image.close()

    def pick_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Output folder", self.output.text())
        if folder:
            self.output.setText(folder)

    def get_options(self):
        resize = self.tool.id == 'image_resize'
        dimensions = resize and self.resize_mode.currentText() == 'Dimensions'
        return Options(pages=self.pages.text(), rotation=int(self.rotation.currentText()),
                       dpi=self.dpi.value(), insert_after=self.insert_after.value(),
                       percent=float(self.percent.currentText()) if resize and not dimensions else 100,
                       width=self.width.value() if dimensions else 0, height=self.height.value() if dimensions else 0,
                       keep_aspect=self.aspect.isChecked(), image_format=self.format.currentText(), quality=self.quality.value())

    def start_job(self):
        if self.worker:
            return
        try:
            options = self.get_options()
            if self.tool.id == 'image_resize' and self.resize_mode.currentText() == 'Dimensions' and not (options.width or options.height):
                raise ValueError("Specify a width or height.")
            if not self.output.text().strip():
                raise ValueError("Choose an output folder.")
            folder = Path(self.output.text()).expanduser().resolve()
        except ValueError as e:
            self.status.setText(str(e))
            return
        self.results.clear()
        self.errors.clear()
        self.errors.hide()
        self.progress_bar.setValue(0)
        self.open_button.setEnabled(False)
        self.folder_button.setEnabled(False)
        self.controls.setEnabled(False)
        self.back_button.setEnabled(False)
        self.process_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.worker = JobThread(self.tool.id, self.file_paths(), folder, options)
        self.worker.progress.connect(self.on_progress)
        self.worker.result.connect(self.on_result)
        self.worker.finished.connect(self.thread_stopped)
        self.worker.start()

    def on_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status.setText(message)

    def on_result(self, result: Result):
        self.last_result = result
        for path in result.outputs:
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.results.addItem(item)
        state = "Cancelled" if result.cancelled else "Finished with errors" if result.errors else "Complete"
        self.status.setText(f"{state} — {len(result.outputs)} output(s) saved. Originals preserved.")
        self.errors.setPlainText('\n'.join(result.errors))
        self.errors.setVisible(bool(result.errors))
        self.open_button.setEnabled(bool(result.outputs))
        self.folder_button.setEnabled(bool(result.outputs))
        if result.outputs:
            self.results.setCurrentRow(0)

    def thread_stopped(self):
        self.worker.deleteLater()
        self.worker = None
        self.controls.setEnabled(True)
        self.back_button.setEnabled(True)
        self.process_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        if self.close_when_done:
            self.close()

    def cancel_job(self):
        if self.worker:
            self.worker.cancel.set()
            self.cancel_button.setEnabled(False)
            self.status.setText("Cancelling after the current file/page operation…")

    def open_result(self, *_):
        item = self.results.currentItem()
        if item:
            self.open_local(Path(item.data(Qt.ItemDataRole.UserRole)))

    def open_folder(self):
        if self.last_result and self.last_result.outputs:
            self.open_local(self.last_result.outputs[0].parent)

    def open_local(self, path):
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
            self.status.setText(f"Could not open {path}. You can open it manually.")

    def closeEvent(self, event):
        if self.worker:
            self.close_when_done = True
            self.cancel_job()
            event.ignore()
        else:
            event.accept()


def main():
    if '--smoke-test' in sys.argv:
        from .smoke import smoke_test
        return smoke_test()
    app = QApplication(sys.argv)
    app.setApplicationName("Local PDF Utilities")
    window = Window()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
