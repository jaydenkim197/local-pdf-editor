# local-pdf-editor

로컬 PDF 편집기 프로젝트입니다. 현재는 개발 baseline만 준비되어 있으며, 앱 코드·실행 명령·자동화 테스트는 아직 없습니다.

## Codex 개발 지침

- 프로젝트 지침: [AGENTS.md](AGENTS.md)
- 개발 전 탐색: [.agents/skills/search-first/SKILL.md](.agents/skills/search-first/SKILL.md)
- 변경 후 검증: [.agents/skills/verification-loop/SKILL.md](.agents/skills/verification-loop/SKILL.md)

저장소 안의 스킬을 기준으로 사용합니다. 두 스킬은 제공된 baseline ZIP의 원본을 그대로 복사했습니다. 개인/global 설치는 로컬 사용 시 선택 사항이며, Codex Cloud에서는 이 저장소 안의 복사본을 사용합니다.

## 프로젝트 기록

- [현재 상태](docs/project-status.md)
- [현재 구조](docs/architecture/current.md)
- [기술 결정](docs/decisions/README.md)
- [개발 기록](docs/development/development-log.md)

상태는 `PROPOSAL / DECISION / PLANNED / IMPLEMENTED / VERIFIED / BLOCKED / DEFERRED / SUPERSEDED`를 사용합니다. 결정, 구현, 검증은 별개입니다.

다음 단계는 PDF 편집기의 MVP 요구사항과 실행 플랫폼을 정한 뒤 첫 기능을 구현하는 것입니다. 현재 별도 패키지 설치나 서비스 시작은 필요하지 않습니다.
