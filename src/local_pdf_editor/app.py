"""One shared Qt workspace for all local M1 tools."""
import sys
from pathlib import Path
from threading import Event

import pypdfium2 as pdfium
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QRectF
from PySide6.QtGui import QDesktopServices, QImage, QPixmap, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QComboBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QProgressBar, QPushButton,
    QScrollArea, QSpinBox, QStackedWidget, QTextEdit, QVBoxLayout, QWidget, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
)

from .processing import Result, open_image, read_pdf, run_job
from .tools import CATEGORIES, M2_IDS, M3_IDS, Options, TOOLS, TOOL_BY_ID
from .m2 import inspect_forms, parse_redactions
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
        try:
            self.result.emit(run_job(self.tool, self.files, self.folder, self.options,
                                     self.cancel, self.progress.emit))
        finally:
            self.options = None


class SelectionPreview(QLabel):
    rectangleSelected = Signal(float, float, float, float)

    def __init__(self, text):
        super().__init__(text)
        self.page_size = None
        self.selection = None
        self.start = None

    def display(self, pixmap, page_size=None):
        self.page_size = page_size
        self.selection = None
        self.start = None
        self.setPixmap(pixmap)

    def area(self):
        pixmap = self.pixmap()
        if pixmap.isNull():
            return QRectF()
        return QRectF((self.width() - pixmap.width()) / 2, (self.height() - pixmap.height()) / 2, pixmap.width(), pixmap.height())

    def mousePressEvent(self, event):
        if self.page_size and event.button() == Qt.MouseButton.LeftButton and self.area().contains(event.position()):
            self.start = event.position()
            self.selection = None

    def mouseMoveEvent(self, event):
        if self.start is not None:
            self.selection = QRectF(self.start, event.position()).normalized().intersected(self.area())
            self.update()

    def mouseReleaseEvent(self, event):
        if self.start is not None:
            area = self.area()
            rect = QRectF(self.start, event.position()).normalized().intersected(area)
            self.start = None
            self.selection = rect
            if rect.width() >= 2 and rect.height() >= 2:
                w, h = self.page_size
                self.rectangleSelected.emit((rect.left() - area.left()) * w / area.width(),
                                            (rect.top() - area.top()) * h / area.height(),
                                            rect.width() * w / area.width(), rect.height() * h / area.height())
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.selection:
            painter = QPainter(self)
            painter.setPen(QPen(QColor('#e02d4a'), 2))
            painter.setBrush(QColor(240, 30, 60, 50))
            painter.drawRect(self.selection)


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
        self.empty = QLabel("No tools in this category. Choose All to see available tools.")
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
        self.files.currentItemChanged.connect(self.file_changed)
        self.files.model().rowsMoved.connect(self.refresh_pages)
        controls_layout.addWidget(self.files)
        file_actions = QHBoxLayout()
        file_actions.addWidget(button("Choose files…", self.pick_files))
        file_actions.addWidget(button("Remove selected", self.remove_files))
        file_actions.addWidget(button("Move up", lambda: self.move_file(-1)))
        file_actions.addWidget(button("Move down", lambda: self.move_file(1)))
        controls_layout.addLayout(file_actions)
        preview_row = QHBoxLayout()
        self.preview = SelectionPreview("Select a file to preview")
        self.preview.rectangleSelected.connect(self.mark_rectangle)
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
        self.pages_list.currentItemChanged.connect(self.preview_page)
        page_layout.addWidget(self.pages_list)
        page_actions = QHBoxLayout()
        self.select_pages_button = button("Use selected pages", self.use_selected_pages)
        self.order_pages_button = button("Use displayed order", self.use_page_order)
        page_actions.addWidget(self.select_pages_button)
        page_actions.addWidget(self.order_pages_button)
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
        self.margins = QLineEdit('10,10,10,10')
        self.watermark = QLineEdit()
        self.font_path = QLineEdit()
        self.signature_path = QLineEdit()
        self.font_size = QDoubleSpinBox()
        self.font_size.setRange(1, 200)
        self.font_size.setValue(12)
        self.opacity = QDoubleSpinBox()
        self.opacity.setRange(0.01, 1)
        self.opacity.setSingleStep(0.05)
        self.opacity.setValue(0.25)
        self.angle = QSpinBox()
        self.angle.setRange(-180, 180)
        self.angle.setValue(45)
        self.start_number = QSpinBox()
        self.start_number.setRange(1, 1_000_000)
        self.password, self.new_password, self.confirm_password = QLineEdit(), QLineEdit(), QLineEdit()
        for widget in (self.password, self.new_password, self.confirm_password):
            widget.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.editingFinished.connect(self.password_changed)
        self.position = QLineEdit('20,20,120,50')
        self.redactions = QTextEdit()
        self.redactions.setAcceptRichText(False)
        self.redactions.setMaximumHeight(90)
        self.redactions.setPlaceholderText('Select a page and drag a region in the preview. Or enter:\n1:20,30,100,40')
        self.threshold = QSpinBox()
        self.threshold.setRange(0, 255)
        self.threshold.setValue(8)
        self.flatten = QCheckBox('Flatten to images — text and interactive fields are lost')
        self.compress_images = QCheckBox('Re-encode opaque images as JPEG (lossy)')
        self.compress_images.toggled.connect(self.show_options)
        self.image_max_dimension = QSpinBox()
        self.image_max_dimension.setRange(0, 40000)
        self.image_max_dimension.setSpecialValueText('Keep dimensions')
        self.image_max_dimension.setValue(2000)
        self.tesseract_path, self.tessdata_path = QLineEdit(), QLineEdit()
        self.tesseract_path.setPlaceholderText('Auto-detect installed Tesseract 5')
        self.tessdata_path.setPlaceholderText('Use the engine’s installed language data')
        self.ocr_language = QLineEdit('eng')
        self.ocr_language.setPlaceholderText('Installed language codes: eng or eng+kor')
        self.ocr_psm = QComboBox()
        for label, value in [('Automatic layout', 3), ('One text block', 6), ('Sparse text', 11)]:
            self.ocr_psm.addItem(label, value)
        tesseract_row = self.path_picker(self.tesseract_path, 'Choose engine…', 'Tesseract executable (*)')
        data_row = QWidget()
        data_layout = QHBoxLayout(data_row)
        data_layout.setContentsMargins(0, 0, 0, 0)
        data_layout.addWidget(self.tessdata_path)
        def choose_data():
            chosen = QFileDialog.getExistingDirectory(self, 'Installed tessdata folder', self.tessdata_path.text())
            if chosen: self.tessdata_path.setText(chosen)
        data_layout.addWidget(button('Choose data…', choose_data))
        self.form_table = QTableWidget(0, 3)
        self.form_table.setHorizontalHeaderLabels(['Field', 'Type', 'Value'])
        self.form_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.form_table.setMaximumHeight(180)
        self.form_schema = []
        font_row = self.path_picker(self.font_path, 'Choose font…', 'TrueType fonts (*.ttf)')
        signature_row = self.path_picker(self.signature_path, 'Choose image…', 'Images (*.png *.jpg *.jpeg)')
        forms = QWidget()
        forms_layout = QVBoxLayout(forms)
        forms_layout.setContentsMargins(0, 0, 0, 0)
        forms_layout.addWidget(button('Load form fields', self.load_form_fields))
        forms_layout.addWidget(self.form_table)
        for key, label, widget in [
            ("pages", "Pages (1-based)", self.pages), ("rotation", "Clockwise degrees", self.rotation),
            ("dpi", "Render DPI", self.dpi), ("insert", "Insert after page (0 = beginning)", self.insert_after),
            ("mode", "Resize mode", self.resize_mode), ("percent", "Percentage", self.percent),
            ("width", "Width in pixels", self.width), ("height", "Height in pixels", self.height),
            ("aspect", "Aspect ratio", self.aspect), ("format", "Output format", self.format),
            ("quality", "JPEG quality", self.quality),
            ('margins', 'Margins: left,top,right,bottom (pt)', self.margins),
            ('text', 'Watermark text', self.watermark), ('font', 'TrueType font (optional)', font_row),
            ('font_size', 'Font size (pt)', self.font_size), ('opacity', 'Watermark opacity', self.opacity),
            ('angle', 'Watermark angle', self.angle), ('start_number', 'First page number', self.start_number),
            ('password', 'Input PDF password (if encrypted)', self.password),
            ('new_password', 'New password', self.new_password), ('confirm_password', 'Confirm new password', self.confirm_password),
            ('signature', 'Signature image', signature_row), ('position', 'Left,top,width,height (visible page pt)', self.position),
            ('redactions', 'Redactions: page:left,top,width,height', self.redactions),
            ('threshold', 'Visual difference threshold (0–255)', self.threshold),
            ('forms', 'AcroForm fields', forms), ('flatten', 'Form output', self.flatten),
            ('compress_images', 'Image compression', self.compress_images),
            ('image_max_dimension', 'Maximum image dimension (px)', self.image_max_dimension),
            ('tesseract', 'Local OCR engine', tesseract_row), ('tessdata', 'Local OCR data', data_row),
            ('ocr_language', 'OCR languages', self.ocr_language), ('ocr_psm', 'OCR page layout', self.ocr_psm),
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
        self.password.clear()
        self.new_password.clear()
        self.confirm_password.clear()
        self.redactions.clear()
        self.form_table.setRowCount(0)
        self.form_schema = []
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
        note = " Structural PDF changes can invalidate existing digital signatures." if tool_id.startswith('pdf_') and tool_id not in ('pdf_png', 'pdf_jpeg', 'pdf_compare') else ""
        if tool_id == 'pdf_redact':
            note += ' All pages become images; searchable text, forms, attachments and metadata are removed. Inspect regions and output before sharing. Select a page, then drag regions in the preview.'
        if tool_id in ('pdf_crop', 'pdf_signature'):
            note += ' Select a page and drag a region, or enter point coordinates.'
        if tool_id == 'pdf_forms':
            note += ' Standard text/check/radio/single-choice fields; form text supports ASCII. XFA is unsupported.'
        if tool_id in M3_IDS and tool_id != 'html_pdf':
            note += ' Encrypted inputs require the correct password; outputs are unencrypted copies.'
        if tool_id in ('pdf_ocr', 'pdf_pdfa'):
            note += ' All pages become images; original forms, vectors, links and metadata are discarded.'
        if tool_id == 'pdf_ocr':
            note += ' OCR accuracy depends on scans and installed language data. The app never downloads engines or models.'
        self.preview.setMaximumHeight(280 if tool_id in ('pdf_redact', 'pdf_crop', 'pdf_signature') else 160)
        if tool_id == 'pdf_watermark': self.font_size.setValue(28)
        if tool_id == 'pdf_numbers': self.font_size.setValue(12)
        self.hint.setText(self.tool.hint + note)
        self.show_options()
        self.stack.setCurrentWidget(self.workspace)

    def show_options(self, *_):
        if not self.tool:
            return
        tool = self.tool.id
        keys = set()
        if tool.startswith('pdf_') and tool not in M3_IDS and tool not in ('pdf_merge', 'pdf_redact', 'pdf_compare', 'pdf_forms', 'pdf_protect', 'pdf_unlock'):
            keys.add('pages')
        if tool == 'pdf_rotate': keys.add('rotation')
        if tool == 'pdf_import': keys.add('insert')
        if tool in ('pdf_png', 'pdf_jpeg'): keys.add('dpi')
        if tool.endswith('jpeg'): keys.add('quality')
        if tool == 'image_resize':
            keys.update(('mode', 'format', 'quality'))
            keys.update(('percent',) if self.resize_mode.currentText() == 'Percentage' else ('width', 'height', 'aspect'))
        if tool in M2_IDS: keys.add('password')
        if tool in M3_IDS and tool != 'html_pdf': keys.add('password')
        if tool == 'pdf_compress':
            keys.add('compress_images')
            if self.compress_images.isChecked(): keys.update(('quality', 'image_max_dimension'))
        if tool in ('pdf_ocr', 'pdf_pdfa'): keys.add('dpi')
        if tool == 'pdf_ocr': keys.update(('tesseract', 'tessdata', 'ocr_language', 'ocr_psm'))
        if tool == 'pdf_crop': keys.add('margins')
        if tool in ('pdf_watermark', 'pdf_numbers'): keys.update(('font', 'font_size'))
        if tool == 'pdf_watermark': keys.update(('text', 'opacity', 'angle'))
        if tool == 'pdf_numbers': keys.add('start_number')
        if tool == 'pdf_protect': keys.update(('new_password', 'confirm_password'))
        if tool == 'pdf_signature': keys.update(('signature', 'position'))
        if tool == 'pdf_redact': keys.update(('redactions', 'dpi'))
        if tool == 'pdf_compare': keys.update(('dpi', 'threshold'))
        if tool == 'pdf_forms': keys.update(('forms', 'flatten', 'dpi'))
        for key, widgets in self.option_rows.items():
            for widget in widgets:
                widget.setVisible(key in keys)
        self.options_group.setVisible(bool(keys))
        self.page_group.setVisible(tool.startswith('pdf_') and tool not in M3_IDS and tool not in ('pdf_merge', 'pdf_protect', 'pdf_unlock', 'pdf_compare', 'pdf_forms'))
        self.select_pages_button.setVisible('pages' in keys)
        self.order_pages_button.setVisible('pages' in keys)
        redaction = tool == 'pdf_redact'
        self.page_group.setTitle('PDF pages — select a page to mark' if redaction else 'PDF pages — drag to reorder, select to choose')
        self.pages_list.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop if redaction else QAbstractItemView.DragDropMode.InternalMove)
        self.pages_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection if redaction else QAbstractItemView.SelectionMode.ExtendedSelection)

    def path_picker(self, field, label, filter):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(field)
        def choose():
            path, _ = QFileDialog.getOpenFileName(self, label, '', filter)
            if path: field.setText(path)
        layout.addWidget(button(label, choose))
        return row

    def password_changed(self):
        if not self.worker and self.tool and self.tool.id in M2_IDS | M3_IDS:
            self.refresh_pages()
            self.preview_current(self.files.currentItem())

    def file_changed(self, item=None, *_):
        if item and self.tool and self.tool.id in M2_IDS | M3_IDS and not self.worker:
            self.refresh_pages()
        self.preview_current(item)

    def preview_page(self, *_):
        if self.tool and self.tool.id in M2_IDS and not self.worker:
            self.preview_current(self.files.currentItem())

    def mark_rectangle(self, left, top, width, height):
        if self.worker or not self.tool:
            return
        rect = ','.join(f'{v:.4f}' for v in (left, top, width, height))
        if self.tool.id == 'pdf_redact':
            item = self.pages_list.currentItem()
            page = item.data(Qt.ItemDataRole.UserRole) if item else 1
            self.redactions.append(f'{page}:{rect}')
        elif self.tool.id == 'pdf_signature':
            self.position.setText(rect)
        elif self.tool.id == 'pdf_crop' and self.preview.page_size:
            w, h = self.preview.page_size
            self.margins.setText(','.join(f'{v:.4f}' for v in (left, top, max(0, w-left-width), max(0, h-top-height))))

    def load_form_fields(self):
        if self.worker or not self.file_paths(): return
        self.form_schema = []
        self.form_table.setRowCount(0)
        try:
            schema = inspect_forms(self.file_paths()[0], self.password.text())
            self.form_schema = schema
            self.form_table.setRowCount(len(schema))
            for row, field in enumerate(schema):
                for column, value in enumerate((field['name'], field['type'])):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.form_table.setItem(row, column, item)
                if field['choices']:
                    combo = QComboBox()
                    combo.addItems(field['choices'])
                    combo.setCurrentText(field['value'])
                    combo.setEnabled(field['supported'] and not field['readonly'])
                    self.form_table.setCellWidget(row, 2, combo)
                else:
                    item = QTableWidgetItem(field['value'])
                    if not field['supported'] or field['readonly']:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.form_table.setItem(row, 2, item)
            self.status.setText(f'{len(schema)} form field(s) loaded; edit values before processing.')
        except Exception as e:
            self.status.setText(f'Cannot load form: {e}')

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
            if self.tool.id == 'pdf_redact' and not current:
                self.redactions.clear()
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
        if self.tool.id == 'pdf_forms':
            self.load_form_fields()

    def pick_files(self):
        extensions = ' '.join('*' + e for e in self.tool.extensions)
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose input files", "", f"Supported files ({extensions})")
        self.add_files(paths)

    def remove_files(self):
        for item in self.files.selectedItems():
            self.files.takeItem(self.files.row(item))
        if self.tool.id == 'pdf_redact':
            self.redactions.clear()
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
        if self.tool.id in M2_IDS | M3_IDS and self.files.currentItem():
            path = Path(self.files.currentItem().data(Qt.ItemDataRole.UserRole))
        try:
            with ExitStack() as stack:
                reader = read_pdf(stack, path, self.password.text() if self.tool.id in M2_IDS | M3_IDS else None)
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
        self.preview.page_size = None
        self.preview.selection = None
        self.preview.start = None
        if item is None or self.worker:
            self.preview.setText("Select a file to preview")
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        image = None
        page_size = None
        try:
            if path.suffix.lower() == '.pdf':
                password = self.password.text() if self.tool.id in M2_IDS | M3_IDS else None
                with ExitStack() as stack:
                    read_pdf(stack, path, password)
                with pdfium.PdfDocument(str(path), password=password) as doc:
                    doc.init_forms()
                    selected = self.pages_list.currentItem()
                    number = selected.data(Qt.ItemDataRole.UserRole) - 1 if selected and self.tool.id in M2_IDS else 0
                    page = doc[min(number, len(doc)-1)]
                    try:
                        w, h = page.get_size()
                        if w <= 0 or h <= 0:
                            raise ValueError("Invalid page dimensions")
                        spatial = self.tool.id in ('pdf_redact', 'pdf_crop', 'pdf_signature')
                        if spatial: page_size = (w, h)
                        bitmap = page.render(scale=min((360 if spatial else 180) / w, (260 if spatial else 130) / h))
                        try:
                            image = bitmap.to_pil().copy()
                        finally:
                            bitmap.close()
                    finally:
                        page.close()
            elif path.suffix.lower() in ('.html', '.htm'):
                self.preview.setText(f'Local HTML: {path.name}\nBasic HTML print layout\nA4 • 15 mm margins')
                return
            else:
                with open_image(path) as opened:
                    image = opened.copy()
                    image.thumbnail((180, 130))
            rgba = image.convert('RGBA')
            try:
                qimage = QImage(rgba.tobytes(), rgba.width, rgba.height, rgba.width * 4, QImage.Format.Format_RGBA8888).copy()
                self.preview.display(QPixmap.fromImage(qimage), page_size)
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
        tool = self.tool.id
        def coordinates(text):
            values = tuple(map(float, text.split(',')))
            if len(values) != 4: raise ValueError('Enter four comma-separated coordinates.')
            return values
        values = []
        if tool == 'pdf_forms':
            for row, field in enumerate(self.form_schema):
                if not field['supported'] or field['readonly']: continue
                combo = self.form_table.cellWidget(row, 2)
                value = combo.currentText() if combo else self.form_table.item(row, 2).text()
                if value != field['value']: values.append((field['name'], value))
        return Options(pages=self.pages.text(), rotation=int(self.rotation.currentText()),
                       dpi=self.dpi.value(), insert_after=self.insert_after.value(),
                       percent=float(self.percent.currentText()) if resize and not dimensions else 100,
                       width=self.width.value() if dimensions else 0, height=self.height.value() if dimensions else 0,
                       keep_aspect=self.aspect.isChecked(), image_format=self.format.currentText(), quality=self.quality.value(),
                       margins=coordinates(self.margins.text()) if tool == 'pdf_crop' else (10,10,10,10),
                       text=self.watermark.text(), font_path=self.font_path.text(), font_size=self.font_size.value(),
                       opacity=self.opacity.value(), angle=self.angle.value(), start_number=self.start_number.value(),
                       password=self.password.text() if tool in M2_IDS | M3_IDS else '',
                       new_password=self.new_password.text() if tool == 'pdf_protect' else '',
                       signature_path=self.signature_path.text() if tool == 'pdf_signature' else '',
                       rect=coordinates(self.position.text()) if tool == 'pdf_signature' else (20,20,120,50),
                       redactions=parse_redactions(self.redactions.toPlainText()) if tool == 'pdf_redact' else (),
                       compare_threshold=self.threshold.value(), form_values=tuple(values), flatten_forms=tool == 'pdf_forms' and self.flatten.isChecked(),
                       compress_images=tool == 'pdf_compress' and self.compress_images.isChecked(), image_max_dimension=self.image_max_dimension.value(),
                       tesseract_path=self.tesseract_path.text(), tessdata_path=self.tessdata_path.text(),
                       ocr_language=self.ocr_language.text().strip(), ocr_psm=self.ocr_psm.currentData())

    def start_job(self):
        if self.worker:
            return
        try:
            options = self.get_options()
            if self.tool.id == 'pdf_protect' and self.new_password.text() != self.confirm_password.text():
                raise ValueError('New passwords do not match.')
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
        self.password.clear()
        self.new_password.clear()
        self.confirm_password.clear()
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
