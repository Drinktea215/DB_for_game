from __future__ import annotations
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import Integer, DateTime, String, func, ForeignKey
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import Enum as SAEnum


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    level_completed: Mapped[list[str]] = mapped_column(JSON)

    boosts: Mapped[Optional[list[PlayerBoost]]] = relationship('PlayerBoost', back_populates='player')

    def __init__(self, username: str):
        self.username = username
        self.level_completed = []

    def _add_boost(self, session: Session, type_boost: str, count: int = 1):
        boost = session.query(Boost).filter_by(type=type_boost).first()
        if not boost:
            boost = Boost(type=type_boost)
            session.add(boost)
            session.commit()

        existing_player_boost = next((b for b in self.boosts if b.boost == boost), None)
        if existing_player_boost:
            existing_player_boost.count += count
        else:
            player_boost = PlayerBoost(player=self, boost=boost, count=count)
            self.boosts.append(player_boost)

    def add_boost_for_level(self, session: Session, level: str, type_boost: str, count: int):
        if level not in self.level_completed:
            self.level_completed.append(level)
        self._add_boost(session, type_boost, count)

    def add_boost_not_level(self, session: Session, type_boost, count):
        self._add_boost(session, type_boost, count)


class BoostType(Enum):
    power = "power"
    intellect = "intellect"
    dexterity = "dexterity"


class Boost(Base):
    __tablename__ = "boosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped["BoostType"] = mapped_column(SAEnum(BoostType))
    players: Mapped[Optional[list[PlayerBoost]]] = relationship('PlayerBoost', back_populates='boost')


class PlayerBoost(Base):
    __tablename__ = 'player_boosts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    player_id: Mapped[str] = mapped_column(Integer, ForeignKey('players.id'))
    player: Mapped[Optional[list[Player]]] = relationship('Player', back_populates='boosts', cascade="all")
    boost_id: Mapped[int] = mapped_column(Integer, ForeignKey('boosts.id'))
    boost: Mapped[Optional[list[Boost]]] = relationship('Boost', back_populates='players', cascade="all")

    count: Mapped[int] = mapped_column(Integer, default=0)
