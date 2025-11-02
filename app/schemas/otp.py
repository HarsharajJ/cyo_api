from pydantic import BaseModel, EmailStr


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str


class OTPResponse(BaseModel):
    message: str
    email: str
