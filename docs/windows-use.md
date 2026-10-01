# Windows 개발용 패키지 사용

## 다운로드와 실행

1. GitHub에 로그인하고 [Windows 검증 워크플로](https://github.com/jaydenkim197/local-pdf-editor/actions/workflows/verify.yml)를 엽니다.
2. 성공한 실행의 **Artifacts**에서 `LocalPdfUtilities-Windows-x64-커밋SHA`를 내려받습니다. 소스 테스트와 EXE 검사를 통과해야 이 패키지가 생성됩니다. 실패한 실행에는 정상 패키지가 없습니다.
3. 내려받은 아티팩트 압축을 풀고, 그 안의 `LocalPdfUtilities-Windows-x64.zip`도 풉니다.
4. `LocalPdfUtilities` 폴더 안의 **LocalPdfUtilities.exe**를 실행합니다. Python을 설치할 필요가 없습니다.

`_internal`, `THIRD_PARTY_NOTICES`, `LOCAL-ENGINES.md`를 포함한 폴더 전체를 보관하세요. EXE만 옮기면 실행에 필요한 DLL·글꼴·프로파일이 빠집니다. GitHub 개발용 아티팩트는 14일간 보관하며, 이후에는 워크플로를 다시 실행해 생성합니다.

ZIP의 SHA-256은 함께 제공되는 `.sha256` 파일에 있습니다. PowerShell의 `Get-FileHash .\LocalPdfUtilities-Windows-x64.zip -Algorithm SHA256` 결과와 비교할 수 있습니다.

## 파일 처리

도구를 고르고 파일을 추가한 뒤 옵션과 출력 폴더를 확인하고 실행합니다. 원본과 기존 결과를 덮어쓰지 않습니다. 작업이 끝나면 결과 파일 또는 폴더를 열 수 있습니다. 파일을 서버에 올리지 않으며 계정 없이 처리합니다.

보안 삭제는 지정한 영역만 제거합니다. 결과의 경계를 확인한 뒤 공유하세요. 소수점 페이지 크기의 이전 버전 결과는 수정된 버전으로 다시 생성해야 합니다. 자르기는 원본 내용 삭제가 아니며 서명 이미지는 인증서 서명이 아닙니다.

## OCR 준비

다른 기능은 앱 패키지로 실행하며, OCR은 **Tesseract 5와 언어 데이터·pdf.ttf를 따로 설치**해야 합니다. 한국어는 `kor`, 영어는 `eng`, 둘 다 쓰면 `eng+kor` 데이터가 필요합니다. 앱의 OCR 화면에서 엔진/데이터 폴더를 지정할 수 있습니다. 설치된 데이터는 오프라인으로 사용하며 앱이 다운로드하지 않습니다. [준비 절차](m3-engines.md)를 참고하세요.

## 검증 범위

성공한 워크플로는 Windows 소스 테스트, 빌드된 EXE의 한글 경로 이동, Python 없는 PATH, 인터넷 송신 차단, 기본 Windows 화면 백엔드의 100%/150% 배율과 영어·한국어 OCR 샘플을 검사합니다. 실행별 실제 결과는 [검증 기록](verification.md)에 남깁니다.

호스팅된 Windows 러너에는 Python과 시스템 구성요소가 설치돼 있습니다. Python 미설치 개인 PC, 실제 Explorer·대화상자·디스플레이와 모든 실사용 문서는 별도 확인이 필요합니다. 이 패키지는 미서명 개발용 빌드이며 설치 프로그램은 포함하지 않습니다. 공개 배포를 위한 라이선스 검토가 남아 있습니다.
