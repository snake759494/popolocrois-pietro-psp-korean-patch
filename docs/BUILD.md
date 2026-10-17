# 빌드 방법

번역 대본·원문은 저장소에 없으므로, 아래는 자신이 가진 원본과 번역 파일로 다시 빌드하는 절차입니다.

## 준비물
- 원본 ISO `PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Japan) (v2.01).iso` (MD5 `7cd263eb25237c7d73127315ffd08ed1`)
- Python 3.12+ : `pip install pillow numpy opencv-python imageio-ffmpeg websocket-client pycdlib capstone`
- 글꼴 `NanumSquareNeo-*.ttf`

## 폴더 구성
```
<작업 폴더>/
  PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Japan) (v2.01).iso
  NanumSquareNeo-*.ttf
  tools/   (이 저장소의 tools)
  trans/   out/*.json, speakers.json, telop/*.txt, boot_extra.json, movie_subs.json, fix.json  (번역 — 저장소 미포함)
  work/
```

## 순서
1. ISO 추출: `python tools/isoext.py "<원본.iso>" work/iso`
2. 메시지 블록: `python tools/msgdb.py` → `work/blocks.json`, `python tools/regioncheck.py` → `work/foreign.json`(문자열 영역에 다른 데이터가 섞인 오탐 블록, 빌드에서 제외), `python tools/extract.py` → `work/msg_src.json`, `work/msg_occ.json`
3. 실행 파일 문자열: `python tools/boot_extract.py` → `work/boot_src.json`
4. 번역 작성: `trans/out/NNN.json`, `trans/out/bootN.json` = `{id: 한국어}`, `trans/speakers.json`, `trans/telop/*.txt`
5. 그림 글자: `python tools/make_title.py`, `python tools/make_labels.py`, `python tools/make_wmap.py`, `python tools/make_chapcards.py`
6. 동영상: `python tools/movcues.py title_01 30 20 450 140`, `python tools/movie_title.py`, `python tools/movie_demo.py title_E1`, `python tools/movie_demo.py title_B1`
7. 빌드: `python tools/build.py` → `PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Korean).iso`
8. 차분: `xdelta3 -e -0 -s 원본.iso 한글.iso 패치.xdelta`

PPSSPP 원격 디버거로 자동 확인할 때는 `python tools/emu.py start <ISO>` / `shot` / `press` / `seq` 를 씁니다.
