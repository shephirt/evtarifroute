from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.database import Base


class Station(Base):
    """A single charging location, sourced from OpenChargeMap."""

    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True)
    ocm_id: Mapped[int] = mapped_column(unique=True, index=True)

    operator_id: Mapped[int | None] = mapped_column(ForeignKey("operators.id"), index=True)
    operator: Mapped["Operator"] = relationship(back_populates="stations")

    name: Mapped[str | None] = mapped_column(String(255))

    # SRID=4326 (WGS84) point geometry, GIST-indexed for spatial queries.
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    max_power_kw: Mapped[float | None] = mapped_column(Numeric(6, 2))
    usage_type: Mapped[str | None] = mapped_column(String(64))

    # Number of individual charging points/bays at this location (OCM
    # "NumberOfPoints") — e.g. a single address entry might have 4 physical
    # charging bays.
    number_of_points: Mapped[int | None] = mapped_column(Integer)

    # Distinct connector/plug type titles reported by OCM for this station
    # (e.g. "Type 2 (Socket Only)", "CCS (Type 2)", "CHAdeMO"). A station can
    # have multiple connections of different types.
    connector_types: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    is_ac: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dc: Mapped[bool] = mapped_column(Boolean, default=False)

    # Trailer/caravan accessibility filter (SRS 2.4)
    drive_through: Mapped[bool] = mapped_column(Boolean, default=False)
    caravan_friendly: Mapped[bool] = mapped_column(Boolean, default=False)
    trailer_friendly: Mapped[bool] = mapped_column(Boolean, default=False)
    hgv_friendly: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Station id={self.id} ocm_id={self.ocm_id}>"
