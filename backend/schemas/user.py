from pydantic import BaseModel, EmailStr


class RegisterForm(BaseModel):
    name: str
    surname: str
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    surname: str
    username: str
    email: EmailStr
