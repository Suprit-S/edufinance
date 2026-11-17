"""Categories: system categories (master table) plus the user's own (FR-12)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select

from app.errors import Conflict, NotFound
from app.extensions import db
from app.models import Category, MonthlyPlanItem, Transaction


def visible_to(user_id: uuid.UUID):
    """SQL condition: system categories and the user's own."""
    return or_(Category.user_id.is_(None), Category.user_id == user_id)


def list_categories(user_id: uuid.UUID, kind=None) -> list[Category]:
    stmt = select(Category).where(visible_to(user_id))
    if kind is not None:
        stmt = stmt.where(Category.kind == kind)
    return list(
        db.session.scalars(stmt.order_by(Category.kind, Category.group_name, Category.name))
    )


def get_category(user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    cat = db.session.get(Category, category_id)
    if cat is None or (cat.user_id is not None and cat.user_id != user_id):
        raise NotFound("Category")
    return cat


def create_category(user_id: uuid.UUID, data: dict) -> Category:
    """Create a custom category; the name must be unique per kind among the
    categories the user can see."""
    duplicate = db.session.scalar(
        select(Category.id).where(
            visible_to(user_id),
            Category.kind == data["kind"],
            func.lower(Category.name) == data["name"].lower(),
        )
    )
    if duplicate:
        raise Conflict(f"A category called '{data['name']}' already exists.")
    cat = Category(
        user_id=user_id,
        name=data["name"],
        kind=data["kind"],
        group_name=data.get("group_name") or "My categories",
        counts_as_earned=data.get("counts_as_earned", True),
        is_system=False,
    )
    db.session.add(cat)
    db.session.flush()
    return cat


def delete_category(user_id: uuid.UUID, category_id: uuid.UUID) -> None:
    cat = get_category(user_id, category_id)
    if cat.user_id is None:
        raise Conflict("Built-in categories cannot be deleted.")
    in_use = db.session.scalar(
        select(Transaction.id).where(Transaction.category_id == cat.id).limit(1)
    ) or db.session.scalar(
        select(MonthlyPlanItem.id).where(MonthlyPlanItem.category_id == cat.id).limit(1)
    )
    if in_use:
        raise Conflict("This category is in use and cannot be deleted.")
    db.session.delete(cat)
    db.session.flush()
