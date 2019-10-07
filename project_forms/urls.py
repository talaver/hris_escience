"""project_forms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('eforms/', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('eforms/', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('eforms/blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, reverse_lazy
from app_forms import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # LOGIN / LOGOUT / DASHBOARD / ADMIN
     path(r'', LoginView.as_view(
             template_name='../templates/registration/login2.html'
             ), name='login'),

    path('eforms/', LoginView.as_view(
             template_name='../templates/registration/login.html'
             ), name='login'),


    path('eforms/login', LoginView.as_view(
            template_name='../templates/registration/login.html'
            ), name='login'),


    path('eforms/logout', LogoutView.as_view(
        next_page=reverse_lazy('login')
        ), name='logout'),


    path('eforms/dashboard', views.dashboard, name='dashboard'),


    path('eforms/admin/', admin.site.urls),



    # LEAVES
    path('eforms/leave_filing', views.leave_filing, name='leave_filing'),


    path('eforms/add_leave', views.add_leave, name='add_leave'),


    path('eforms/leave_request', views.leave_request, name='leave_request'),
    path('eforms/leave_request_details/<int:pk>',
         views.leave_request_details,
         name='leave_request_details'),
    path('eforms/leave_request/delete/<int:pk>',
         views.delete,
         name='delete'),


    path('eforms/leave_summary', views.leave_summary, name='leave_summary'),
    path('eforms/excel_summary_of_leaves',
         views.excel_summary_of_leaves,
         name='excel_summary_of_leaves'),
    path('eforms/pdf_summary_of_leaves',
         views.pdf_summary_of_leaves,
         name='pdf_summary_of_leaves'),
    path('eforms/csv_summary_of_leaves',
         views.csv_summary_of_leaves,
         name='csv_summary_of_leaves'),
    path('eforms/json_summary_of_leaves',
         views.json_summary_of_leaves,
         name='json_summary_of_leaves'),


    path('eforms/leave_approval', views.leave_approval, name='leave_approval'),
    path('eforms/leave_approval_details/<int:pk>',
         views.leave_approval_details,
         name='leave_approval_details'),


    path('eforms/reports_leave', views.reports_leave, name='reports_leave'),
    path('eforms/excel_leave', views.excel_leave, name='excel_leave'),
    path('eforms/pdf_leave', views.pdf_leave, name='pdf_leave'),
    path('eforms/csv_leave', views.csv_leave, name='csv_leave'),
    path('eforms/json_leave', views.json_leave, name='json_leave'),
    # END OF LEAVES



    # CHANGE OF WORK SCHEDULE
    path('eforms/change_of_work_schedule',
         views.change_of_work_schedule,
         name='change_of_work_schedule'),


    path('eforms/add_change_of_work_schedule',
         views.add_change_of_work_schedule,
         name='add_change_of_work_schedule'),


    path('eforms/change_of_work_schedule_request',
         views.change_of_work_schedule_request,
         name='change_of_work_schedule_request'),
    path('eforms/change_of_work_schedule_request_details/<int:pk>',
         views.change_of_work_schedule_request_details,
         name='change_of_work_schedule_request_details'),
    path('eforms/change_of_work_schedule_request/delete/<int:pk>',
         views.deleteChangeOfWorkSchedule,
         name='deleteChangeOfWorkSchedule'),


    path('eforms/change_of_work_schedule_summary',
         views.change_of_work_schedule_summary,
         name='change_of_work_schedule_summary'),
    path('eforms/excel_summary_of_change_of_work_schedule',
         views.excel_summary_of_change_of_work_schedule,
         name='excel_summary_of_change_of_work_schedule'),
    path('eforms/pdf_summary_of_change_of_work_schedule',
         views.pdf_summary_of_change_of_work_schedule,
         name='pdf_summary_of_change_of_work_schedule'),
    path('eforms/csv_summary_of_change_of_work_schedule',
         views.csv_summary_of_change_of_work_schedule,
         name='csv_summary_of_change_of_work_schedule'),
    path('eforms/json_summary_of_change_of_work_schedule',
         views.json_summary_of_change_of_work_schedule,
         name='json_summary_of_change_of_work_schedule'),


    path('eforms/change_of_work_schedule_approval',
         views.change_of_work_schedule_approval,
         name='change_of_work_schedule_approval'),
    path('eforms/change_of_work_schedule_approval_details/<int:pk>',
         views.change_of_work_schedule_approval_details,
         name='change_of_work_schedule_approval_details'),


    path('eforms/reports_change_of_work_schedule',
         views.reports_change_of_work_schedule,
         name='reports_change_of_work_schedule'),
    path('eforms/excel_change_of_work_schedule',
         views.excel_change_of_work_schedule,
         name='excel_change_of_work_schedule'),
    path('eforms/pdf_change_of_work_schedule',
         views.pdf_change_of_work_schedule,
         name='pdf_change_of_work_schedule'),
    path('eforms/csv_change_of_work_schedule',
         views.csv_change_of_work_schedule,
         name='csv_change_of_work_schedule'),
    path('eforms/json_change_of_work_schedule',
         views.json_change_of_work_schedule,
         name='json_change_of_work_schedule'),
    # END OF CHANGE OF WORK SCHEDULE



    # PRODUCTIVITY TOOL
    path('eforms/productivity_tool',
         views.productivity_tool,
         name='productivity_tool'),


    path('eforms/add_productivity_tool',
         views.add_productivity_tool,
         name='add_productivity_tool'),


    path('eforms/productivity_tool_request',
         views.productivity_tool_request,
         name='productivity_tool_request'),
    path('eforms/productivity_tool_request_details/<int:pk>',
         views.productivity_tool_request_details,
         name='productivity_tool_request_details'),
    path('eforms/productivity_tool_request/delete/<int:pk>',
         views.deleteProductivityTool,
         name='deleteProductivityTool'),


    path('eforms/productivity_tool_summary',
         views.productivity_tool_summary,
         name='productivity_tool_summary'),
    path('eforms/excel_summary_of_productivity_tool',
         views.excel_summary_of_productivity_tool,
         name='excel_summary_of_productivity_tool'),
    path('eforms/pdf_summary_of_productivity_tool',
         views.pdf_summary_of_productivity_tool,
         name='pdf_summary_of_productivity_tool'),
    path('eforms/csv_summary_of_productivity_tool',
         views.csv_summary_of_productivity_tool,
         name='csv_summary_of_productivity_tool'),
    path('eforms/json_summary_of_productivity_tool',
         views.json_summary_of_productivity_tool,
         name='json_summary_of_productivity_tool'),


    path('eforms/productivity_tool_approval',
         views.productivity_tool_approval,
         name='productivity_tool_approval'),
    path('eforms/productivity_tool_approval_details/<int:pk>',
         views.productivity_tool_approval_details,
         name='productivity_tool_approval_details'),


    path('eforms/reports_productivity_tool',
         views.reports_productivity_tool,
         name='reports_productivity_tool'),
    path('eforms/excel_productivity_tool',
         views.excel_productivity_tool,
         name='excel_productivity_tool'),
    path('eforms/pdf_productivity_tool',
         views.pdf_productivity_tool,
         name='pdf_productivity_tool'),
    path('eforms/csv_productivity_tool',
         views.csv_productivity_tool,
         name='csv_productivity_tool'),
    path('eforms/json_productivity_tool',
         views.json_productivity_tool,
         name='json_productivity_tool'),
    # END OF PRODUCTIVITY TOOL



    # OVERTIME
    path('eforms/overtime', views.overtime, name='overtime'),


    path('eforms/add_overtime', views.add_overtime, name='add_overtime'),


    path('eforms/overtime_request', views.overtime_request, name='overtime_request'),
    path('eforms/overtime_request_details/<int:pk>',
         views.overtime_request_details,
         name='overtime_request_details'),
    path('eforms/overtime_request/delete/<int:pk>',
         views.deleteOvertime,
         name='deleteOvertime'),


    path('eforms/overtime_summary', views.overtime_summary, name='overtime_summary'),
    path('eforms/excel_summary_of_overtime',
         views.excel_summary_of_overtime,
         name='excel_summary_of_overtime'),
    path('eforms/pdf_summary_of_overtime',
         views.pdf_summary_of_overtime,
         name='pdf_summary_of_overtime'),
    path('eforms/csv_summary_of_overtime',
         views.csv_summary_of_overtime,
         name='csv_summary_of_overtime'),
    path('eforms/json_summary_of_overtime',
         views.json_summary_of_overtime,
         name='json_summary_of_overtime'),


    path('eforms/overtime_approval',
         views.overtime_approval,
         name='overtime_approval'),
    path('eforms/overtime_approval_details/<int:pk>',
         views.overtime_approval_details,
         name='overtime_approval_details'),


    path('eforms/reports_overtime', views.reports_overtime, name='reports_overtime'),
    path('eforms/excel_overtime', views.excel_overtime, name='excel_overtime'),
    path('eforms/pdf_overtime', views.pdf_overtime, name='pdf_overtime'),
    path('eforms/csv_overtime', views.csv_overtime, name='csv_overtime'),
    path('eforms/json_overtime', views.json_overtime, name='json_overtime'),
    # END OF OVERTIME



    # UNDERTIME
    path('eforms/undertime', views.undertime, name='undertime'),


    path('eforms/add_undertime', views.add_undertime, name='add_undertime'),


    path('eforms/undertime_request',
         views.undertime_request,
         name='undertime_request'),
    path('eforms/undertime_request_details/<int:pk>',
         views.undertime_request_details,
         name='undertime_request_details'),
    path('eforms/undertime_request/delete/<int:pk>',
         views.deleteUndertime,
         name='deleteUndertime'),


    path('eforms/undertime_summary',
         views.undertime_summary,
         name='undertime_summary'),
    path('eforms/excel_summary_of_undertime',
         views.excel_summary_of_undertime,
         name='excel_summary_of_undertime'),
    path('eforms/pdf_summary_of_undertime',
         views.pdf_summary_of_undertime,
         name='pdf_summary_of_undertime'),
    path('eforms/csv_summary_of_undertime',
         views.csv_summary_of_undertime,
         name='csv_summary_of_undertime'),
    path('eforms/json_summary_of_undertime',
         views.json_summary_of_undertime,
         name='json_summary_of_undertime'),


    path('eforms/undertime_approval',
         views.undertime_approval,
         name='undertime_approval'),
    path('eforms/undertime_approval_details/<int:pk>',
         views.undertime_approval_details,
         name='undertime_approval_details'),


    path('eforms/reports_undertime',
         views.reports_undertime,
         name='reports_undertime'),
    path('eforms/excel_undertime', views.excel_undertime, name='excel_undertime'),
    path('eforms/pdf_undertime', views.pdf_undertime, name='pdf_undertime'),
    path('eforms/csv_undertime', views.csv_undertime, name='csv_undertime'),
    path('eforms/json_undertime', views.json_undertime, name='json_undertime'),
    # END OF UNDERTIME


    # BROADCAST
    path('eforms/add_broadcast', views.add_broadcast, name='add_broadcast'),
    path('eforms/dashboard/delete/<int:pk>',
         views.bcast_delete,
         name='bcast_delete'),
    # END OF BROADCAST

    path('eforms/change_password', views.change_password, name='change_password'),
    path('eforms/updateProfile', views.updateProfile, name='updateProfile'),
    path('eforms/multifactor_auth', views.multifactor_auth, name='multifactor_auth'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
