from pydantic import BaseModel, EmailStr
from datetime import datetime


class HospitalResponse(BaseModel):
    id: int
    name: str
    address: str
    phone: str

    class Config:
        from_attributes = True


class PatientRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    age: int
    phone: str


class DoctorRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    specialization: str
    hospital_id: int
    experience: int
    qualification: str
    bio: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    age: int | None = None
    phone: str | None = None

    class Config:
        from_attributes = True


class DoctorResponse(BaseModel):
    id: int
    name: str
    specialization: str
    bio: str
    experience: int
    qualification: str
    hospital_id: int
    hospital_name: str

    class Config:
        from_attributes = True


class SlotResponse(BaseModel):
    id: int
    doctor_id: int
    doctor_name: str
    specialization: str
    hospital_name: str
    start_time: datetime
    is_booked: bool

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    slot_id: int
    patient_name: str
    patient_age: int
    patient_phone: str
    symptoms: str | None = None
    patient_id: int | None = None


class BookingResponse(BaseModel):
    id: int
    slot_id: int
    patient_id: int | None = None
    patient_name: str
    patient_age: int
    patient_phone: str
    symptoms: str | None = None

    class Config:
        from_attributes = True


class DoctorBookingResponse(BaseModel):
    booking_id: int
    patient_name: str
    patient_age: int
    patient_phone: str
    symptoms: str | None
    start_time: datetime