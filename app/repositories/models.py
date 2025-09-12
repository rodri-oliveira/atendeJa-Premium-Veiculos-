from __future__ import annotations
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, ForeignKey, Boolean, JSON, Index, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class ConversationStatus(str, Enum):
    active_bot = "active_bot"
    human_handoff = "human_handoff"
    closed = "closed"


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    timezone: Mapped[str] = mapped_column(String(64), default="America/Sao_Paulo")
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict)

    contacts: Mapped[list[Contact]] = relationship(back_populates="tenant")  # type: ignore


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"))
    wa_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, default=list)
    do_not_disturb: Mapped[bool] = mapped_column(Boolean, default=False)

    tenant: Mapped[Tenant] = relationship(back_populates="contacts")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="contact")  # type: ignore

    __table_args__ = (
        Index("uix_contact_tenant_wa", "tenant_id", "wa_id", unique=True),
    )


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    status: Mapped[ConversationStatus] = mapped_column(SAEnum(ConversationStatus), default=ConversationStatus.active_bot)
    assigned_to: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact: Mapped[Contact] = relationship(back_populates="conversations")


class MessageDirection(str, Enum):
    inbound = "inbound"
    outbound = "outbound"


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    direction: Mapped[MessageDirection] = mapped_column(SAEnum(MessageDirection))
    type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="received")
    wa_message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("uix_wa_message_id", "tenant_id", "wa_message_id", unique=True),
        Index("uix_idempotency_key", "tenant_id", "idempotency_key", unique=True),
    )


class ConversationEvent(Base):
    __tablename__ = "conversation_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# --- Pizzaria/Lanches domain models ---


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    wa_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    default_address: Mapped[dict | None] = mapped_column(JSON, default=None)  # {street, number, complement, district, city, state, cep, geo?}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("uix_customer_tenant_wa", "tenant_id", "wa_id", unique=True),
    )


class MenuItem(Base):
    __tablename__ = "menu_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(64))  # pizza, lanche, bebida, etc.
    price: Mapped[float] = mapped_column(Float)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    options: Mapped[dict | None] = mapped_column(JSON, default=None)  # sizes, crusts, etc.

    __table_args__ = (
        Index("idx_menu_tenant_category", "tenant_id", "category"),
    )


class OrderStatus(str, Enum):
    draft = "draft"
    pending_payment = "pending_payment"
    paid = "paid"
    in_kitchen = "in_kitchen"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    canceled = "canceled"


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.draft)
    total_items: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_fee: Mapped[float] = mapped_column(Float, default=0.0)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_address: Mapped[dict | None] = mapped_column(JSON, default=None)
    notes: Mapped[str | None] = mapped_column(String(280), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[list[OrderItem]] = relationship(back_populates="order")  # type: ignore


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), index=True)
    qty: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float)
    options: Mapped[dict | None] = mapped_column(JSON, default=None)  # chosen options

    order: Mapped[Order] = relationship(back_populates="items")  # type: ignore


class StoreHours(Base):
    __tablename__ = "store_hours"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0=Monday .. 6=Sunday
    opens_at: Mapped[str] = mapped_column(String(8))  # "18:00"
    closes_at: Mapped[str] = mapped_column(String(8))  # "23:30"

    __table_args__ = (
        Index("uix_store_hours_tenant_day", "tenant_id", "weekday", unique=True),
    )


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))  # bairro/CEP/rótulo
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    criteria: Mapped[dict | None] = mapped_column(JSON, default=None)  # e.g., {"cep_prefix": ["013", "014"]}

    __table_args__ = (
        Index("idx_zone_tenant_name", "tenant_id", "name"),
    )


class OrderStatusEvent(Base):
    __tablename__ = "order_status_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    from_status: Mapped[str] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
