import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app import models, schemas


async def create_doctor(db: AsyncSession, doctor: schemas.DoctorCreate):
    db_doctor = models.Doctor(name=doctor.name, specialization=doctor.specialization)
    db.add(db_doctor)
    await db.commit()
    await db.refresh(db_doctor)
    return db_doctor


async def get_active_slots(db: AsyncSession, doctor_id: int):
    result = await db.execute(
        select(models.Slot).where(
            models.Slot.doctor_id == doctor_id,
            models.Slot.is_booked == False
        )
    )
    return result.scalars().all()



async def create_booking(db: AsyncSession, booking: schemas.BookingCreate):
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

    slot.is_booked = True


    db_booking = models.Booking(
        slot_id=booking.slot_id,
        patient_name=booking.patient_name,
        patient_phone=booking.patient_phone
    )
    db.add(db_booking)

    await db.commit()
    await db.refresh(db_booking)
    return db_booking




async def create_prescription(db: AsyncSession, prescription: schemas.PrescriptionCreate):
    booking_result = await db.execute(
        select(models.Booking).where(models.Booking.id == prescription.booking_id)
    )
    if not booking_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Візит (booking_id) не знайдено")

    sms_code = f"{random.randint(1000, 9999)}"

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

    print(f"📦 [SMS-GATEWAY] Рецепт #{db_prescription.id}. Код для пацієнта: {sms_code}")

    return db_prescription


async def redeem_prescription(db: AsyncSession, prescription_id: int, redeem_data: schemas.PrescriptionRedeem):
    result = await db.execute(
        select(models.Prescription).where(models.Prescription.id == prescription_id)
    )
    db_prescription = result.scalar_one_or_none()

    if not db_prescription:
        raise HTTPException(status_code=404, detail="Рецепт не знайдено")

    if db_prescription.is_redeemed:
        raise HTTPException(status_code=400, detail="Цей рецепт уже був погашений в аптеці!")

    if db_prescription.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Термін дії цього рецепта закінчився")

    if db_prescription.verification_code != redeem_data.verification_code:
        raise HTTPException(status_code=400, detail="Неправильний код підтвердження з SMS!")

    db_prescription.is_redeemed = True
    await db.commit()
    await db.refresh(db_prescription)
    return db_prescription