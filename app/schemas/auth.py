from pydantic import BaseModel


class ForgotPasswordRequest(BaseModel):
    identifier: str  # email or username


class ResetPasswordRequest(BaseModel):
    identifier: str  # email or username
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str
