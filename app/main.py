import os
import hashlib
import datetime

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import engine, Base, get_db
from app.models import Hospital, User, Doctor, Slot, Booking
from app.schemas import (
    HospitalResponse,
    PatientRegister,
    DoctorRegister,
    LoginRequest,
    UserResponse,
    DoctorResponse,
    SlotResponse,
    BookingCreate,
    BookingResponse,
    DoctorBookingResponse
)


app = FastAPI(title="MedFlow API", description="Система первинного медичного маршруту пацієнта")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(CURRENT_DIR, "static")), name="static")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def render_template(file_name: str) -> HTMLResponse:
    path = os.path.join(CURRENT_DIR, "templates", file_name)

    with open(path, "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read(), status_code=200)


def build_default_slots(doctor_id: int) -> list[Slot]:
    now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)

    return [
        Slot(doctor_id=doctor_id, start_time=now.replace(hour=9), is_booked=False),
        Slot(doctor_id=doctor_id, start_time=now.replace(hour=10), is_booked=False),
        Slot(doctor_id=doctor_id, start_time=now.replace(hour=11), is_booked=False),
        Slot(doctor_id=doctor_id, start_time=now.replace(hour=14), is_booked=False)
    ]


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        hospitals_result = await session.execute(select(Hospital))
        existing_hospitals = hospitals_result.scalars().all()

        if not existing_hospitals:
            hospitals = [
                Hospital(name="Міська клінічна лікарня №1", address="м. Київ, вул. Центральна, 12", phone="+380441112233"),
                Hospital(name="Дитяча поліклініка MedChild", address="м. Київ, вул. Здоров'я, 7", phone="+380442223344"),
                Hospital(name="Сімейна амбулаторія MedFamily", address="м. Київ, просп. Медичний, 25", phone="+380443334455")
            ]

            session.add_all(hospitals)
            await session.flush()

            doctors = [
                Doctor(hospital_id=hospitals[0].id, name="Коваленко Іван Петрович", specialization="Терапевт", bio="Проводить первинний огляд дорослих пацієнтів, оцінює симптоми та визначає подальший маршрут лікування.", experience=12, qualification="Лікар вищої категорії"),
                Doctor(hospital_id=hospitals[1].id, name="Бондаренко Анна Сергіївна", specialization="Педіатр", bio="Проводить первинний прийом дітей, оцінює стан дитини та надає рекомендації батькам.", experience=9, qualification="Педіатр першої категорії"),
                Doctor(hospital_id=hospitals[2].id, name="Гриценко Максим Олександрович", specialization="Сімейний лікар", bio="Працює з пацієнтами різного віку, проводить первинну консультацію та супровід сімей.", experience=7, qualification="Сімейний лікар")
            ]

            session.add_all(doctors)
            await session.flush()

            slots = []
            for doctor in doctors:
                slots.extend(build_default_slots(doctor.id))

            session.add_all(slots)
            await session.commit()

            print("Демо-дані створено: лікарні, лікарі первинної ланки та слоти.")


@app.get("/", response_class=HTMLResponse)
async def read_landing():
    return render_template("landing.html")


@app.get("/app", response_class=HTMLResponse)
async def read_app():
    return render_template("index.html")


@app.get("/patient", response_class=HTMLResponse)
async def read_patient_page():
    return render_template("patient.html")


@app.get("/doctor", response_class=HTMLResponse)
async def read_doctor_page():
    return render_template("doctor.html")


@app.get("/family-doctor", response_class=HTMLResponse)
async def read_family_doctor_page():
    return render_template("family_doctor.html")


@app.get("/hospitals", response_model=list[HospitalResponse])
async def get_hospitals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hospital).order_by(Hospital.id))
    return result.scalars().all()


