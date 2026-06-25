# Slack arXiv Paper Digest Bot

매일 arXiv의 `cs.LG`, `cs.AI`, `stat.ML` 최신 논문을 가져오고, 관심 키워드로 랭킹한 뒤, 상위 논문에 대한 짧은 한국어 설명을 Gemini API로 생성하여 Slack DM으로 보내는 Python 봇입니다.

## 설치

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux에서는 가상환경 활성화 명령만 아래처럼 바꾸면 됩니다.

```bash
source .venv/bin/activate
```

## Gemini API Key 발급

1. Google AI Studio의 API key 페이지로 이동합니다: https://aistudio.google.com/app/apikey
2. Google 계정으로 로그인합니다.
3. `Create API key`를 눌러 새 키를 발급합니다.
4. 발급된 키를 `.env`의 `GEMINI_API_KEY`에 넣습니다.

Gemini API는 무료 티어와 쿼터 제한이 있을 수 있습니다. 요청이 많거나 무료 한도를 넘으면 API 호출이 실패할 수 있으며, 이 경우 봇은 fallback 설명을 사용하고 Slack 전송은 계속 시도합니다.

## .env 설정

`.env.example`을 참고해 `.env` 파일을 만듭니다.

```env
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_USER_ID=U0123456789
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
ARXIV_DELAY_SECONDS=15
ARXIV_NUM_RETRIES=6
```

필수 값은 `SLACK_BOT_TOKEN`, `SLACK_USER_ID`입니다. `GEMINI_API_KEY`가 비어 있거나 Gemini API 호출에 실패하면 간단한 fallback 설명으로 Slack 메시지를 보냅니다.

Slack 앱에는 DM 전송을 위해 보통 `chat:write`, `im:write` 권한이 필요합니다. 토큰과 API key는 코드에 하드코딩하지 말고 `.env`나 GitHub Secrets에만 저장하세요.

arXiv에서 HTTP 429가 나오면 잠시 rate limit에 걸린 상태입니다. 기본 설정은 요청 실패 시 15초 간격으로 6회 재시도합니다. 필요하면 `.env`에서 `ARXIV_DELAY_SECONDS`나 `ARXIV_NUM_RETRIES`를 더 크게 잡으세요.

## 실행

```bash
python main.py
```

실행 흐름은 다음과 같습니다.

1. arXiv에서 최신 논문 100개 수집
2. 키워드 점수로 정렬
3. 상위 3개 선택
4. Gemini API로 한국어 설명 생성
5. Slack DM 전송

## 간단한 테스트

의존성 설치 후 아래 명령을 실행합니다.

```bash
python main.py
```

Slack DM을 받으면 arXiv 수집, 랭킹, 메시지 전송은 성공입니다. `Field`, `Core Idea`, `Note`가 구체적인 한국어 설명으로 채워지면 Gemini 설명 생성까지 성공한 것입니다.

## GitHub Actions 예시

매일 오전 10시 KST는 UTC 기준 01시입니다. 이 저장소에는 `.github/workflows/daily-paper-digest.yml` 예시가 포함되어 있습니다.

```yaml
name: Daily Paper Digest

on:
  schedule:
    - cron: "0 1 * * *"
  workflow_dispatch:

jobs:
  send-digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Send digest
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_USER_ID: ${{ secrets.SLACK_USER_ID }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GEMINI_MODEL: gemini-2.5-flash
          ARXIV_DELAY_SECONDS: "30"
          ARXIV_NUM_RETRIES: "8"
        run: python main.py
```

## 파일 구조

- `main.py`: 전체 파이프라인 실행
- `config.py`: `.env` 로딩 및 설정 관리
- `arxiv_fetcher.py`: arXiv 최신 논문 수집
- `ranking.py`: 키워드 기반 점수 계산 및 정렬
- `llm_explainer.py`: Gemini API 기반 한국어 설명 생성
- `slack_sender.py`: Slack DM 메시지 구성 및 전송
