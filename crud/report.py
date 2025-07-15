from crud.base import CRUDBase
from models.report import Report
from schemas.report import ReportCreate

report_crud = CRUDBase[Report, ReportCreate, ReportCreate](Report)
