"""Expose actual pytest results in Actions summaries and failure annotations."""
import argparse
import os
from pathlib import Path
import xml.etree.ElementTree as ET


def escape(text):
    return text.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    try:
        root = ET.parse(args.report).getroot()
    except (OSError, ET.ParseError) as error:
        print('::error::' + escape(f'No readable pytest result: {error}. Verification is incomplete.'))
        return 1
    cases = list(root.iter('testcase'))
    failed = [(case, issue) for case in cases for issue in case if issue.tag in ('failure', 'error')]
    skipped = sum(case.find('skipped') is not None for case in cases)
    counts = f'{len(cases)} cases; {len(failed)} failures/errors; {skipped} skipped'
    print(counts)
    print('::notice title=Actual pytest results::' + escape(counts))
    if os.environ.get('PDF_PREFLIGHT_JAR'):
        validated = sum(case.get('name', '').startswith('test_pdfa_fresh_raster_output_and_independent_preflight')
                        and not any(item.tag in ('failure', 'error', 'skipped') for item in case) for case in cases)
        print(f'::notice title=Independent PDF-A validation::{validated} PDF/A specimen tests passed with independent Preflight enabled.')
    lines = ['## Actual pytest results', '', counts, '']
    for index, (case, issue) in enumerate(failed):
        name = f"{case.get('classname', '')}.{case.get('name', '')}"
        detail = issue.text or issue.get('message', 'No details supplied')
        if index < 10:
            title = escape(name).replace(',', '%2C').replace(':', '%3A')
            print(f'::error title={title}::{escape(detail[-6000:])}')
        lines.extend([f'### {name}', '', '```text', detail[-8000:], '```', ''])
    if not cases:
        print('::error::No test cases executed. Verification is incomplete.')
    if skipped:
        print(f'::warning::{skipped} pytest cases skipped; do not claim they passed.')
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with Path(summary).open('a', encoding='utf-8') as stream:
            stream.write('\n'.join(lines) + '\n')
    return int(bool(failed) or not cases)


if __name__ == '__main__':
    raise SystemExit(main())
