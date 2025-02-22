from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str
    is_remember: bool = False


class UserProfile(BaseModel):
    id: str
    email: str
    nickname: str
    profile_image_url: str
    role: str
    is_active: bool
    email_verified: bool


class RegisterSecurity(BaseModel):
    password: str
    confirm_password: str


class PASSIdentityInfo(BaseModel):
    pass_user_id: str
    name: str
    phone_number: str
    birthdate: str
    gender: str


class RegisterRequest(BaseModel):
    user_profile: UserProfile
    security: RegisterSecurity
    identity_pass: PASSIdentityInfo


class SocialRequest(BaseModel):
    social_id: str
    social_platform: str
    user_id: str
