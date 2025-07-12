from sqladmin import ModelView
from models.report import Report

class ReportAdmin(ModelView, model=Report):
    column_list = [Report.id, Report.reporter_id, Report.reason, Report.created_at]
    name = "Report"
    name_plural = "Reports"
