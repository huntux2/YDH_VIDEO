# 다른 PC에서 홍보 영상 이어서 제작하기 (원격 연동 및 제작 완벽 가이드)

이 문서는 **다른 PC(집, 사무실, 노트북 등)에서 원격 저장소(GitHub)를 받아 오늘과 100% 동일한 룰과 품질로 글로벌 홍보 영상을 바로 제작**할 수 있도록 정리한 올인원 가이드입니다.

---

## 1. 다른 PC에서 처음 세팅하는 방법 (1분 완료)

### 1단계: 원격 저장소(GitHub) 복제하기 (`git clone`)
다른 PC의 작업 폴더(예: `D:\AI-Antigravity\autonomous` 또는 원하는 경로)에서 아래 명령어로 `YDH_VIDEO` 저장소를 내려받습니다.

```powershell
git clone https://github.com/huntux2/YDH_VIDEO.git
```

> **팁 (Antigravity 전역 룰 자동 적용)**:
> Antigravity가 프로젝트 최상위 루트에서도 동일한 룰을 읽을 수 있도록, 내려받은 `YDH_VIDEO\GEMINI.md` 파일을 상위 워크스페이스 루트 폴더에도 복사해 두거나 `YDH_VIDEO` 폴더를 워크스페이스로 열면 모든 제작 룰이 즉시 자동 적용됩니다.

### 2단계: 파이썬 필수 패키지 설치 (최초 1회)
렌더링 스크립트 실행에 필요한 패키지는 단 2개(`Pillow`, `imageio-ffmpeg`)뿐입니다. 별도의 FFmpeg 설치 없이도 자동으로 내장 FFmpeg 바이너리를 사용합니다.

```powershell
pip install Pillow imageio-ffmpeg
```

---

## 2. 매일 새 영상 제작 및 원격 동기화 루틴

### A. 다른 PC에서 작업 시작 전 (최신 상태 받기)
```powershell
cd YDH_VIDEO
git pull
```

### B. AI(Antigravity)에게 오늘 영상 요청하기
채팅창에 아래처럼 한 줄만 입력하면 됩니다:
- **"오늘 날짜(`YYYY-MM-DD`)로 룰에 맞춰서 새 터치 타이밍 홍보 영상이랑 업로드 가이드 세트 만들어줘"**

### C. 작업 완료 후 원격에 올리기 (다른 곳에서도 볼 수 있게 저장)
AI에게 **"원격에 커밋하고 푸시해줘"**라고 말하거나 아래 명령어를 실행합니다:
```powershell
git add .
git commit -m "feat(video): YYYY-MM-DD 글로벌 터치 타이밍 홍보 영상 및 업로드 가이드 추가"
git push
```

---

## 3. 폴더 및 파일 구조 (100% 독립형 구조)

