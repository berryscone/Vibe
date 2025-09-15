# Authentication
- Google/Apple과 같은 Identity Provider(IdP)를 통해 사용자가 "누구" 인지 인증
- Single Sign-On(SSO) 사용

## Single Sign-On (SSO)
- Google/Apple 등의 신뢰할 수 있는 IdP의 계정을 이용해 여러가지 서비스를 이용

### Google & Apple & Kakao SSO 
- OAuth2 기반의 OpenID Connect (OIDC) 프로토콜 사용
- JWT id token 사용

### Naver SSO
- OAuth2

<br><br>

# Authorization
- 사용자가 어떤 "권한"이 있는지를 식별하고 허용/비허용을 결정 (인가)

## Resource Server (RS)
- 허용된 사용자에게만 리소스를 제공하는 서버
- REST API Server

## Authorization Server (AS)
- Authorization만 담당하는 서버
- Access/Refresh 토큰을 발급,갱신 한다

### Aceess Token (AT)
- Resource server의 인가에 사용되는 토큰으로 JWT 형식을 사용
- 짧은 갱신 주기를 가지는 토큰으로 다음과 같은 내용들을 가진다
- iat: issued at - 생성시간
- sub: subject - 누구에게 발급됐는지
- iss: issuer - 누가 발급했는지
- exp: expiration time - 언제까지 유효한지
- cnf: confirmation - proof-of-possession에 사용되는 키값
- 서버는 토큰이 공격자에 의해 탈취되었는지를 알 수 없기 때문에 최대한 짧은 유효시간을 사용해 피해를 최소화

### Refresh Token (RT)
- 상대적으로 긴 갱신 주기를 가지는 토큰으로 AT를 갱신할 때 사용
- AT가 만료된 경우 client는 사용자 개입 없이 RT를 이용해 AT를 갱신한다.
- 이런 방법을 통해 AT의 탈취 취약성을 보완면서도 사용자의 UX를 해치지 않는다.
- JWT 또는 Opaque형식을 사용
- Opaque 포맷을 사용하는 경우
    - 랜덤값을 사용하고 AT를 갱신할 때 RT도 함께 갱신
    - JWT와 다르게 토큰 자체로는 어떠한 정보도 얻을 수 없기 때문에 서버 스토리지에 user_id와 같은 다른 정보와 함께 저장
- 탈취여부를 확인하기 위해 보통 폐기된 RT도 DB에 일정시간동안 보관
- 폐기된 RT가 사용되면 해당 갱신된 RT를 포함해 전체 RT를 비활성화해서 피해를 최소화 한다
- 탈취 됐을때의 취약점을 보완하기 위해 RT를 저장할 때 IP주소나 device를 식별할 수 있는값을 함께 저장 가능
- 보안 취약점 해결을 위해 여러가지 방법들을 사용해도 결국 탈취되었을 때 사용자 정보가 털리는건 못막음
- DPoP을 사용해서 토큰을 발급받은 당사자만 사용하도록 할 수 있음

### JWT(JSON Web Token)
- JSON 형식을 가지는 토큰으로 self-contained 특징을 가진다
- 토큰에 필요한 정보와 서명이 있어서 서버는 stateless로 운영 가능 (DB에 access token 저장 불필요)
- header.claim.signature 포맷
- HS256같은 대칭키 알고리즘이나, RS256같은 비대칭키 알고리즘을 사용해서 서명 가능
- client가 로그인 하면 서명된 토큰을 제공하고 client는 인가가 필요한 리소스에 접근시 토큰을 제출
- server는 토큰의 서명을 검증해서 토큰의 내용이 변조되지 않았음을 확인

### DPoP (Demonstration Proof of Possession)
- OAuth 2.0 및 OIDC 보안을 강화하기 위한 메커니즘
- DPoP증명을 사용해 토큰의 소유자임을 증명
- DPoP증명
    - JWT 형식을 사용하며 header에 JWK(JSON Web Key) 형식으로 클라이언트의 공개키가 포함됨
    - payload에는 htm(HTTP Method), htu(HTTP URI) 등의 claim을 포함
    - signature는 클라이언트의 개인키를 이용해 서명
    - 모든 요청에 HTTP DPoP header로 전송
- 클라이언트가 토큰을 발급받을 때 비대칭키를 만들고 개인키로 서명된 DPoP증명을 서버에 전송
- 서버는 DPoP증명에 포함된 공개키를 이용해서 서명을 확인하고 AT의 payload에 해시된 공개키를 포함해서 발급 - 공개키를 AT에 바인딩
- 클라이언트는 모든 요청에 AT와 함께 개인키로 서명된 DPoP증명을 HTTP DPoP header로 함께 전송
- 서버는 서명된 DPoP증명을 헤더에 포함된 JWK를 이용해 검증하고 AT에 바인딩된 해시된 공개키가 DPoP에 포함된 공개키를 해싱한 값과 일치하는지 확인해서 요청자가 토큰의 소유자임을 증명
- 토큰의 소유를 비대칭키로 증명함으로서 토큰이 공격자에 의해 탈취되어도 클라이언트의 개인키가 노출되지 않으면 토큰을 사용하지 못함
- DPoP과 AT는 JWT포맷으로 서명되었으니 변조여부를 확인 가능하고 AT에 바인딩된 클라이언트의 공개키가 DPoP증명의 공개키와 일치하는지를 확인
    1. DPoP증명에 포함된 클라이언트의 공개키를 이용해 DPoP증명이 위조되지 않음을 확인
    2. AT에 바인딩된 공개키와 DPoP증명에 포함된 공개키가 일치하는지 확인
    3. 서버의 키를 이용해 AT가 위조되지 않았음을 확인
    4. DPoP증명과 AT모두 위조되지 않았음이 확인되었고 DPoP과 AT포함된 클라이언트의 공개키가 일치함을 확인했으니 리소스 요청자가 AT의 소유자임이 증명됨
    5. 클라이언트 또는 서버의 공개키가 탈취되지 않았다면 AT가 탈취되어도 공격자는 적합한 DPoP을 만들 수 없기 때문에 탈취한 토큰을 사용해도 서버에서 비인가 된다