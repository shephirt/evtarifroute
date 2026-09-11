"""Curated MSP (Mobility Service Provider) tariff seed data (SRS 2.3 / Phase 4).

IMPORTANT — data quality disclaimer:
These figures are illustrative approximations based on generally known,
publicly advertised tariff structures for well-known German/DACH/NL EV
charging subscriptions as of general knowledge. They are NOT scraped or
verified against live provider pricing pages, and real-world tariffs change
frequently (and often have regional/promotional variations, connector-type
surcharges, idle fees, etc. not modeled here at all). Treat these as
reasonable placeholders to make the recommendation engine functionally
testable end-to-end — before using this for real user-facing decisions,
each entry should be verified/updated against the provider's current published
rates, ideally with a periodic review process (e.g. quarterly).

`covered_operator_names` are matched against `operators.name` in our DB
(which mirrors OpenChargeMap operator names) at seed time — not stored
directly, since OCM's internal operator IDs aren't known ahead of ingestion.
Matching is case-insensitive exact-match on OCM's operator title.
"""

TARIFF_SEED_DATA = [
    {
        "name": "EnBW mobility+ Basic",
        "provider": "EnBW",
        "base_fee_monthly": 0.0,
        "price_per_kwh_ac": 0.45,
        "price_per_kwh_dc": 0.55,
        "roaming_price_per_kwh": 0.66,
        "covered_operator_names": ["EnBW (D)"],
        "notes": (
            "Illustrative approximation, not verified against live pricing. "
            "Pay-as-you-go, no monthly fee, higher per-kWh rate."
        ),
    },
    {
        "name": "EnBW mobility+ L",
        "provider": "EnBW",
        "base_fee_monthly": 5.99,
        "price_per_kwh_ac": 0.39,
        "price_per_kwh_dc": 0.45,
        "roaming_price_per_kwh": 0.59,
        "covered_operator_names": ["EnBW (D)"],
        "notes": "Illustrative approximation. Monthly fee, lower per-kWh rate.",
    },
    {
        "name": "Shell Recharge Card",
        "provider": "Shell",
        "base_fee_monthly": 0.0,
        "price_per_kwh_ac": 0.45,
        "price_per_kwh_dc": 0.55,
        "roaming_price_per_kwh": 0.65,
        "covered_operator_names": [
            "Shell Recharge Solutions (DE)",
            "Shell Recharge Solutions (BE)",
        ],
        "notes": "Illustrative approximation, not verified against live pricing.",
    },
    {
        "name": "Allego App",
        "provider": "Allego",
        "base_fee_monthly": 0.0,
        "price_per_kwh_ac": 0.45,
        "price_per_kwh_dc": 0.59,
        "roaming_price_per_kwh": 0.65,
        "covered_operator_names": ["Allego BV"],
        "notes": "Illustrative approximation, not verified against live pricing.",
    },
    {
        "name": "be emobil Tarif",
        "provider": "be emobil",
        "base_fee_monthly": 0.0,
        "price_per_kwh_ac": 0.42,
        "price_per_kwh_dc": 0.52,
        "roaming_price_per_kwh": 0.60,
        "covered_operator_names": ["be emobil"],
        "notes": "Illustrative approximation, not verified against live pricing.",
    },
    {
        "name": "Vattenfall InCharge",
        "provider": "Vattenfall",
        "base_fee_monthly": 0.0,
        "price_per_kwh_ac": 0.42,
        "price_per_kwh_dc": 0.52,
        "roaming_price_per_kwh": 0.60,
        "covered_operator_names": ["Vattenfall InCharge"],
        "notes": "Illustrative approximation, not verified against live pricing.",
    },
    {
        "name": "Tesla Supercharging (non-membership)",
        "provider": "Tesla",
        "base_fee_monthly": 0.0,
        "price_per_kwh_ac": None,
        "price_per_kwh_dc": 0.42,
        "roaming_price_per_kwh": 0.55,
        "covered_operator_names": [
            "Tesla (Tesla-only charging)",
            "Tesla (including non-tesla)",
        ],
        "notes": (
            "Illustrative approximation. DC/Supercharging only, no AC home rate — "
            "falls back to the DC rate for cost estimation."
        ),
    },
    {
        "name": "ubitricity Streetlamp Charging",
        "provider": "ubitricity (Shell)",
        "base_fee_monthly": 0.0,
        "price_per_kwh_ac": 0.55,
        "price_per_kwh_dc": None,
        "roaming_price_per_kwh": 0.60,
        "covered_operator_names": ["ubitricity"],
        "notes": (
            "Illustrative approximation. AC-only (lamppost/on-street charging), "
            "no DC rate — falls back to the AC rate for cost estimation."
        ),
    },
    {
        "name": "Aral pulse App",
        "provider": "Aral (bp pulse)",
        "base_fee_monthly": 0.0,
        "price_per_kwh_ac": 0.45,
        "price_per_kwh_dc": 0.55,
        "roaming_price_per_kwh": 0.65,
        "covered_operator_names": ["Aral pulse"],
        "notes": "Illustrative approximation, not verified against live pricing.",
    },
    {
        "name": "PlugSurfing Roaming",
        "provider": "PlugSurfing",
        "base_fee_monthly": 0.0,
        "price_per_kwh_ac": 0.55,
        "price_per_kwh_dc": 0.65,
        "roaming_price_per_kwh": 0.65,
        "covered_operator_names": ["PlugSurfing"],
        "notes": (
            "Illustrative approximation. A pure roaming/aggregator app — home and "
            "roaming rates are effectively the same here since it has no owned "
            "charging network."
        ),
    },
]
