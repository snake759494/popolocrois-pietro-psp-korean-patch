# 포포로크로이스 이야기 ~피에트로 왕자의 모험~ (PSP) 비공식 한글패치

PSP 일본판 **ポポロクロイス物語 ～ピエトロ王子の冒険～ (UCJS-10005, v2.01)** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·일본어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `.iso`** 를 준비합니다. (CSO·CHD 등으로 변환한 이미지에는 적용할 수 없습니다.)
   - PowerShell: `Get-FileHash -Algorithm MD5 -LiteralPath '.\PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Japan) (v2.01).iso'`
2. xdeltaUI 같은 도구로 원본 `.iso` 에 `PoPoLoCrois_Pietro_Ouji_no_Bouken_KO_v1.0.2.xdelta` 를 적용합니다. (Patch = xdelta, Source File = 원본 ISO, Output File = 새 파일명)
   - 명령줄: `xdelta3 -d -s "PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Japan) (v2.01).iso" PoPoLoCrois_Pietro_Ouji_no_Bouken_KO_v1.0.2.xdelta "PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Korean).iso"`
3. 만들어진 ISO를 PPSSPP 또는 커스텀 펌웨어에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 ISO 크기 | 1,168,572,416 바이트 |
| 원본 ISO MD5 | `7cd263eb25237c7d73127315ffd08ed1` |
| 원본 ISO SHA-256 | `8255ed48eeeaf198a538b24486cfd327ccb346646c0efdb1c70450e8863cd068` |
| xdelta SHA-256 | `dad1aefd28800ff18f99527bb9316b5c9af4e326fd345696dc13a1ab61fa3479` |
| 결과 ISO 크기 | 1,168,572,416 바이트 |
| 결과 ISO SHA-256 | `bfaa9a014447e4acee9a4f5cc9ec3d5b0742dbeaa80d1179045e3fee8bff3d50` |

## 주의
- 복호화한 실행 파일(BOOT.BIN)을 EBOOT로 넣었기 때문에 **PPSSPP·커스텀 펌웨어 전용**입니다. 정품 펌웨어에서는 부팅되지 않습니다.
- 다른 버전 패치나 원본에서 만든 **상태저장(세이브 스테이트)** 은 불러오지 마세요. 메모리에 이전 데이터가 남아 화면이 깨질 수 있습니다. 일반 세이브는 그대로 쓸 수 있습니다.

## 한글화 내용
- 이벤트·마을·필드 대사 전체: 고유 문장 21,083개(화자 이름 184개 포함), 스크립트에 직접 들어 있는 문장 22곳
- 실행 파일 문자열 2,119개(여관·상점 안내 포함): 메뉴, 아이템·장비·기술·몬스터 이름과 설명, 지명, 시스템 메시지, 전투 튜토리얼 문구
- 세이브 데이터 표시 문자열(UTF-8) 88개(장 제목·저장 장소), XMB 게임 제목
- 애니메이션 이벤트 자막 31개 파일과 스태프롤
- 그림 글자: 타이틀 로고, 장 제목 카드 12장, 월드맵 지방 이름 판 15개·장소 이름 56개, 카드 미니게임 이름 라벨
- 동영상: 타이틀 대기 오프닝 내레이션·원작자 메시지, 데모 영상 2개의 로고·대화창·배너를 한글로 다시 그려 재인코딩
- 글꼴: 게임 폰트 3종(kanji12·jk18_020·menu24)에 나눔스퀘어네오 ExtraBold로 한글 1,351자 배치

## 그대로 둔 것
- 이벤트 애니메이션 속 영어 장식 문구(PopoloCrois History 등), 제작사 로고
- 데모 영상 첫 장면 이름표의 일부 흔적, 지도 지방 이름 판 2개의 작은 얼룩

## 검증 범위
PPSSPP(1.17·1.20)에서 오프닝 영상, 타이틀, 새 게임 시작, 첫 이벤트 애니메이션, 초반 대화, 데모 영상까지 확인했습니다. 전체 플레이 검증은 하지 않았습니다. 문제를 발견하면 Issues에 알려 주세요.

## 문서
- [CHANGELOG.md](CHANGELOG.md) — 변경 기록
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — 파일 형식과 한글화 방법
- [docs/BUILD.md](docs/BUILD.md) — 직접 빌드하는 방법
- [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md) — 글꼴
- [RIGHTS.md](RIGHTS.md) — 권리 및 외부 자료
