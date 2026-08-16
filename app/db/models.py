from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReceiptORM(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    invoice_number: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    invoice_date: Mapped[date] = mapped_column(
        Date,
        index=True,
    )

    issuer_name: Mapped[str] = mapped_column(
        String(255),
    )

    issuer_identifier: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    receiver_name: Mapped[str] = mapped_column(
        String(255),
    )

    receiver_identifier: Mapped[str] = mapped_column(
        String(100),
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        index=True,
    )

    expense_summary: Mapped[str] = mapped_column(
        Text,
    )

    source_filename: Mapped[str] = mapped_column(
        String(255),
    )

    extraction_method: Mapped[str] = mapped_column(
        String(50),
    )

    llm_model: Mapped[str] = mapped_column(
        String(100),
    )

    raw_llm_response: Mapped[str] = mapped_column(
        Text,
    )

    parsed_llm_result: Mapped[dict] = mapped_column(
        JSON,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    items: Mapped[list["ReceiptItemORM"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan",
        order_by="ReceiptItemORM.position",
    )


class ReceiptItemORM(Base):
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    receipt_id: Mapped[int] = mapped_column(
        ForeignKey(
            "receipts.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    position: Mapped[int] = mapped_column()

    description: Mapped[str] = mapped_column(
        Text,
    )

    corrected_description: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
    )

    receipt: Mapped["ReceiptORM"] = relationship(
        back_populates="items",
    )