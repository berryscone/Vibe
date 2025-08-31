https://blog.naver.com/mds_datasecurity/222182943542


# Google OAuth2와 Server에서 발행하는 JWT token & refresh token(RT)을 이용한 인증 방법

1. Client는 client_secret.json 파일에 있는 정보를 이용해서 구글서버로 부터 id_token을 획득
    a. google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file 메소드 사용
    b. (a)함수가 리턴하는 오브젝트의 run_local_server 메소드를 사용해서 토큰 정보를 획득

2. Client는 획득한 id_token을 이용해 API 서버에서 사용자인증을 획득
    a. API 서버에서 제공하는 인증 API에 id_token을 전송
    b. API 서버는 client가 보낸 id_token을 구글서버를 통해 검증
        - google.oauth2.id_token.verify_oauth2_token 메소드 사용
    c. 검증에 성공하면 사용자 정보를 획득

3. API 서버는 인증에 성공한 사용자 정보를 이용해 자체 JWT 토큰을 client에 발행
    - short period로 사용 가능한 JWT 토큰 발행
    - long period로 사용 가능한 refresh 토큰 발행 (이하 RT)
    - 토큰이 만료되면 client는 RT를 이용해 API 서버의 refresh endpoint를 이용해 새로운 토큰을 발급요청
    - API 서버는 refresh 요청을 받으면 아래 사항들을 확인
        a. 만료 날짜가 지나지 않았는지
        b. 비활성 기간이 지정된 기간보다 길지 않은지
        c. (per device 토큰 사용을 위해) fingerprint 확인
        d. rate limit 확인
        e. 만료되어 갱신된 토큰여부 확인
            - 만료된 토큰이 사용되는건 강력한 탈취시그널로 해당 만료된 토큰을이용해 갱신된 모든 토큰을 비활성화
            - 이를 위해 토큰 갱신 시 만료된 토큰에 갱신된 토큰정보의 link를 저장
    - refresh 토큰 발행시 저장해야 할 정보
        a. RT의 hash값
        b. 상태 - 활성, 비활성, 만료 등
        c. fingerprint of the client device
        d. RT의 만료날짜
        e. RT의 마지막 활성화 날짜
        f. 이전, 다음 RT들의 ID

## Refresh Token 사용 이유
- 인증토큰에 짧은 lifetime을 부여함으로서 토큰 탈취의 위험도를 최소화
- 짧은 lifetime의 인증토큰을 사용하면서도 사용자가 자주 재 인증 하는 불편함을 최소화