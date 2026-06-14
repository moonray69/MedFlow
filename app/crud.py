import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app import models, schemas


# ==========================================
# 🩺 ЛОГІКА ДЛЯ ЛІКАРІВ ТА СЛОТІВ


async def create_doctor(db: AsyncSession, doctor: schemas.DoctorCreate):
    db_doctor = models.Doctor(name=doctor.name, specialization=doctor.specialization)
    db.add(db_doctor)
    await db.commit()
    await db.refresh(db_doctor)
    return db_doctor


async def get_active_slots(db: AsyncSession, doctor_id: int):
    # Беремо тільки ті слоти лікаря, які ще НЕ заброньовані
    result = await db.execute(
        select(models.Slot).where(
            models.Slot.doctor_id == doctor_id,
            models.Slot.is_booked == False
        )
    )
    return result.scalars().all()


# ==========================================
# 📅 ЛОГІКА БРОНЮВАННЯ (З ЗАХИСТОМ RACE CONDITION)

async def create_booking(db: AsyncSession, booking: schemas.BookingCreate):
    # 🔴 КРИТИЧНА ЗОНА: Використовуємо ззалізне блокування рядка (Pessimistic Locking)
    # за допомогою .with_for_update(). Інші транзакції чекатимуть, поки ми не зробимо commit.
    query = select(models.Slot).where(models.Slot.id == booking.slot_id).with_for_update()
    result = await db.execute(query)
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(status_code=404, detail="Слот не знайдено")

    if slot.is_booked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Цей слот уже заброньовано іншим пацієнтом!"
        )

    # Бронюємо слот
    slot.is_booked = True

    # Створюємо сам запис на прийом
    db_booking = models.Booking(
        slot_id=booking.slot_id,
        patient_name=booking.patient_name,
        patient_phone=booking.patient_phone
    )
    db.add(db_booking)

    await db.commit()
    await db.refresh(db_booking)
    return db_booking


# ==========================================
# 💊 ЛОГІКА ЕЛЕКТРОННИХ РЕЦЕПТІВ

async def create_prescription(db: AsyncSession, prescription: schemas.PrescriptionCreate):
    # Перевіряємо, чи взагалі існує такий візит (booking)
    booking_result = await db.execute(
        select(models.Booking).where(models.Booking.id == prescription.booking_id)
    )
    if not booking_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Візит (booking_id) не знайдено")

    # Генеруємо 4 випадкові цифри для SMS-підтвердження
    sms_code = f"{random.randint(1000, 9999)}"

    # Рахуємо дедлайн дії рецепта (сьогодні + кількість днів)
    created_now = datetime.datetime.utcnow()
    expires_now = created_now + datetime.timedelta(days=prescription.duration_days)

    db_prescription = models.Prescription(
        booking_id=prescription.booking_id,
        medication_name=prescription.medication_name,
        verification_code=sms_code,
        is_redeemed=False,
        created_at=created_now,
        expires_at=expires_now
    )
    db.add(db_prescription)
    await db.commit()
    await db.refresh(db_prescription)

    # У реальному житті тут був би код відправки SMS, але в MVP я просто
    # виведемо код у консоль Docker і повернемо в коді, щоб ми могли його скопіювати.
    print(f"📦 [SMS-GATEWAY] Рецепт #{db_prescription.id}. Код для пацієнта: {sms_code}")

    return db_prescription


async def redeem_prescription(db: AsyncSession, prescription_id: int, redeem_data: schemas.PrescriptionRedeem):
    # Шукаємо рецепт за ID
    result = await db.execute(
        select(models.Prescription).where(models.Prescription.id == prescription_id)
    )
    db_prescription = result.scalar_one_or_none()

    if not db_prescription:
        raise HTTPException(status_code=404, detail="Рецепт не знайдено")

    # ТРИРІВНЕВА ВАЛІДАЦІЯ:
    # 1. Перевірка на повторне використання
    if db_prescription.is_redeemed:
        raise HTTPException(status_code=400, detail="Цей рецепт уже був погашений в аптеці!")

    # 2. Перевірка терміну дії
    if db_prescription.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Термін дії цього рецепта закінчився")

    # 3. Перевірка 4-значного цифрового коду
    if db_prescription.verification_code != redeem_data.verification_code:
        raise HTTPException(status_code=400, detail="Неправильний код підтвердження з SMS!")

    # Якщо все ок — гасимо рецепт (ліки видано)
    db_prescription.is_redeemed = True
    await db.commit()
    await db.refresh(db_prescription)
    return db_prescription