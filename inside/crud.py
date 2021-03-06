from typing import List

import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from inside import db_models, schemas


def get_user_by_name(db: Session, name: str) -> db_models.User:
    return db.query(db_models.User).filter(db_models.User.name == name).first()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()


def create_user(db: Session, user: schemas.UserWithPassword) -> schemas.UserBase:
    hashed = hash_password(user.password)
    db_user = db_models.User(name=user.name, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return schemas.UserBase(name=db_user.name)


def check_password(hashed_password: str, other_password: str):
    return bcrypt.checkpw(other_password.encode("utf-8"), hashed_password.encode())


def check_user(db: Session, user: schemas.UserWithPassword) -> bool:
    db_user = get_user_by_name(db, user.name)
    return db_user and check_password(db_user.hashed_password, user.password)


def get_last_messages(db: Session, limit: int) -> List[schemas.Message]:
    query_result = (
        db.query(db_models.Message)
        .order_by(db_models.Message.id.desc())
        .limit(limit)
        .all()
    )
    return [
        schemas.Message(name=message.user.name, message=message.message)
        for message in reversed(query_result)
    ]


def post_message(db: Session, message: schemas.Message) -> None:
    db_user = get_user_by_name(db, message.name)

    if db_user is None:
        raise HTTPException(status_code=400, detail=f"Unknown user: {message.name}")

    db_message = db_models.Message(user_id=db_user.id, message=message.message)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