@app.post("/register/patient", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_patient(data: PatientRegister, db: AsyncSession = Depends(get_db)):
    existing_result = await db.execute(select(User).where(User.email == data.email))
    existing_user = existing_result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Користувач з таким email вже існує")

    user = User(full_name=data.full_name, email=data.email, password_hash=hash_password(data.password), role="patient", age=data.age, phone=data.phone)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@app.post("/register/doctor", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_doctor(data: DoctorRegister, db: AsyncSession = Depends(get_db)):
    existing_result = await db.execute(select(User).where(User.email == data.email))
    existing_user = existing_result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Користувач з таким email вже існує")

    hospital_result = await db.execute(select(Hospital).where(Hospital.id == data.hospital_id))
    hospital = hospital_result.scalar_one_or_none()

    if not hospital:
        raise HTTPException(status_code=404, detail="Лікарню не знайдено")

    user = User(full_name=data.full_name, email=data.email, password_hash=hash_password(data.password), role="doctor")

    db.add(user)
    await db.flush()

    doctor = Doctor(user_id=user.id, hospital_id=data.hospital_id, name=data.full_name, specialization=data.specialization, bio=data.bio, experience=data.experience, qualification=data.qualification)

    db.add(doctor)
    await db.flush()

    db.add_all(build_default_slots(doctor.id))

    await db.commit()
    await db.refresh(user)

    return user


@app.post("/login", response_model=UserResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Невірний email або пароль")

    return user


@app.get("/users/{user_id}/doctor-profile", response_model=DoctorResponse)
async def get_doctor_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Doctor, Hospital.name)
        .join(Hospital, Doctor.hospital_id == Hospital.id)
        .where(Doctor.user_id == user_id)
    )

    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Профіль лікаря не знайдено")

    doctor, hospital_name = row

    return DoctorResponse(id=doctor.id, name=doctor.name, specialization=doctor.specialization, bio=doctor.bio, experience=doctor.experience, qualification=doctor.qualification, hospital_id=doctor.hospital_id, hospital_name=hospital_name)


@app.get("/doctors", response_model=list[DoctorResponse])
async def get_primary_doctors(age: int | None = None, db: AsyncSession = Depends(get_db)):
    allowed_specializations = ["Терапевт", "Педіатр", "Сімейний лікар"]

    if age is not None:
        allowed_specializations = ["Педіатр", "Сімейний лікар"] if age < 18 else ["Терапевт", "Сімейний лікар"]

    result = await db.execute(
        select(Doctor, Hospital.name)
        .join(Hospital, Doctor.hospital_id == Hospital.id)
        .where(Doctor.specialization.in_(allowed_specializations))
        .order_by(Doctor.id)
    )

    rows = result.all()

    return [
        DoctorResponse(id=doctor.id, name=doctor.name, specialization=doctor.specialization, bio=doctor.bio, experience=doctor.experience, qualification=doctor.qualification, hospital_id=doctor.hospital_id, hospital_name=hospital_name)
        for doctor, hospital_name in rows
    ]


@app.get("/doctors/{doctor_id}/slots", response_model=list[SlotResponse])
async def get_slots(doctor_id: int, db: AsyncSession = Depends(get_db)):
    doctor_result = await db.execute(
        select(Doctor, Hospital.name)
        .join(Hospital, Doctor.hospital_id == Hospital.id)
        .where(Doctor.id == doctor_id)
    )

    doctor_row = doctor_result.first()

    if not doctor_row:
        raise HTTPException(status_code=404, detail="Лікаря не знайдено")

    doctor, hospital_name = doctor_row

    slots_result = await db.execute(select(Slot).where(Slot.doctor_id == doctor_id).order_by(Slot.start_time))
    slots = slots_result.scalars().all()

    if not slots:
        db.add_all(build_default_slots(doctor_id))
        await db.commit()

        slots_result = await db.execute(select(Slot).where(Slot.doctor_id == doctor_id).order_by(Slot.start_time))
        slots = slots_result.scalars().all()

    return [
        SlotResponse(id=slot.id, doctor_id=slot.doctor_id, doctor_name=doctor.name, specialization=doctor.specialization, hospital_name=hospital_name, start_time=slot.start_time, is_booked=slot.is_booked)
        for slot in slots
    ]


@app.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(booking_data: BookingCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Slot).where(Slot.id == booking_data.slot_id).with_for_update())
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(status_code=404, detail="Слот не знайдено")

    if slot.is_booked:
        raise HTTPException(status_code=400, detail="Цей слот вже заброньовано")

    doctor_result = await db.execute(select(Doctor).where(Doctor.id == slot.doctor_id))
    doctor = doctor_result.scalar_one_or_none()

    if not doctor:
        raise HTTPException(status_code=404, detail="Лікаря не знайдено")

    allowed = ["Педіатр", "Сімейний лікар"] if booking_data.patient_age < 18 else ["Терапевт", "Сімейний лікар"]

    if doctor.specialization not in allowed:
        raise HTTPException(status_code=400, detail="Обраний лікар не підходить для віку пацієнта")

    booking = Booking(slot_id=booking_data.slot_id, patient_id=booking_data.patient_id, patient_name=booking_data.patient_name, patient_age=booking_data.patient_age, patient_phone=booking_data.patient_phone, symptoms=booking_data.symptoms)

    db.add(booking)
    slot.is_booked = True

    await db.commit()
    await db.refresh(booking)

    return booking


@app.get("/patients/{patient_id}/bookings", response_model=list[DoctorBookingResponse])
async def get_patient_bookings(patient_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Booking, Slot.start_time)
        .join(Slot, Booking.slot_id == Slot.id)
        .where(Booking.patient_id == patient_id)
        .order_by(Slot.start_time)
    )

    rows = result.all()

    return [
        DoctorBookingResponse(booking_id=booking.id, patient_name=booking.patient_name, patient_age=booking.patient_age, patient_phone=booking.patient_phone, symptoms=booking.symptoms, start_time=start_time)
        for booking, start_time in rows
    ]


@app.get("/doctors/{doctor_id}/bookings", response_model=list[DoctorBookingResponse])
async def get_doctor_bookings(doctor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Booking, Slot.start_time)
        .join(Slot, Booking.slot_id == Slot.id)
        .where(Slot.doctor_id == doctor_id)
        .order_by(Slot.start_time)
    )

    rows = result.all()

    return [
        DoctorBookingResponse(booking_id=booking.id, patient_name=booking.patient_name, patient_age=booking.patient_age, patient_phone=booking.patient_phone, symptoms=booking.symptoms, start_time=start_time)
        for booking, start_time in rows
    ]