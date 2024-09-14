from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import Integer, DateTime, String, func, ForeignKey, Table, Column
from datetime import datetime
from random import choice
from enum import Enum
from sqlalchemy import Enum as SAEnum


class Base(DeclarativeBase):
    pass


assoc_table_for_boosts = Table(
    "assoc_table_for_boosts", Base.metadata,
    Column("player_id", ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
    Column("boost_id", ForeignKey("boosts.id", ondelete="CASCADE"), primary_key=True)
)


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    experience_for_level_up: Mapped[int] = mapped_column(Integer, default=1000)
    count_reward_for_level_up: Mapped[int] = mapped_column(Integer, default=1)

    boosts: Mapped[list[Boost]] = relationship(secondary=assoc_table_for_boosts, back_populates="players")

    def _add_boost(self, type_boost: str, count=None):
        count = self.count_reward_for_level_up if count is None else count
        for x in range(count):
            boost = Boost(type=type_boost)
            self.boosts.append(boost)

    def level_up(self):
        self.level += 1
        self.experience = 0
        self.experience_for_level_up *= 2
        self._add_boost_for_level_up()
        self.count_reward_for_level_up += 1

    def _add_boost_for_level_up(self):
        type_boost = choice(list(BoostType))
        self._add_boost(type_boost.value)

    def add_boost_not_level_up(self, type_boost, count):
        self._add_boost(type_boost, count)

    def increase_experience(self, amount: int):
        self.experience += amount
        while self.experience >= self.experience_for_level_up:
            amount = self.experience - self.experience_for_level_up
            self.level_up()
            self.experience += amount


class BoostType(Enum):
    power = "power"
    intellect = "intellect"
    dexterity = "dexterity"


class Boost(Base):
    __tablename__ = "boosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped["BoostType"] = mapped_column(SAEnum(BoostType))
    players: Mapped[list[Player]] = relationship(secondary=assoc_table_for_boosts,
                                                 back_populates="boosts",
                                                 lazy="selectin")
