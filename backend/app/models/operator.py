from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Operator(Base):
    """A Charge Point Operator (CPO), e.g. Ionity, EnBW, EWE Go."""

    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(primary_key=True)
    ocm_operator_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    website: Mapped[str | None] = mapped_column(String(512))

    stations: Mapped[list["Station"]] = relationship(back_populates="operator")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Operator id={self.id} name={self.name!r}>"
