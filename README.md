# LocalHub MVP — Gemini + 로컬 JSON 버전

실시간 서울시 Open API 호출을 제거한 안정적인 MVP입니다.

## 구성
- Vue 3: 챗봇, 실제 서울 자치구 GeoJSON 지도, 시설 조회, 커뮤니티
- FastAPI: Gemini 중계, 가중치 추천 계산, JSON 시설 조회, 메모리 게시판
- SQLite: 아직 미연결
- 시설 데이터: `backend/app/data/*.json`

> 지도 경계는 실제 서울 자치구 공개 GeoJSON을 브라우저에서 불러옵니다. 시설 데이터 조회는 외부 API 호출 없이 로컬 JSON으로 작동합니다.

## 1. Gemini 키 설정
`backend/.env.example`을 복사하여 `backend/.env`를 만들고 값을 입력합니다.

```env
GEMINI_API_KEY=실제키
GEMINI_MODEL=gemini-3.5-flash
```

## 2. Windows Git Bash 백엔드 실행
```bash
cd ~/Downloads/localhub-mvp/backend
py -3.11 -m venv venv
source venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`

## 3. 프론트 실행
새 터미널:
```bash
cd ~/Downloads/localhub-mvp/frontend
npm install
npm run dev
```

화면: `http://localhost:5173`

## JSON 교체 위치
- `childcare.json`
- `playgrounds.json`
- `hospitals.json`
- `schools.json`
- `culture_centers.json`
- `district_scores.json`

모든 시설 JSON 공통 필드:
```json
{
  "id": "hospital-11710-1",
  "type": "HOSPITAL",
  "name": "시설명",
  "district": "송파구",
  "address": "주소",
  "phone": "02-...",
  "category": "소아청소년과",
  "latitude": 37.5,
  "longitude": 127.1
}
```

실제 공공데이터를 내려받은 뒤 이 공통 필드로 변환해 같은 파일명으로 덮어쓰면 화면 코드는 수정하지 않아도 됩니다.
