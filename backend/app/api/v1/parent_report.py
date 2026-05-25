from datetime import date

from fastapi import APIRouter, Header, Query

from app.api.v1.auth import optional_auth_account
from app.domain.parent_report import ParentReport
from app.services.parent_report_service import get_parent_report_service

router = APIRouter(prefix="/parent", tags=["parent"])
parent_report_service = get_parent_report_service()


@router.get("/reports/{child_id}", response_model=ParentReport)
def get_parent_report(
    child_id: str,
    report_date: date | None = Query(default=None, alias="date"),
    authorization: str | None = Header(default=None),
) -> ParentReport:
    account = optional_auth_account(authorization)
    if account is not None:
        child_id = account.child_id
    return parent_report_service.get_daily_report(
        child_id,
        report_date=report_date,
    )


@router.get("/report/today", response_model=ParentReport)
def get_today_parent_report(
    child_id: str = Query(..., min_length=1),
    authorization: str | None = Header(default=None),
) -> ParentReport:
    account = optional_auth_account(authorization)
    if account is not None:
        child_id = account.child_id
    return parent_report_service.get_daily_report(child_id)
