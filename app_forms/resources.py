from import_export import resources
from .models import (ChangeOfWorkSchedule, ProductivityTool,
                     Overtime, Undertime, Leaves)


class ChangeOfWorkScheduleResource(resources.ModelResource):
    class Meta:
        model = ChangeOfWorkSchedule


class ProductivityToolResource(resources.ModelResource):
    class Meta:
        model = ProductivityTool


class OvertimeResource(resources.ModelResource):
    class Meta:
        model = Overtime


class UndertimeResource(resources.ModelResource):
    class Meta:
        model = Undertime


class LeavesResource(resources.ModelResource):
    class Meta:
        model = Leaves
