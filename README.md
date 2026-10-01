# Local PDF & Image Utilities

Windows 우선, 완전 로컬 PDF·이미지 유틸리티입니다. 파일 업로드, 계정, AI 처리, 네트워크 서비스 없이 동작합니다. 원본과 기존 결과 파일을 덮어쓰지 않습니다.

## M1 기능

- PDF 병합·분할·페이지 순서 변경·삭제·가져오기·회전
- PDF → JPEG/PNG, JPEG/PNG → PDF
- HEIC → JPEG/PNG, JPEG ↔ PNG
- 일괄 크기 변경: 25/50/75/100%, 임의 비율, 너비·높이, 비율 유지, EXIF 방향 보정
- 공통 화면: 드롭/파일 선택, 순서 변경, 미리보기, 옵션, 진행·취소, 결과 파일/폴더 열기

기존 PDF 본문·이미지 직접 편집, Office 변환, AI 요약·번역, Markdown 변환은 범위 밖입니다. [제품 사양](docs/product-spec.md)을 확인하세요.

## Windows 실행 — Python 3.12 / Windows x64

저장소 루트에서 PowerShell로 실행합니다. 개발 중에는 인터넷이 패키지 설치에만 필요하며, 설치 후 앱은 오프라인으로 실행됩니다.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
.venv\Scripts\python.exe -m local_pdf_editor
```

페이지 번호는 1부터 시작합니다. `1,3-5`처럼 입력하거나 목록에서 선택 후 **Use selected pages**를 누릅니다. 재정렬은 모든 페이지를 한 번씩 포함하며, 목록을 드래그한 뒤 **Use displayed order**를 누릅니다. 가져오기는 첫 파일이 대상, 둘째 파일이 원본이고 `Insert after page = 0`은 맨 앞입니다. 분할은 선택한 페이지별 PDF를 만듭니다.

비율 유지 옵션은 지정한 너비·높이 안에 맞춥니다. 취소 전에 완성된 결과는 보존되며 목록에 표시됩니다.

## 검증 및 Windows 패키징

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts\package_app.py
dist\LocalPdfUtilities\LocalPdfUtilities.exe --smoke-test --heic-fixture tests\fixtures\sample.heic
```

`dist/LocalPdfUtilities/` 폴더 전체가 실행 패키지입니다. EXE만 복사하면 안 됩니다. Windows 패키지는 Windows에서 빌드해야 합니다. 서명·설치 프로그램은 포함하지 않습니다. 공개 배포 전 LGPL 소스/고지와 HEVC 배포 검토가 남아 있습니다: [라이선스 검토](docs/licenses/README.md).

Linux Cloud에서는 `.venv/bin/python`을 사용합니다. 테스트가 Qt offscreen 모드를 설정합니다.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m local_pdf_editor --smoke-test --heic-fixture tests/fixtures/sample.heic
```

Cloud 기능·offscreen GUI는 검증했지만 **실제 Windows GUI·패키지 실행 검증은 아직 하지 않았습니다.** [검증 기록 및 Windows 체크리스트](docs/verification.md)를 확인하세요.

## 프로젝트 문서

- [AGENTS.md](AGENTS.md), [search-first](.agents/skills/search-first/SKILL.md), [verification-loop](.agents/skills/verification-loop/SKILL.md)
- [제품 사양](docs/product-spec.md), [구현 계획](docs/implementation-plan.md), [현재 상태](docs/project-status.md), [구조](docs/architecture/current.md), [결정](docs/decisions/ADR-0001-m1-stack.md), [개발 기록](docs/development/development-log.md)

저장소 스킬이 기준입니다. 상태는 `PROPOSAL / DECISION / PLANNED / IMPLEMENTED / VERIFIED / BLOCKED / DEFERRED / SUPERSEDED`를 사용하며, 구현과 검증을 구분합니다.
