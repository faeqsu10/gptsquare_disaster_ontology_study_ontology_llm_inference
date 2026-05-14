# 산불 PoC 시연용 미니 웹

5주차 스터디 발표(2026-05-13)에서 시연 1~4를 한 화면으로 보여주기 위한 미니 웹.

기존 `study/wildfire-poc/` 백엔드를 그대로 호출만 합니다 (코드 무수정).

## 구성

```
demo/
├── server.py            FastAPI + SSE 엔드포인트
├── runner.py            subprocess 스트리밍 + 녹화/재생
├── chat_oneshot.py      chat.py를 1회 호출용으로 감싼 진입점
├── run_demo.sh          기동 스크립트 (LD_LIBRARY_PATH 주입)
├── static/              index.html + style.css + app.js
└── recordings/          라이브 실행 시 자동 저장되는 JSONL 녹화본
```

## 기동

```bash
./study/wildfire-poc/demo/run_demo.sh
# 브라우저에서 http://127.0.0.1:8765 열기
```

포트 변경: `DEMO_PORT=9000 ./study/wildfire-poc/demo/run_demo.sh`

## 모드

화면 우상단 토글로 전환합니다.

- **실시간 실행** — `./run.sh ...`를 그대로 subprocess로 호출. 출력이 라인 단위로 SSE 스트리밍됩니다. 매 실행마다 `recordings/{demo_key}_latest.jsonl` 갱신.
- **녹화 재생** — 가장 최근 녹화본을 원본 페이스대로 재생. 라이브가 실패하거나 네트워크 문제가 있을 때 fallback.

## 발표 직전 체크리스트

- [ ] TypeDB 컨테이너 실행 중 (`docker ps | grep typedb`)
- [ ] `.env`에 `GEMINI_API_KEY` 설정됨
- [ ] 시연 1·2·4 라이브로 한 번씩 실행 → `recordings/`에 최신 녹화본 생성
- [ ] 시연 3 채팅 3건(여수 상암동 / MOCK / 1990 광주 동구) 라이브로 1회씩 실행
- [ ] 브라우저 폰트 크기 (Ctrl + 휠로 110~125%)
- [ ] 발표용 외부 모니터에 전체화면

## 시연 매핑

| 카드 | 호출 대상 | 녹화 키 |
|---|---|---|
| 시연 ① | `inference/run_inference_demo.py` | `demo1_inference` |
| 시연 ② | `tests/test_param_externalization.py` | `demo2_policy` |
| 시연 ③ | `demo/chat_oneshot.py --query <질문>` | `demo3_chat` |
| 시연 ④ | `llm/eval/run_eval.py` | `demo4_eval` |

시연 ④는 stdout 라인을 파싱해 카운터 카드(한 번에 성공 / 자가 수정 / 예비 답안 / 거절·실패)를 라이브로 채웁니다.
