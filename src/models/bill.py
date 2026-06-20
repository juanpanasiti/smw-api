import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, SmallInteger, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import NUMERIC, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.category import MovementCategory
    from src.models.expense import Expense
    from src.models.user import User


class BillService(Base):
    __tablename__ = "bill_services"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movement_categories.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_arrival_day: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), onupdate=text("NOW()"), nullable=False
    )

    __table_args__ = (CheckConstraint("expected_arrival_day BETWEEN 1 AND 31", name="chk_bill_expected_arrival_day"),)

    # Relationships
    user: Mapped["User"] = relationship("User")
    category: Mapped["MovementCategory"] = relationship("MovementCategory")
    issues: Mapped[list["BillIssue"]] = relationship(
        "BillIssue", back_populates="bill_service", cascade="all, delete-orphan"
    )


class BillIssue(Base):
    __tablename__ = "bill_issues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    bill_service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bill_services.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    amount: Mapped[float] = mapped_column(NUMERIC(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="unpaid")
    expense_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), onupdate=text("NOW()"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("bill_service_id", "period", name="uq_bill_service_period"),
        CheckConstraint("period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'", name="chk_bill_period_format"),
        CheckConstraint("amount > 0", name="chk_bill_issue_amount_positive"),
    )

    # Relationships
    bill_service: Mapped["BillService"] = relationship("BillService", back_populates="issues")
    expense: Mapped["Expense | None"] = relationship("Expense")
