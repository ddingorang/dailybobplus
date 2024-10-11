# dailybobplus

- 슬랙 앱 관리 페이지 : https://api.slack.com/apps/

### Socket Mode
- 로컬 환경에서 개발할 때 사용하는 모드
- 슬랙 앱에서 이벤트 발생 시 로컬 주소로 request를 보냄
- request url을 지정할 필요가 없음
- 다만 배포 시에는 request url을 지정 필요

### ngrok
- 로컬 개발 환경에서 실행 중인 웹 서버를 외부에서 접근할 수 있도록 만들어주는 도구
- 외부 접근이 가능한 서버 주소를 만들어 줌
- ngrok.exe 실행하여 커맨드 입력
> ngrok http 3000
- 커맨드 실행 시마다 주소가 바뀜 -> Event Subscription에서 request url 변경 필요

### OAuth & Permissions
- Bot User OAuth Token 발급 필요 : 코드에 붙여 넣기
- 새로 발급 받을 때마다 reinstall 필요
- Bot Token Scopes
