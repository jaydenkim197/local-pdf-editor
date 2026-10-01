import json
import os
import platform
from pathlib import Path
import sys
import traceback

from local_pdf_editor.app import main


if '--smoke-test' in sys.argv and '--smoke-report' in sys.argv:
    report = Path(sys.argv[sys.argv.index('--smoke-report') + 1])
    evidence = {'platform': platform.platform(), 'python': platform.python_version(),
                'frozen': bool(getattr(sys, 'frozen', False)), 'executable': sys.executable,
                'scale_factor': os.environ.get('QT_SCALE_FACTOR', '1')}
    try:
        status = main()
        evidence['passed'] = status == 0
        from PySide6.QtGui import QGuiApplication
        evidence['qt_backend'] = QGuiApplication.platformName()
    except Exception:
        status = 1
        evidence.update(passed=False, error=traceback.format_exc())
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding='utf-8')
    raise SystemExit(status)

raise SystemExit(main())
