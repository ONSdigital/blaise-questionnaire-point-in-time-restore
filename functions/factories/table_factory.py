from datetime import datetime
from typing import Any, Optional, Type

from sqlalchemy import BIGINT, BLOB, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base_table import Base

_model_cache: dict[str, Type[Base]] = {}


class TableFactory:

    @staticmethod
    def create_form_table_model(table_name: str) -> Any:
        if table_name in _model_cache:
            return _model_cache[table_name]

        class QuestionnaireFormTable(Base):

            __tablename__ = table_name
            __table_args__ = {"extend_existing": True}
            Serial_Number: Mapped[int] = mapped_column(BIGINT())
            FormID: Mapped[int] = mapped_column(
                BIGINT(), primary_key=True, autoincrement=True
            )
            ValidationStatus: Mapped[Optional[int]] = mapped_column(Integer())
            Mode: Mapped[Optional[str]] = mapped_column(String(255))
            DataEntryBehaviour: Mapped[Optional[str]] = mapped_column(String(255))
            SaveStatus: Mapped[Optional[str]] = mapped_column(String(255))
            IdentityName: Mapped[Optional[str]] = mapped_column(String(255))
            SourceInfo: Mapped[Optional[str]] = mapped_column(String(255))
            TimeCreated: Mapped[Optional[datetime]] = mapped_column(DateTime())
            LastModification: Mapped[Optional[datetime]] = mapped_column(DateTime())
            DataStream = mapped_column(BLOB())

        _model_cache[table_name] = QuestionnaireFormTable
        return QuestionnaireFormTable
