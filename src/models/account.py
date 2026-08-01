from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, text
from sqlalchemy.dialects.postgresql import NUMERIC, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.expense import Expense
    from src.models.user import User


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
        nullable=False,
    )

    __mapper_args__ = {
        "polymorphic_on": "account_type",
        "polymorphic_identity": "account",
    }

    # Relationships
    owner: Mapped[User] = relationship("User", back_populates="accounts")
    expenses: Mapped[list[Expense]] = relationship("Expense", back_populates="account", cascade="all, delete-orphan")


class CreditCard(Account):
    __tablename__ = "credit_cards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    main_credit_card_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("credit_cards.id"),
        nullable=True,
    )
    closing_day: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    due_day: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    limit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False)
    financing_limit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "credit_card",
    }

    # Self-referential: card extensions — remote_side points to the "one" side (parent)
    extensions: Mapped[list[CreditCard]] = relationship(
        "CreditCard",
        foreign_keys=[main_credit_card_id],
        back_populates="main_card",
    )
    main_card: Mapped[CreditCard | None] = relationship(
        "CreditCard",
        foreign_keys=[main_credit_card_id],
        back_populates="extensions",
        remote_side="CreditCard.id",
    )