어떤 PC의 어느 드라이브(`C:\`, `D:\`)에 받아도 경로 오류 없이 즉시 실행되도록 모든 공용 아이콘과 스티커 에셋이 `assets/` 폴더 안에 내장되어 있으며, 모든 파이썬 스크립트는 **상대 경로(`os.path.dirname(__file__)`)** 기준으로 동작합니다.

```text
YDH_VIDEO/
├── GEMINI.md                       # [핵심] AI 홍보 영상 제작 7대 절대 룰
├── VIDEO_PRODUCTION_GUIDE.md       # [본 문서] 다른 PC 원격 세팅 및 제작 가이드
├── MARKETING_PLAN.md               # 글로벌 숏폼 홍보 마스터 플랜 및 로드맵
├── assets/                         # 모든 영상 제작용 공용 그래픽 에셋 (100% 내장)
│   ├── 01_App_Icon_512x512.png     # Autonomous 기어 앱 아이콘
│   ├── sticker_tired_finger.png    # 장면 1용 아픈 손가락 캐릭터 스티커
│   ├── sticker_chill_robot.png     # 장면 4용 선글라스 로봇 캐릭터 스티커
│   ├── mythic_loot_chest.jpg       # 보스 클리어 전설 보상 상자 에셋
│   ├── rpg_boss_scene.jpg          # Ep01 RPG 보스전 배경 에셋
│   └── timing_strike_scene.jpg     # Ep02 0.01초 퍼펙트 터치 타이밍 배경 에셋
├── scripts/                        # 파이썬 1080p MP4 렌더링 스크립트 모음 (상대 경로 기반)
│   ├── render_ep01_rpg_potion_en.py
│   └── render_ep02_precision_timing_en.py
├── 2026-10-14/                     # 날짜별 완료 산출물 폴더 (5종 세트)
└── 2026-10-15/                     # 날짜별 완료 산출물 폴더 (5종 세트)
    ├── Macro_Ep02_Perfect_Touch_Timing_Pixel_Macro_EN_1080p.mp4
    ├── 00_한글_영상가이드.txt
    ├── 01_youtube_upload.txt
    ├── 02_tiktok_upload.txt
    └── 03_instagram_upload.txt
```

---

## 4. 홍보 영상 제작 7대 핵심 룰 요약 (`GEMINI.md` 동기화)

1. **최우선 제작 주제 — 정밀 터치 타이밍 포착 (`Precision Touch Timing`)**:
   - 빠르게 움직이는 타이밍 게이지 바(`MISS` — `GOOD` — `PERFECT` — `GOOD` — `MISS`)에서 바늘이 `PERFECT` 구간에 들어오는 **0.01초의 순간을 픽셀 색상 감지로 포착해 터치하는 영상**을 주력으로 제작합니다.
   - 이전 에피소드와 소재가 겹치지 않도록 매일 새로운 정밀 타이밍 게임 상황(대장간 명검 단조 타이밍, 골프/야구 홈런 임팩트 바, 보스 필살기 0.01초 패링/반격 타이밍, 요리/채광 퍼펙트 구간 등)을 선정합니다.
2. **도박 · 사행성 · 확률형 뽑기(가챠) 절대 제작 금지**:
   - 카지노, 슬롯, 룰렛, 베팅뿐만 아니라 가챠(Gacha), 리세마라(Reroll), 확률 강화 등 사행성 요소는 일절 제작하지 않습니다.
3. **인과관계 3단계 애니메이션 필수 준수**:
   - 반드시 **`1. 실제 게이지/타이밍 바 위에서 픽셀 색상 감지(11배 돋보기 조준) → 2. 타겟 버튼 먼저 클릭(1st: CLICK!) → 3. 버튼 클릭 직후 파워/체력 게이지 상승(2nd: GAUGE RISES!) 및 성공 연출`** 순서로 구현합니다.
4. **하단 HUD 클린 패널 & UI 겹침 제로(Zero-Overlap) 검수**:
   - 배경 에셋의 하단 32%는 글자 없는 깔끔한 빈 대시보드 패널로 생성하고, 파이썬에서 움직이는 타이밍 바와 버튼을 직접 선명하게 그립니다.
   - 렌더링 후 반드시 `view_file`로 영상을 열람해 배지나 말풍선이 게이지 바와 단 1픽셀도 겹치지 않는지 확인합니다.
5. **글로벌 플랫폼 및 각국 법규 위반 키워드·기호 100% 배제**:
   - 제목·설명·태그·해시태그·자막 어디에도 **`hack`, `hacks` (`#gaminghacks`, `#gamerhacks`), `cheat`, `exploit`, `mod`, `bot`** 등 불법 프로그램으로 오인될 단어를 절대 쓰지 않습니다.
   - 대신 **`#touchassistant`, `#smartautoclicker`, `#gamingtips`, `#androidtips`, `official Android Accessibility Service`, `no root`** 등 합법 접근성 유틸리티 키워드만 사용합니다.
   - 유튜브 스튜디오에서 차단되는 꺾쇠괄호(`<`, `>`)는 일절 쓰지 않고 `→` 기호를 사용합니다.
6. **앱 아이콘(`Autonomous`) & 구글 플레이 공식 앱 이름(`Macro`) 통일**:
   - 엔드카드(`15.0s ~ 18.0s`)와 업로드 문서 전체에서 공식 스토어 등록명인 **`Macro`**(`Search [ Macro ] on Google Play!`)로 표기합니다.
7. **일일 산출물 5종 세트 필수 생성**:
   - 날짜별 폴더(`YYYY-MM-DD`) 안에 하위 폴더 구분 없이 **`MP4 영상 1개 + 00_한글_영상가이드.txt + 01_youtube_upload.txt + 02_tiktok_upload.txt + 03_instagram_upload.txt`** 총 5개 파일을 세트로 생성합니다.
