from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, SmallInteger, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import NUMERIC, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.account import Account
    from src.models.category import MovementCategory


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movement_categories.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    acquired_at: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(NUMERIC(12, 2), nullable=False)
    expense_type: Mapped[str] = mapped_column(String(50), nullable=False)
    total_installments: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    first_payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Optimistic Locking
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), onupdate=text("NOW()"), nullable=False
    )

    __table_args__ = (CheckConstraint("amount > 0", name="chk_expense_amount_positive"),)

    __mapper_args__ = {
        "polymorphic_on": "expense_type",
        "polymorphic_identity": "expense",
        "version_id_col": version_id,
    }

    # Relationships
    account: Mapped[Account] = relationship("Account", back_populates="expenses")
    category: Mapped[MovementCategory | None] = relationship("MovementCategory", back_populates="expenses")
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="expense", cascade="all, delete-orphan")


class Purchase(Expense):
    __mapper_args__ = {
        "polymorphic_identity": "purchase",
    }


class Subscription(Expense):
    __mapper_args__ = {
        "polymorphic_identity": "subscription",
    }


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[float] = mapped_column(NUMERIC(12, 2), nullable=False)
    no_installment: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    period_month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    period_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    is_last_payment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    credit_card_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Optimistic Locking
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), onupdate=text("NOW()"), nullable=False
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_payment_amount_positive"),
        CheckConstraint("period_month BETWEEN 1 AND 12", name="chk_payment_period_month"),
        UniqueConstraint("expense_id", "period_year", "period_month", name="uq_expense_period"),
    )

    __mapper_args__ = {
        "version_id_col": version_id,
    }

    # Relationships
    expense: Mapped[Expense] = relationship("Expense", back_populates="payments")
