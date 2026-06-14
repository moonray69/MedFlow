from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)

    doctors = relationship("Doctor", back_populates="hospital")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)

    age = Column(Integer, nullable=True)
    phone = Column(String, nullable=True)

    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)
    bookings = relationship("Booking", back_populates="patient")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)

    name = Column(String, nullable=False)
    specialization = Column(String, nullable=False)
    bio = Column(String, nullable=False)
    experience = Column(Integer, nullable=False)
    qualification = Column(String, nullable=False)

    user = relationship("User", back_populates="doctor_profile")
    hospital = relationship("Hospital", back_populates="doctors")
    slots = relationship("Slot", back_populates="doctor")


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)

    doctor = relationship("Doctor", back_populates="slots")
    booking = relationship("Booking", back_populates="slot", uselist=False)


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    patient_name = Column(String, nullable=False)
    patient_age = Column(Integer, nullable=False)
    patient_phone = Column(String, nullable=False)
    symptoms = Column(String, nullable=True)

    slot = relationship("Slot", back_populates="booking")
    patient = relationship("User", back_populates="bookings")