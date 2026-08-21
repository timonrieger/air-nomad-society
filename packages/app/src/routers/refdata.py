from fastapi import APIRouter

from src.models.refdata import RefData
from src.services import refdata

router = APIRouter()


@router.get("/refdata")
def reference_data() -> RefData:
    """The choice lists the subscription form is built from."""
    return RefData(
        cities=refdata.load().cities,
        currencies=refdata.currency_choices(),
        countries=refdata.country_choices(),
        regions=refdata.regions(),
    )
