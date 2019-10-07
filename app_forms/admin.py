from django.contrib import admin
from .models import (ChangeOfWorkSchedule,
                     ProductivityTool, Overtime, Undertime,
                     Leaves, Broadcast, UserProfile)

admin.site.register(ChangeOfWorkSchedule)
admin.site.register(ProductivityTool)
admin.site.register(Overtime)
admin.site.register(Undertime)
admin.site.register(Leaves)
admin.site.register(Broadcast)
admin.site.register(UserProfile)
