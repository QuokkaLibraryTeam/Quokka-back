from fastapi_admin.resources import Model
from fastapi_admin.widgets import displays, fields
from models.report import Report

class ReportResource(Model):
    label = "Report"
    model = Report
    page_pre_title = "Reports"
    page_title = "Report List"

    fields = [
        displays.Display(name="id", label="ID"),
        fields.ForeignKey(name="reporter", label="Reporter"),
        fields.ForeignKey(name="story", label="Story"),
        fields.ForeignKey(name="comment", label="Comment"),
        fields.TextArea(name="reason", label="Reason"),
        displays.Datetime(name="created_at"),
    ]
