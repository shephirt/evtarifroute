from sqlalchemy import ARRAY, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MspTariff(Base):
    """A Mobility Service Provider (MSP) subscription/tariff.

    Manually curated (see Phase 4) — maps a tariff to the CPOs it covers so
    the recommendation engine can compare cost vs. roaming rates.
    """

    __tablename__ = "msp_tariffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(255))

    base_fee_monthly: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    price_per_kwh_ac: Mapped[float | None] = mapped_column(Numeric(6, 4))
    price_per_kwh_dc: Mapped[float | None] = mapped_column(Numeric(6, 4))
    roaming_price_per_kwh: Mapped[float | None] = mapped_column(Numeric(6, 4))

    # Operator IDs (operators.ocm_operator_id) covered by this tariff's home
    # network / preferential rate.
    covered_operator_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)

    notes: Mapped[str | None] = mapped_column(String(1024))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MspTariff id={self.id} name={self.name!r}>"
