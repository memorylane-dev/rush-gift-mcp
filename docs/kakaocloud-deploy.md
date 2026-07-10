# 카카오클라우드 배포 가이드 (공모전 필수)

Agentic Player 10 공모전은 **카카오클라우드에 배포된 MCP 서버**만 정상 응모로
인정한다. 이 문서는 카카오클라우드 VM 하나에 이 서버를 올리는 전체 과정이다.

전체 그림:

```
[1] 카카오클라우드 가입 + 공모전 크레딧
[2] VM(가상 컴퓨터) 1대 생성 + 공인 IP
[3] 방화벽(보안 그룹)에서 80 포트 열기
[4] VM 접속 → Docker 설치 → 이 저장소 실행
[5] PlayMCP 콘솔에서 엔드포인트를 새 주소로 교체 → 재심사
```

---

## 1. 계정과 크레딧

1. https://kakaocloud.com 에서 회원가입 후 콘솔 접속.
2. **공모전 공지( b.kakao.com/views/PlayMCP/AGENTIC_PlAYER_10 )를 먼저 확인**할 것.
   참가자용 크레딧 쿠폰이나 지정된 리전/스펙 안내가 있으면 그것을 따른다.
3. 프로젝트를 하나 만든다 (이름 자유, 예: `rush-gift`).

## 2. VM 생성

콘솔에서 **Virtual Machine 생성**:

| 항목 | 값 |
|---|---|
| 이미지 | Ubuntu 22.04 (또는 24.04) |
| 사양 | 가장 작은 것으로 충분 (2 vCPU / 2~4GB) |
| 키페어 | **새로 생성 후 .pem 파일 다운로드** — 이 파일이 비밀번호 대신이다. 잃어버리면 접속 불가 |
| 공인 IP | **할당** (Public IP 연결) — 이 IP가 서버 주소가 된다 |

## 3. 보안 그룹 (방화벽)

VM에 연결된 보안 그룹의 **인바운드 규칙**에 추가:

| 프로토콜 | 포트 | 소스 | 용도 |
|---|---|---|---|
| TCP | 22 | 내 IP (권장) | SSH 접속용 |
| TCP | 80 | 0.0.0.0/0 | MCP 서버 (PlayMCP가 접속) |

## 4. 서버 실행

내 컴퓨터 터미널에서 VM에 접속한다 (`<공인IP>`와 pem 경로는 본인 것으로):

```bash
chmod 400 ~/Downloads/키페어.pem
ssh -i ~/Downloads/키페어.pem ubuntu@<공인IP>
```

접속한 VM 안에서 아래를 순서대로 실행:

```bash
# Docker 설치
curl -fsSL https://get.docker.com | sudo sh

# 저장소 받기 + 이미지 빌드
git clone https://github.com/memorylane-dev/rush-gift-mcp.git
cd rush-gift-mcp
sudo docker build -t rush-gift-mcp .

# 실행 (TMAP_APP_KEY는 실제 키로 교체)
sudo docker run -d --name rush-gift --restart unless-stopped \
  -p 80:8000 \
  -e MCP_STATELESS_HTTP=true \
  -e RUSH_GIFT_PLACE_PROVIDER=tmap \
  -e RUSH_GIFT_ROUTE_PROVIDER=tmap \
  -e RUSH_GIFT_STORE_PROVIDER=tmap \
  -e TMAP_APP_KEY=여기에_실제_키 \
  rush-gift-mcp

# 확인 — {"status":"ok", ...} 가 나오면 성공
curl http://localhost/health
```

내 컴퓨터에서도 확인:

```bash
curl http://<공인IP>/health
```

## 5. PlayMCP 엔드포인트 교체

PlayMCP 개발자 콘솔 → 등록한 MCP → 엔드포인트를 다음으로 변경:

```
http://<공인IP>/mcp
```

**"정보 불러오기"**로 툴 4개가 보이는지 확인한 뒤 재심사를 제출한다.

---

## 코드 업데이트 방법

로컬에서 `git push` 후, VM에서:

```bash
cd ~/rush-gift-mcp && git pull
sudo docker build -t rush-gift-mcp .
sudo docker rm -f rush-gift && sudo docker run -d --name rush-gift --restart unless-stopped \
  -p 80:8000 \
  -e MCP_STATELESS_HTTP=true \
  -e RUSH_GIFT_PLACE_PROVIDER=tmap \
  -e RUSH_GIFT_ROUTE_PROVIDER=tmap \
  -e RUSH_GIFT_STORE_PROVIDER=tmap \
  -e TMAP_APP_KEY=여기에_실제_키 \
  rush-gift-mcp
```

## 문제 해결

| 증상 | 확인할 것 |
|---|---|
| `curl http://<공인IP>/health` 무응답 | 보안 그룹 80 포트 인바운드, 공인 IP 연결 여부 |
| 컨테이너가 바로 죽음 | `sudo docker logs rush-gift` — env 오타면 시작 시 명확한 에러가 찍힘 (fail fast) |
| 정보 불러오기 실패 | 엔드포인트 끝이 `/mcp`인지, `http://`인지 확인 |
| TMAP 호출 실패 | `TMAP_APP_KEY` 값 확인 (`sudo docker exec rush-gift env \| grep TMAP`) |

## 참고

- Vercel 배포(`rush-gift-mcp.vercel.app`)는 그대로 두어도 된다 — 개발/테스트용으로
  유지하고, 공모전 접수 엔드포인트만 카카오클라우드 주소를 쓰면 된다.
- HTTPS가 필요해지면(심사 요건 변경 등) 도메인 연결 후 Caddy 컨테이너를 앞에
  붙이는 방법이 가장 간단하다. 필요할 때 진행.
