import json

import uvicorn
from fastapi import FastAPI, Depends,  HTTPException, Security, APIRouter
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel

import jwt


ACCESS_TOKEN_EXPIRE_MINUTES = 30    # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7      # 7 days
ALGORITHM = "HS256"
JWT_SECRET_KEY = "xXıAhu1J31d10j91j01ASX9dj09UIROLjdAB1B9CDDx1902J1AsSmM124OdxWsxRTswM121"  # should be kept secret
JWT_REFRESH_SECRET_KEY = "xXıAhu1J31d10j91j01ASX9dj09UIROLjdAB1"  # should be kept secret


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
    scheme_name="JWT"
)

origins = [
    "http://localhost:8000",
]


users = []
cached_token = []


class AuthToken(BaseModel):
    token: str


class AuthDetails(BaseModel):
    email: str
    password: str


class AuthHandler:
    security = HTTPBearer()
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")
    secret = JWT_SECRET_KEY

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(secret=plain_password, hash=hashed_password)

    def encode_token(self, user_name):
        payload = {
            'exp': datetime.utcnow() + timedelta(days=0, minutes=5),
            'iat': datetime.utcnow(),
            'sub': user_name
        }
        return jwt.encode(
            payload,
            self.secret,
            algorithm='HS256'
        )

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError as e:
            print(e)
        except jwt.InvalidTokenError as e:
            print(e)

    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
        return self.decode_token(token=auth)


auth_handler = AuthHandler()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/register')
async def register(auth_details: AuthDetails):
    if not auth_details.email or not auth_details.password:
        raise HTTPException(status_code=400, detail='Username/password must be provided')

    hashed_password = auth_handler.get_password_hash(auth_details.password)
    dic = {
        'email': auth_details.email,
        'pwd': auth_details.password
        }
    users.append(dict(dic))
    token = AuthHandler()
    cached_token.append(token.encode_token(user_name=dic))

    return {"token": token.encode_token(user_name=dic)}


@app.post('/login')
async def login(auth_details: AuthToken):

    print(str(cached_token[0]))

    if not auth_details.token or not str(cached_token[0]) == str(auth_details.token):
        raise HTTPException(status_code=401, detail='Invalid token')
    return auth_details.token


@app.post('/unprotected')
async def unprotected(token: AuthToken):
    return {'token': token}


@app.post('/protected')
async def protected(username=Depends(auth_handler.auth_wrapper())):
    return {'email': username}


@app.get('/')
async def home():
    return {'auth_details': users}


if __name__ == "__main__":
    uvicorn.run(app=app)





