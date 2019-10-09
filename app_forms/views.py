from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import (ChangeOfWorkScheduleForm, ProductivityToolForm,
                    OvertimeForm, UndertimeForm, LeaveForm,
                    SearchForm, FilterForm, RemarksForm,
                    BroadcastForm, UpdateProfileForm, AuthenticateForm)
from .models import (ChangeOfWorkSchedule, ProductivityTool,
                     Overtime, Undertime, Leaves, Broadcast,
                     UserProfile)
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import Group, User
import datetime
import calendar as cal
from django.db.models import Sum
import xlwt
from django.core.mail import send_mail
from .utils import render_to_pdf
from .resources import (ChangeOfWorkScheduleResource, ProductivityToolResource,
                        OvertimeResource, UndertimeResource, LeavesResource)
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from random import randint
import boto3

exclude_group = ['Employees', 'Supervisors',
                 'Probationary', 'Regular',
                 'Approvers']

groups = ['Supervisors', 'Approvers',
          'NeST', 'QA', 'HRD', 'Sales Team', 'Marketing',
          'Dev', 'Accounting', 'SFE Support', 
          'PMs', 'Training Team',
          'Innov', 'Customer Support Group', 'Reports Team']

grpSupervisor = Group.objects.get(name='Supervisors')
grpApprovers = Group.objects.get(name='Approvers')
grpHRD = Group.objects.get(name='HRD')
grpProbationary = Group.objects.get(name='Probationary')
grpRegular = Group.objects.get(name='Regular')
grpEmployees = Group.objects.get(name='Employees')

global_leave = Leaves.objects.none()
global_summary_of_leave = Leaves.objects.none()
global_c_o_w_s = ChangeOfWorkSchedule.objects.none()
global_summary_of_change_of_work_schedule = ChangeOfWorkSchedule.objects.none()
global_prodtool = ProductivityTool.objects.none()
global_summary_of_prodtool = ProductivityTool.objects.none()
global_ot = Overtime.objects.none()
global_summary_of_ot = Overtime.objects.none()
global_ut = Undertime.objects.none()
global_summary_of_ut = Undertime.objects.none()


def index(request):
    return render(request, 'app_forms/login.html')


def multifactor_auth(request):
    user = UserProfile.objects.get(username=request.user)
    if request.method == 'POST':
        form = AuthenticateForm(request.POST)
        if form.is_valid():
            mfa_code = form.cleaned_data['mfa_code']
            if user.mfa_code == mfa_code:
                user.mfa_code = None
                user.save()
                return HttpResponseRedirect('dashboard')
            else:
                return HttpResponseRedirect('logout')
    else:
        if user.phoneNum == "":
            return HttpResponseRedirect('updateProfile')
        else:
            mfa_code = str(randint(100000, 999999))
            user.mfa_code = mfa_code
            user.save()
            mfa_msg = ("Hello " + user.name +
                       ", \nYour MFA code is : " + mfa_code)
            client = boto3.client('sns', 'ap-southeast-1')
            client.publish(PhoneNumber=user.phoneNum, Message=mfa_msg)
            form = AuthenticateForm()

    return render(request,
                  'app_forms/authentication_page.html',
                  {'form': form})


@login_required
def dashboard(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global grpRegular, grpEmployees, grpProbationary
    global groups
    group = ""
    supervisor = ""
    teamLead = ""
    for grps in groups:
        grpGroup = Group.objects.get(name=grps)
        if grpGroup in request.user.groups.all():
            group = str(grpGroup)
            grpUsers = User.objects.filter(
                groups=grpGroup
            )
            for users in grpUsers:
                if grpSupervisor in users.groups.all():
                    supervisor = users.get_full_name()
                if grpApprovers in users.groups.all():
                    teamLead = users.get_full_name()

# ============= USED TO GROUP USERS REGULAR/PROBATIONARY/EMPLOYEE =============
    Now = datetime.date.today()
    dateJoined = datetime.date(request.user.date_joined.year,
                               request.user.date_joined.month,
                               request.user.date_joined.day)
    reg_Date = dateJoined + datetime.timedelta(days=183)
    if (Now.year > request.user.date_joined.year and reg_Date <= Now):
        grpRegular.user_set.remove(request.user)
        grpEmployees.user_set.add(request.user)
    elif(reg_Date <= Now):
        grpProbationary.user_set.remove(request.user)
        grpRegular.user_set.add(request.user)
    elif(reg_Date > Now):
        grpProbationary.user_set.add(request.user)
    broadcast = Broadcast.objects.all()
    return render(request,
                  'app_forms/dashboard.html',
                  {'broadcast': broadcast,
                   'reg_Date': reg_Date,
                   'group': group,
                   'supervisor': supervisor,
                   'teamlead': teamLead})


@login_required
def updateProfile(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, request.FILES)
        if form.is_valid():
            phoneNum = form.cleaned_data['phoneNum']
            profilePic = form.cleaned_data['profilePic']
            user.phoneNum = "+63" + phoneNum
            user.profilePic = profilePic
            user.save()
        return HttpResponseRedirect('dashboard')
    else:
        form = UpdateProfileForm()
    return render(request,
                  'app_forms/Profile/update_profile.html',
                  {'form': form,
                   'user': user})


@login_required
def change_password(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was' +
                                      ' successfully updated!')
            return HttpResponseRedirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'app_forms/Profile/change_password.html',
                  {'form': form})


# -------------------------------F O R M A T-----------------------------------
#   * MAIN MODULE : LEAVE FILING √
#   > EMPLOYEES <
#       > ADD LEAVE √
#           * add_leave
#
#       > FILED LEAVES √
#           * leave_request
#           * leave_request_details/id
#
#       > LEAVE SUMMARY √
#           * leave_summary
#           * excel_summary_of_leaves
#           * csv_summary_of_leaves
#           * pdf_summary_of_leaves
#           * json_summary_of_leaves
#
#   > SUPERVISOR / Approvers / HR <
#       > APPROVAL REQUESTS √
#           * leave_approval
#           * leave_approval_details/id
#
#       > REPORTS √
#           * reports_leave
#           * excel_leave
#           * pdf_leave
#           * csv_leave
#           * json_leave
#       > DELETE √
#           * delete
# -------------------------E N D--O F--F O R M A T-----------------------------

# -----------------------------------------------------------------------------
# LEAVE FILING
# -----------------------------------------------------------------------------


@login_required
def leave_filing(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global grpRegular, grpEmployees, grpProbationary
    vacationCount = Leaves.objects.filter(author=request.user,
                                          leaveType='Vacation Leave',
                                          created__icontains=(datetime.
                                                              date.
                                                              today().
                                                              year)
                                          ).aggregate(Sum('leaveCount'))
    sickCount = Leaves.objects.filter(author=request.user,
                                      leaveType__icontains='Sick Leave',
                                      created__icontains=(datetime.
                                                          date.
                                                          today().
                                                          year)
                                      ).aggregate(Sum('leaveCount'))
    totalCount = Leaves.objects.filter(author=request.user,
                                       created__icontains=(datetime.
                                                           date.
                                                           today().
                                                           year)
                                       ).aggregate(Sum('leaveCount'))
    dateJoined = datetime.date(request.user.date_joined.year,
                               request.user.date_joined.month,
                               request.user.date_joined.day)
    reg_Date = dateJoined + datetime.timedelta(days=183)
    if grpEmployees in request.user.groups.all():
        leaveCredits = 15
        sickLeave = leaveCredits
        vacationLeave = leaveCredits
        total_leave_credits = sickLeave + vacationLeave
    elif grpRegular in request.user.groups.all():
        end_of_month = cal.mdays[reg_Date.month]
        end_of_year = datetime.date(reg_Date.year, 12, 31)
        diff_days = (end_of_month - reg_Date.day) + 1
        diff_months = (end_of_year.month - reg_Date.month)

        leaveCredits = round((diff_months * 1.25) +
                             ((diff_days / 30.4167) * 1.25), 1)
        sickLeave = leaveCredits
        vacationLeave = leaveCredits
        total_leave_credits = sickLeave + vacationLeave
    else:
        sickLeave = 0
        vacationLeave = 0
        leaveCredits = 0
        total_leave_credits = sickLeave + vacationLeave
    return render(request,
                  'app_forms/Leaves/leave_filing.html',
                  {'total_leave_credits': total_leave_credits,
                   #  USED LEAVES
                   'vacationCount': vacationCount,
                   'totalCount': totalCount,
                   'sickCount': sickCount,
                   #  VALID LEAVES
                   'sickLeave': sickLeave,
                   'vacationLeave': vacationLeave})


@login_required
def add_leave(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global grpRegular, grpEmployees
    vacationCount = Leaves.objects.filter(author=request.user,
                                          leaveType='Vacation Leave',
                                          created__icontains=(datetime.
                                                              date.
                                                              today().
                                                              year)
                                          ).aggregate(Sum('leaveCount'))
    sickCount = Leaves.objects.filter(author=request.user,
                                      leaveType__icontains='Sick Leave',
                                      created__icontains=(datetime.
                                                          date.
                                                          today().
                                                          year)
                                      ).aggregate(Sum('leaveCount'))
    totalCount = Leaves.objects.filter(author=request.user,
                                       created__icontains=(datetime.
                                                           date.
                                                           today().
                                                           year)
                                       ).aggregate(Sum('leaveCount'))
    dateJoined = datetime.date(request.user.date_joined.year,
                               request.user.date_joined.month,
                               request.user.date_joined.day)
    reg_Date = dateJoined + datetime.timedelta(days=183)

    if grpEmployees in request.user.groups.all():
        leaveCredits = 15
        sickLeave = leaveCredits
        vacationLeave = leaveCredits
        total_leave_credits = sickLeave + vacationLeave
    elif grpRegular in request.user.groups.all():
        end_of_month = cal.mdays[reg_Date.month]
        end_of_year = datetime.date(reg_Date.year, 12, 31)
        diff_days = (end_of_month - reg_Date.day) + 1
        diff_months = (end_of_year.month - reg_Date.month)

        leaveCredits = round((diff_months * 1.25) +
                             ((diff_days / 30.4167) * 1.25), 1)
        sickLeave = leaveCredits
        vacationLeave = leaveCredits
        total_leave_credits = sickLeave + vacationLeave
    else:
        sickLeave = 0
        vacationLeave = 0
        leaveCredits = 0
        total_leave_credits = 0

    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            global exclude_group
            name = request.user.username
            author = request.user
            email = request.user.email
            leaveType = form.cleaned_data['leaveType']
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            timeFrom = form.cleaned_data['timeFrom']
            timeTo = form.cleaned_data['timeTo']
            reason = form.cleaned_data['reason']
            status = 'None'
            department = str(request.user.groups.exclude(
                name__in=exclude_group
                ).first())
            if ((timeFrom is None) and (timeTo is None)):
                leaveCount = (datetime.date(dateTo.year,
                              dateTo.month, dateTo.day)
                              -
                              datetime.date(dateFrom.year,
                              dateFrom.month, dateFrom.day)).days + 1
            elif ((timeFrom is not None) and (timeTo is not None)):
                leaveCount = 0.5
            Leaves.objects.create(
                name=name, author=author, email=email,
                leaveType=leaveType, dateFrom=dateFrom, dateTo=dateTo,
                timeFrom=timeFrom, timeTo=timeTo, reason=reason,
                leaveCount=leaveCount, department=department, status=status,
            ).save()
            return HttpResponseRedirect('leave_filing')
    else:
        form = LeaveForm()
    return render(request,
                  'app_forms/Leaves/add_leave.html',
                  {'form': form,
                   'vacationCount': vacationCount,
                   'sickCount': sickCount,
                   'sickLeave': sickLeave,
                   'vacationLeave': vacationLeave,
                   'total_leave_credits': total_leave_credits,
                   'totalCount': totalCount,
                   'leaveCredits': leaveCredits,
                   'total_leave_credits': total_leave_credits})


@login_required
def leave_request(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    leaves = Leaves.objects.filter(author=request.user)
    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            status = form.cleaned_data['status']
            if status:
                leaves = Leaves.objects.filter(
                    author=request.user,
                    status=status
                ).order_by('dateFrom')
            if status == 'All':
                leaves = Leaves.objects.filter(
                    author=request.user,
                    status__icontains='e'
                ).order_by('dateFrom')
            if dateFrom:
                leaves = Leaves.objects.filter(
                    author=request.user,
                    dateFrom__range=(dateFrom, dateTo)
                ).order_by('dateFrom')
            if dateTo:
                leaves = Leaves.objects.filter(
                    author=request.user,
                    dateTo__range=(dateFrom, dateTo)
                ).order_by('dateFrom')
        else:
            form = FilterForm()
            leaves = Leaves.objects.filter(author=request.user)
    else:
        form = FilterForm()
        leaves = Leaves.objects.filter(author=request.user)
    return render(request,
                  'app_forms/Leaves/leave_request.html',
                  {'leaves': leaves,
                   'form': form})


@login_required
def leave_request_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    leaves = Leaves.objects.get(id=pk)
    # ON CLICK OF ENTRY, SHOW DETAILS
    return render(request,
                  'app_forms/Leaves/leave_request_details.html',
                  {'leaves': leaves})


@login_required
def leave_summary(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_summary_of_leave
    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            status = form.cleaned_data['status']
            if status:
                leaves = Leaves.objects.filter(
                    author=request.user,
                    status=status
                ).order_by('dateFrom')
            if dateFrom:
                leaves = Leaves.objects.filter(
                    author=request.user,
                    dateFrom__range=(dateFrom, dateTo)
                ).order_by('dateFrom')
            if dateTo:
                leaves = Leaves.objects.filter(
                    author=request.user,
                    dateTo__range=(dateFrom, dateTo)
                ).order_by('dateFrom')
            global_summary_of_leave = leaves
        else:
            form = FilterForm()
            leaves = Leaves.objects.filter(
                author=request.user
            )
            global_summary_of_leave = leaves
    else:
        form = FilterForm()
        leaves = Leaves.objects.filter(
            author=request.user
        )
        global_summary_of_leave = leaves
    return render(request,
                  'app_forms/Leaves/leave_summary.html',
                  {'form': form,
                   'leaves': leaves})
    return global_summary_of_leave


@login_required
def excel_summary_of_leaves(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_leave_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_Leaves')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True
    columns = ['Name', 'Leave Type',
               'Date From', 'Date To',
               'Time From', 'Time To',
               'Reason', 'Status',
               'Days', 'Remarks', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = global_summary_of_leave.values_list('name', 'leaveType',
                                               'dateFrom', 'dateTo',
                                               'timeFrom', 'timeTo',
                                               'reason', 'status',
                                               'leaveCount', 'remarks')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_summary_of_leaves(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_leave_reports.' + str(Now) + '.pdf'
    context = {"leaves": global_summary_of_leave,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/Leaves/pdf_template.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_summary_of_leaves(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_leave_reports.' + str(Now) + '.csv'
    leaves_resource = LeavesResource()
    queryset = global_summary_of_leave
    dataset = leaves_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_summary_of_leaves(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_leave_reports.' + str(Now) + '.json'
    leaves_resource = LeavesResource()
    queryset = global_summary_of_leave
    dataset = leaves_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.json, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def leave_approval(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global exclude_group, grpSupervisor, grpHRD, grpApprovers
    if grpHRD in request.user.groups.all():
            leaves = Leaves.objects.all()
    elif grpSupervisor or grpApprovers in request.user.groups.all():
            leaves = Leaves.objects.filter(
                department__icontains=request.user.groups.exclude(
                    name__in=exclude_group).first())

    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():  # SEARCH BUTTON
            searchBox = form.cleaned_data['searchBox']
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            if searchBox:
                if grpHRD in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        name__icontains=searchBox
                    ).order_by('dateFrom')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        name__icontains=searchBox,
                        department__icontains=request.user.groups.exclude(
                            name__in=exclude_group
                        ).first()).order_by('dateFrom')
            if dateFrom:
                if grpHRD in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        dateFrom__range=(dateFrom, dateTo)
                    ).order_by('dateFrom')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        dateFrom__range=(dateFrom, dateTo),
                        department__icontains=request.user.groups.exclude(
                            name__in=exclude_group
                        ).first()).order_by('dateFrom')
            if dateTo:
                if grpHRD in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        dateTo__range=(dateFrom, dateTo)
                    ).order_by('dateFrom')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        dateTo__range=(dateFrom, dateTo),
                        department__icontains=request.user.groups.exclude(
                            name__in=exclude_group
                        ).first()).order_by('dateFrom')
        else:
            form = SearchForm()
            if grpHRD in request.user.groups.all():
                leaves = Leaves.objects.all()
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                leaves = Leaves.objects.filter(
                    department__icontains=request.user.groups.exclude(
                        name__in=exclude_group).first())
    else:
        form = SearchForm()
        if grpHRD in request.user.groups.all():
            leaves = Leaves.objects.all()
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            leaves = Leaves.objects.filter(
                department__icontains=request.user.groups.exclude(
                    name__in=exclude_group).first())
    return render(request,
                  'app_forms/Leaves/leave_approval.html',
                  {'leaves': leaves,
                   'form': form})


@login_required
def leave_approval_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    leaves = Leaves.objects.get(id=pk)
    if request.method == 'POST':
        form = RemarksForm(request.POST)
        leaves = Leaves.objects.get(pk=pk)
        if form.is_valid():
            remarks = form.cleaned_data['remarks']
            status = form.cleaned_data['status']
            approvedBy = request.user.get_full_name()
            leaves.remarks = remarks
            leaves.status = status
            leaves.approvedBy = approvedBy
            leaves.save()
            status_email = ""
            if(status == 'False'):
                status_email = "declined"
            elif(status == 'True'):
                status_email = "approved"
            send_mail(
                'Request for Leave Approval',  # SUBJECT
                'Your ' + leaves.leaveType +
                ' ' + '(' + str(leaves.dateFrom) +
                ' - ' + str(leaves.dateTo) + ')' +
                ' has been ' + status_email +
                ' by ' + approvedBy,  # MESSAGE
                'E-Forms.electronicscience.com',  # FROM
                [leaves.email],  # TO
                fail_silently=False,
            )
        return HttpResponseRedirect('leave_approval')
    else:
        form = RemarksForm()
    return render(request,
                  'app_forms/Leaves/leave_approval_details.html',
                  {'leaves': leaves,
                   'form': form})


@login_required
def reports_leave(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_leave, grpSupervisor, grpApprovers, grpHRD, exclude_group
    department = str(request.user.groups.exclude(
                name__in=exclude_group
                ).first())
    if grpHRD in request.user.groups.all():
            leaves = Leaves.objects.all()
    elif grpSupervisor or grpApprovers in request.user.groups.all():
            leaves = Leaves.objects.filter(
                department__icontains=request.user.groups.exclude(
                    name__in=exclude_group).first())

    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            status = form.cleaned_data['status']
            if status:
                if grpHRD in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        status=status
                    ).order_by('dateFrom')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        status=status,
                        department__icontains=department
                    ).order_by('dateFrom')
            if status == 'All':
                if grpHRD in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        status__icontains='e'
                    ).order_by('dateFrom')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        status__icontains='e',
                        department__icontains=department
                    ).order_by('dateFrom')
            if dateFrom:
                if grpHRD in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        dateFrom__range=(dateFrom, dateTo)
                    ).order_by('dateFrom')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        dateFrom__range=(dateFrom, dateTo),
                        department__icontains=department
                    ).order_by('dateFrom')
            if dateTo:
                if grpHRD in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        dateTo__range=(dateFrom, dateTo)
                    ).order_by('dateFrom')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    leaves = Leaves.objects.filter(
                        dateTo__range=(dateFrom, dateTo),
                        department__icontains=department
                    ).order_by('dateFrom')
            global_leave = leaves
        else:
            form = FilterForm()
            if grpHRD in request.user.groups.all():
                leaves = Leaves.objects.all().order_by('dateFrom')
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                leaves = Leaves.objects.filter(
                    department__icontains=department
                ).order_by('dateFrom')
            global_leave = leaves
    else:
        form = FilterForm()
        if grpHRD in request.user.groups.all():
            leaves = Leaves.objects.all().order_by('dateFrom')
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            leaves = Leaves.objects.filter(
                department__icontains=department
            ).order_by('dateFrom')
        global_leave = leaves
    return render(request,
                  'app_forms/Leaves/reports_leave.html',
                  {'form': form,
                   'leaves': leaves,
                   'global_leave': global_leave})
    return global_leave


@login_required
def excel_leave(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'leave_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_Leaves')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True
    columns = ['Name', 'Leave Type',
               'Date From', 'Date To',
               'Time From', 'Time To',
               'Reason', 'Status',
               'Days', 'Remarks', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = global_leave.values_list('name', 'leaveType',
                                    'dateFrom', 'dateTo',
                                    'timeFrom', 'timeTo',
                                    'reason', 'status',
                                    'leaveCount', 'remarks')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_leave(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'leave_reports.' + str(Now) + '.pdf'
    context = {"leaves": global_leave,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/Leaves/pdf_template.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_leave(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'leave_reports.' + str(Now) + '.csv'
    leaves_resource = LeavesResource()
    queryset = global_leave
    dataset = leaves_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_leave(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'leave_reports.' + str(Now) + '.json'
    leaves_resource = LeavesResource()
    queryset = global_leave
    dataset = leaves_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.json, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def delete(request, pk):
    if request.method == 'DELETE':
        leave = get_object_or_404(Leaves, pk=pk)
        leave.delete()
    return HttpResponseRedirect('leave_filing')

# -----------------------------------------------------------------------------
# END OF LEAVE FILING
# -----------------------------------------------------------------------------

# -------------------------------F O R M A T-----------------------------------
#   * MAIN MODULE : CHANGE OF WORK SCHEDULE √
#   > EMPLOYEES <
#       > ADD CHANGE OF WORK SCHEDULE √
#           * add_change_of_work_schedule
#
#       > FILED CHANGE OF WORK SCHEDULE √
#           * change_of_work_schedule_request
#           * change_of_work_schedule_request_details/id
#
#       > CHANGE OF WORK SCHEDULE SUMMARY √
#           * change_of_work_schedule_summary
#           * excel_summary_of_change_of_work_schedule
#           * pdf_summary_of_change_of_work_schedule
#           * csv_summary_of_change_of_work_schedule
#           * json_summary_of_change_of_work_schedule
#
#   > SUPERVISOR / Approvers / HR <
#       > APPROVAL REQUESTS √
#           * change_of_work_schedule_approval
#           * change_of_work_schedule_approval_details/id
#
#       > REPORTS √
#           * reports_change_of_work_schedule
#           * excel_change_of_work_schedule
#           * pdf_change_of_work_schedule
#           * csv_change_of_work_schedule
#           * json_change_of_work_schedule
#       > DELETE √
#           * deleteChangeOfWorkSchedule
# -------------------------E N D--O F--F O R M A T-----------------------------

# -----------------------------------------------------------------------------
# CHANGE OF WORK SCHEDULE
# -----------------------------------------------------------------------------


@login_required
def change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    return render(request,
                  'app_forms/COWS/change_of_work_schedule.html')


@login_required
def add_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global group
    Usupervisor = ""
    Ugroup = ""
    Uname = ""
    for grps in groups:
        grpGroup = Group.objects.get(name=grps)
        if grpGroup in request.user.groups.all():
            group = str(grpGroup)
            grpUsers = User.objects.filter(
                groups=grpGroup
            )
            for users in grpUsers:
                if grpSupervisor in users.groups.all():
                    Usupervisor = users.get_full_name()
                    Ugroup = grpGroup
                    Uname = request.user.get_full_name()
    if request.method == 'POST':
        form = ChangeOfWorkScheduleForm(request.POST)
        if form.is_valid():
            name = Uname
            author = request.user
            department = str(Ugroup)
            fromDate = form.cleaned_data['fromDate']
            fromTimeFrom = form.cleaned_data['fromTimeFrom']
            fromTimeTo = form.cleaned_data['fromTimeTo']
            toDate = form.cleaned_data['toDate']
            toTimeFrom = form.cleaned_data['toTimeFrom']
            toTimeTo = form.cleaned_data['toTimeTo']
            reason = form.cleaned_data['reason']
            supervisor_name = Usupervisor
            status = 'None'
            ChangeOfWorkSchedule.objects.create(
                name=name, author=author, department=department,
                fromDate=fromDate, fromTimeFrom=fromTimeFrom,
                fromTimeTo=fromTimeTo, toDate=toDate, toTimeFrom=toTimeFrom,
                toTimeTo=toTimeTo, reason=reason, status=status,
                supervisor_name=supervisor_name,
            ).save()
        return HttpResponseRedirect('change_of_work_schedule')
    else:
        form = ChangeOfWorkScheduleForm()
    return render(request,
                  'app_forms/COWS/add_change_of_work_schedule.html',
                  {'form': form,
                   'Usupervisor': Usupervisor,
                   'Ugroup': Ugroup,
                   'Uname': Uname})


@login_required
def change_of_work_schedule_request(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    cows = ChangeOfWorkSchedule.objects.filter(
        name=request.user.get_full_name()
    )
    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            if dateFrom:
                cows = ChangeOfWorkSchedule.objects.filter(
                    author=request.user,
                    fromDate__range=(dateFrom, dateTo)
                ).order_by('fromDate')
            if dateTo:
                cows = ChangeOfWorkSchedule.objects.filter(
                    author=request.user,
                    toDate__range=(dateFrom, dateTo)
                ).order_by('fromDate')
        else:
            form = FilterForm()
            cows = ChangeOfWorkSchedule.objects.filter(
                name=request.user.get_full_name()
            )
    else:
        form = FilterForm()
        cows = ChangeOfWorkSchedule.objects.filter(
            name=request.user.get_full_name()
        )
    return render(request,
                  'app_forms/COWS/change_of_work_schedule_request.html',
                  {'cows': cows,
                   'form': form})


@login_required
def change_of_work_schedule_request_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    cows = ChangeOfWorkSchedule.objects.get(id=pk)
    # ON CLICK OF ENTRY, SHOW DETAILS
    return render(request,
                  'app_forms/COWS/' +
                  'change_of_work_schedule_request_details.html',
                  {'cows': cows})


@login_required
def change_of_work_schedule_summary(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_summary_of_change_of_work_schedule
    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            status = form.cleaned_data['status']
            if status:
                cows = ChangeOfWorkSchedule.objects.filter(
                    author=request.user,
                    status=status
                ).order_by('fromDate')
            if status == 'All':
                cows = ChangeOfWorkSchedule.objects.filter(
                    author=request.user,
                    status__icontains='e'
                ).order_by('fromDate')
            if dateFrom:
                cows = ChangeOfWorkSchedule.objects.filter(
                    author=request.user,
                    fromDate__range=(dateFrom, dateTo)
                ).order_by('fromDate')
            if dateTo:
                cows = ChangeOfWorkSchedule.objects.filter(
                    author=request.user,
                    toDate__range=(dateFrom, dateTo)
                ).order_by('fromDate')
            global_summary_of_change_of_work_schedule = cows
        else:
            form = FilterForm()
            cows = ChangeOfWorkSchedule.objects.filter(
                author=request.user
            ).order_by('fromDate')
            global_summary_of_change_of_work_schedule = cows
    else:
        form = FilterForm()
        cows = ChangeOfWorkSchedule.objects.filter(
            author=request.user
        ).order_by('fromDate')
        global_summary_of_change_of_work_schedule = cows
    return render(request,
                  'app_forms/COWS/change_of_work_schedule_summary.html',
                  {'form': form,
                   'cows': cows})
    return global_summary_of_change_of_work_schedule


@login_required
def excel_summary_of_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_change_of_work_schedule_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_ChangeofWorkSchedule')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True
    columns = ['Date From', 'Time From',
               'DaTime To', 'Date To',
               'Time From', 'Time To',
               'Reason', 'Status',
               'Remarks', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    row = global_summary_of_change_of_work_schedule.values_list('fromDate',
                                                                'fromTimeFrom',
                                                                'fromTimeTo',
                                                                'toDate',
                                                                'toTimeFrom',
                                                                'toTimeTo',
                                                                'reason',
                                                                'status',
                                                                'remarks')
    for rows in row:
        row_num += 1
        for col_num in range(len(rows)):
            ws.write(row_num, col_num, rows[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_summary_of_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_change_of_work_schedule_reports.' + str(Now) + '.pdf'
    context = {"cows": global_summary_of_change_of_work_schedule,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/COWS/pdf_template.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_summary_of_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_change_of_work_schedule_reports.' + str(Now) + '.csv'
    cows_resource = ChangeOfWorkScheduleResource()
    queryset = global_summary_of_change_of_work_schedule
    dataset = cows_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_summary_of_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_change_of_work_schedule_reports.' + str(Now) + '.json'
    cows_resource = ChangeOfWorkScheduleResource()
    queryset = global_summary_of_change_of_work_schedule
    dataset = cows_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.json, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def change_of_work_schedule_approval(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global exclude_group, grpSupervisor, grpHRD, grpApprovers
    if grpHRD in request.user.groups.all():
            cows = ChangeOfWorkSchedule.objects.all()
    elif grpSupervisor or grpApprovers in request.user.groups.all():
            cows = ChangeOfWorkSchedule.objects.filter(
                department__icontains=request.user.groups.exclude(
                    name__in=exclude_group).first())

    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():  # SEARCH BUTTON
            searchBox = form.cleaned_data['searchBox']
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            if searchBox:
                if grpHRD in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        name__icontains=searchBox
                    ).order_by('fromDate')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        name__icontains=searchBox,
                        department__icontains=request.user.groups.exclude(
                            name__in=exclude_group
                        ).first()).order_by('fromDate')
            if dateFrom:
                if grpHRD in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        fromDate__range=(dateFrom, dateTo)
                    ).order_by('fromDate')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        fromDate__range=(dateFrom, dateTo),
                        department__icontains=request.user.groups.exclude(
                            name__in=exclude_group
                        ).first()).order_by('fromDate')
            if dateTo:
                if grpHRD in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        toDate__range=(dateFrom, dateTo)
                    ).order_by('fromDate')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        toDate__range=(dateFrom, dateTo),
                        department__icontains=request.user.groups.exclude(
                            name__in=exclude_group
                        ).first()).order_by('fromDate')
        else:  # RESET BUTTON
            form = SearchForm()
            if grpHRD in request.user.groups.all():
                cows = ChangeOfWorkSchedule.objects.all()
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                cows = ChangeOfWorkSchedule.objects.filter(
                    department__icontains=request.user.groups.exclude(
                        name__in=exclude_group).first())
    else:
        if grpHRD in request.user.groups.all():
            form = SearchForm()
            cows = ChangeOfWorkSchedule.objects.all()
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            form = SearchForm()
            cows = ChangeOfWorkSchedule.objects.filter(
                department__icontains=request.user.groups.exclude(
                    name__in=exclude_group).first())
    return render(request,
                  'app_forms/COWS/change_of_work_schedule_approval.html',
                  {'cows': cows,
                   'form': form})


@login_required
def change_of_work_schedule_approval_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    cows = ChangeOfWorkSchedule.objects.get(id=pk)
    if request.method == 'POST':
        form = RemarksForm(request.POST)
        cows = ChangeOfWorkSchedule.objects.get(pk=pk)
        if form.is_valid():
            remarks = form.cleaned_data['remarks']
            status = form.cleaned_data['status']
            approvedBy = request.user.get_full_name()
            cows.remarks = remarks
            cows.status = status
            cows.approvedBy = approvedBy
            cows.dateApproved = datetime.date.today()
            cows.save()
            get_user = User.objects.get(
                username=cows.author
            )
            get_user_email = get_user.email
            status_email = ""
            if(status == 'False'):
                status_email = "declined"
            elif(status == 'True'):
                status_email = "approved"
            send_mail(
                'Request for Change Of Work Schedule Approval',  # SUBJECT
                'Your request for Change of Work Schedule :' +
                '\n Date : ' + str(cows.fromDate) +
                '\n Time From : ' + str(cows.fromTimeFrom) +
                '\n Time To : ' + str(cows.fromTimeTo) +
                '\n \n ------------------T 0--------------------- \n' +
                '\n Date : ' + str(cows.toDate) +
                '\n Time From : ' + str(cows.toTimeFrom) +
                '\n Time To : ' + str(cows.toTimeTo) +
                '\n has been ' + status_email +
                ' by ' + approvedBy,  # MESSAGE
                'E-Forms.electronicscience.com',  # FROM
                [get_user_email],  # TO
                fail_silently=False,
            )
        return HttpResponseRedirect('change_of_work_schedule_approval')
    else:
        form = RemarksForm()
    return render(request,
                  'app_forms/COWS/' +
                  'change_of_work_schedule_approval_details.html',
                  {'cows': cows,
                   'form': form})


@login_required
def reports_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_c_o_w_s, grpSupervisor, grpApprovers, grpHRD
    department = str(request.user.groups.exclude(
                name__in=exclude_group).first())
    if grpHRD in request.user.groups.all():
            cows = ChangeOfWorkSchedule.objects.all().order_by('fromDate')
    elif grpSupervisor or grpApprovers in request.user.groups.all():
            cows = ChangeOfWorkSchedule.objects.filter(
                department=department
            ).order_by('fromDate')

    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            status = form.cleaned_data['status']
            if status:
                if grpHRD in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        status=status
                    ).order_by('fromDate')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        status=status,
                        department=department
                    ).order_by('fromDate')
            if status == 'All':
                if grpHRD in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        status__icontains='e'
                    ).order_by('fromDate')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        status__icontains='e',
                        department=department
                    ).order_by('fromDate')
            if dateFrom:
                if grpHRD in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        fromDate__range=(dateFrom, dateTo)
                    ).order_by('fromDate')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        fromDate__range=(dateFrom, dateTo),
                        department=department
                    ).order_by('fromDate')
            if dateTo:
                if grpHRD in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        toDate__range=(dateFrom, dateTo)
                    ).order_by('fromDate')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    cows = ChangeOfWorkSchedule.objects.filter(
                        toDate__range=(dateFrom, dateTo),
                        department=department
                    ).order_by('fromDate')
            global_c_o_w_s = cows
        else:
            form = FilterForm()
            if grpHRD in request.user.groups.all():
                cows = ChangeOfWorkSchedule.objects.all().order_by('fromDate')
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                cows = ChangeOfWorkSchedule.objects.filter(
                    department=department
                ).order_by('fromDate')
            global_c_o_w_s = cows
    else:
        form = FilterForm()
        if grpHRD in request.user.groups.all():
            cows = ChangeOfWorkSchedule.objects.all().order_by('fromDate')
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            cows = ChangeOfWorkSchedule.objects.filter(
                department=department
            ).order_by('fromDate')
        global_c_o_w_s = cows
    return render(request,
                  'app_forms/COWS/reports_change_of_work_schedule.html',
                  {'form': form,
                   'cows': cows,
                   'global_c_o_w_s': global_c_o_w_s})
    return global_c_o_w_s


@login_required
def excel_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'change_of_work_schedule_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_Change_Of_Work_Schedule')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True

    columns = ['Name', 'Date From',
               'Time From', 'Time To',
               'Date To', 'Time From',
               'Time To', 'Reason',
               'Status', 'Remarks', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = global_c_o_w_s.values_list('name', 'fromDate',
                                      'fromTimeFrom', 'fromTimeTo',
                                      'toDate', 'toTimeFrom',
                                      'toTimeTo', 'reason',
                                      'status', 'remarks')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'change_of_work_schedule_reports.' + str(Now) + '.pdf'
    context = {"cows": global_c_o_w_s,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/COWS/pdf_template.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'change_of_work_schedule_reports.' + str(Now) + '.csv'
    cows_resource = ChangeOfWorkScheduleResource()
    queryset = global_c_o_w_s
    dataset = cows_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_change_of_work_schedule(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'change_of_work_schedule_reports.' + str(Now) + '.json'
    cows_resource = ChangeOfWorkScheduleResource()
    queryset = global_c_o_w_s
    dataset = cows_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.json, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def deleteChangeOfWorkSchedule(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    if request.method == 'DELETE':
        cow = get_object_or_404(ChangeOfWorkSchedule, pk=pk)
        cow.delete()
    return HttpResponseRedirect('change_of_work_schedule')

# -----------------------------------------------------------------------------
# END OF CHANGE OF WORK SCHEDULE
# -----------------------------------------------------------------------------

# -------------------------------F O R M A T-----------------------------------
#   * MAIN MODULE : PRODUCTIVITY TOOL √
#   > EMPLOYEES <
#       > ADD PRODUCTIVITY TOOL √
#           * add_productivity_tool
#
#       > FILED PRODUCTIVITY TOOL √
#           * productivity_tool_request
#           * productivity_tool_request_details/id
#
#       > PRODUCTIVITY TOOL SUMMARY √
#           * productivity_tool_summary
#           * excel_summary_of_productivity_tool
#           * pdf_summary_of_productivity_tool
#           * csv_summary_of_productivity_tool
#           * json_summary_of_productivity_tool
#
#   > SUPERVISOR / Approvers / HR <
#       > APPROVAL REQUESTS √
#           * productivity_tool_approval
#           * productivity_tool_approval_details/id
#
#       > REPORTS
#           * reports_productivity_tool
#           * excel_productivity_tool
#           * pdf_productivity_tool
#           * csv_productivity_tool
#           * json_productivity_tool
#       > DELETE √
#           * deleteProductivityTool
# -------------------------E N D--O F--F O R M A T-----------------------------

# -----------------------------------------------------------------------------
# PRODUCTIVITY TOOL
# -----------------------------------------------------------------------------


@login_required
def productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    dateValid = datetime.date(request.user.date_joined.year+1,
                              request.user.date_joined.month,
                              request.user.date_joined.day)
    if dateValid <= Now:
        validity = "yes"
    else:
        validity = "no"
    return render(request,
                  'app_forms/ProductivityTool/productivity_tool.html',
                  {'validity': validity})


@login_required
def add_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    if request.method == 'POST':
        form = ProductivityToolForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            department = str(request.user.groups.exclude(
                name__in=exclude_group).first())
            prodTool = form.cleaned_data['prodTool']
            price = form.cleaned_data['price']
            reasons = form.cleaned_data['reasons']
            author = request.user
            status = 'None'
            ProductivityTool.objects.create(
                name=name, author=author, department=department,
                prodTool=prodTool, price=price,
                reasons=reasons, status=status,
            ).save()
        return HttpResponseRedirect('productivity_tool')
    else:
        form = ProductivityToolForm()
    return render(request,
                  'app_forms/ProductivityTool/add_productivity_tool.html',
                  {'form': form})


@login_required
def productivity_tool_request(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    prodtool = ProductivityTool.objects.filter(author=request.user)
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            sBox = form.cleaned_data['searchBox']
            if sBox:
                prodtool = ProductivityTool.objects.filter(
                    prodTool__icontains=sBox,
                    author=request.user
                ).order_by('dateApproved')
        else:
            form = SearchForm()
            prodtool = ProductivityTool.objects.filter(author=request.user)
    else:
        form = SearchForm()
        prodtool = ProductivityTool.objects.filter(author=request.user)
    return render(request,
                  'app_forms/ProductivityTool/productivity_tool_request.html',
                  {'prodtool': prodtool,
                   'form': form})


@login_required
def productivity_tool_request_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    prodtool = ProductivityTool.objects.get(id=pk)
    # ON CLICK OF ENTRY, SHOW DETAILS
    return render(request,
                  'app_forms/ProductivityTool/' +
                  'productivity_tool_request_details.html',
                  {'prodtool': prodtool})


@login_required
def productivity_tool_summary(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_summary_of_prodtool
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            sBox = form.cleaned_data['searchBox']
            if sBox:
                prodtool = ProductivityTool.objects.filter(
                    prodTool__icontains=sBox,
                    author=request.user
                ).order_by('dateApproved')
            global_summary_of_prodtool = prodtool
        else:
            prodtool = ProductivityTool.objects.filter(
                name=request.user.get_full_name()
            ).order_by('dateApproved')
            global_summary_of_prodtool = prodtool
    else:
        form = SearchForm()
        prodtool = ProductivityTool.objects.filter(
            name=request.user.get_full_name()
        ).order_by('dateApproved')
        global_summary_of_prodtool = prodtool
    return render(request,
                  'app_forms/ProductivityTool/productivity_tool_summary.html',
                  {'form': form,
                   'prodtool': prodtool})
    return global_summary_of_prodtool


@login_required
def excel_summary_of_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_of_productivity_tool_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_Productivity_Tool')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True
    columns = ['Name', 'Productivity Tool',
               'Price', 'Reason/s',
               'Status', 'Date Approved',
               'Approved By', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = global_summary_of_prodtool.values_list('name', 'prodTool',
                                                  'price', 'reasons',
                                                  'status', 'dateApproved',
                                                  'approvedBy')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_summary_of_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_of_productivity_tool_reports.' + str(Now) + '.pdf'
    context = {"prodtool": global_summary_of_prodtool,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/ProductivityTool/pdf_template.html',
                        context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_summary_of_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_of_productivity_tool_reports.' + str(Now) + '.csv'
    prodtool_resource = ProductivityToolResource()
    queryset = global_summary_of_prodtool
    dataset = prodtool_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_summary_of_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_of_productivity_tool_reports.' + str(Now) + '.json'
    prodtool_resource = ProductivityToolResource()
    queryset = global_summary_of_prodtool
    dataset = prodtool_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.json, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def productivity_tool_approval(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global exclude_group, grpSupervisor, grpHRD, grpApprovers
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():  # SEARCH BUTTON
            searchBox = form.cleaned_data['searchBox']
            if searchBox:
                if grpHRD in request.user.groups.all():
                    prodtool = ProductivityTool.objects.filter(
                        name__icontains=searchBox
                    ).order_by('created')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    form = SearchForm()
                    prodtool = ProductivityTool.objects.filter(
                        name__icontains=searchBox,
                        department__icontains=request.user.groups.exclude(
                            name__in=exclude_group
                        ).first()).order_by('dateApproved')
        else:  # RESET BUTTON
            form = SearchForm()
            if grpHRD in request.user.groups.all():
                prodtool = ProductivityTool.objects.all()
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                prodtool = ProductivityTool.objects.filter(
                    department__icontains=request.user.groups.exclude(
                        name__in=exclude_group
                    ).first()).order_by('dateApproved')
    else:
        form = SearchForm()
        if grpHRD in request.user.groups.all():
            prodtool = ProductivityTool.objects.all()
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            prodtool = ProductivityTool.objects.filter(
                department__icontains=request.user.groups.exclude(
                    name__in=exclude_group).first())
    return render(request,
                  'app_forms/ProductivityTool/productivity_tool_approval.html',
                  {'prodtool': prodtool,
                   'form': form})


@login_required
def productivity_tool_approval_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    prodtool = ProductivityTool.objects.get(id=pk)
    if request.method == 'POST':
        form = RemarksForm(request.POST)
        prodtool = ProductivityTool.objects.get(pk=pk)
        if form.is_valid():
            remarks = form.cleaned_data['remarks']
            status = form.cleaned_data['status']
            approvedBy = request.user.get_full_name()
            prodtool.remarks = remarks
            prodtool.status = status
            prodtool.approvedBy = approvedBy
            prodtool.dateApproved = datetime.date.today()
            prodtool.save()
            get_user = User.objects.get(
                username=prodtool.author
            )
            get_user_email = get_user.email
            status_email = ""
            if(status == 'False'):
                status_email = "declined"
            elif(status == 'True'):
                status_email = "approved"
            send_mail(
                'Request for Productivity Tool Approval',  # SUBJECT
                'Your request for Productivity Tool :' +
                '\n Name : ' + str(prodtool.name) +
                '\n Productivity Tool : ' + str(prodtool.prodTool) +
                '\n Price : ' + str(prodtool.price) +
                '\n Reason/s : ' + str(prodtool.reasons) +
                '\n has been ' + status_email +
                ' by ' + approvedBy,  # MESSAGE
                'E-Forms.electronicscience.com',  # FROM
                [get_user_email],  # TO
                fail_silently=False,
            )
        return HttpResponseRedirect('productivity_tool_approval')
    else:
        form = RemarksForm()
    return render(request,
                  'app_forms/ProductivityTool/' +
                  'productivity_tool_approval_details.html',
                  {'prodtool': prodtool,
                   'form': form})


@login_required
def reports_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_prodtool, grpSupervisor, grpHRD
    department = str(request.user.groups.exclude(
                name__in=exclude_group).first())
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            sBox = form.cleaned_data['searchBox']
            if sBox:
                if grpHRD in request.user.groups.all():
                    prodtool = ProductivityTool.objects.filter(
                        name__icontains=sBox).order_by('created')
                elif grpSupervisor in request.user.groups.all():
                    prodtool = ProductivityTool.objects.filter(
                        name__icontains=sBox,
                        department=department
                    ).order_by('created')
            global_prodtool = prodtool
        else:
            if grpHRD in request.user.groups.all():
                prodtool = ProductivityTool.objects.all().order_by('created')
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                prodtool = ProductivityTool.objects.filter(
                    department=department
                ).order_by('created')
            global_prodtool = prodtool
    else:
        form = SearchForm()
        if grpHRD in request.user.groups.all():
            prodtool = ProductivityTool.objects.all().order_by('created')
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            prodtool = ProductivityTool.objects.filter(
                department=department
            ).order_by('created')
        global_prodtool = prodtool
    return render(request,
                  'app_forms/ProductivityTool/reports_productivity_tool.html',
                  {'form': form,
                   'prodtool': prodtool,
                   'global_prodtool': global_prodtool})
    return global_prodtool


@login_required
def excel_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'productivity_tool_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_Productivity_Tool')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True
    columns = ['Name', 'Productivity Tool',
               'Price', 'Reason/s',
               'Status', 'Date Approved',
               'Approved By', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = global_prodtool.values_list('name', 'prodTool',
                                       'price', 'reasons',
                                       'status', 'dateApproved',
                                       'approvedBy')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'productivity_tool_reports.' + str(Now) + '.pdf'
    context = {"prodtool": global_prodtool,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/ProductivityTool/pdf_template.html',
                        context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'productivity_tool_reports.' + str(Now) + '.csv'
    prodtool_resource = ProductivityToolResource()
    queryset = global_prodtool
    dataset = prodtool_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_productivity_tool(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'productivity_tool_reports.' + str(Now) + '.json'
    prodtool_resource = ProductivityToolResource()
    queryset = global_prodtool
    dataset = prodtool_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.csv, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def deleteProductivityTool(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    if request.method == 'DELETE':
        prodtool = get_object_or_404(ProductivityTool, pk=pk)
        prodtool.delete()
    return HttpResponseRedirect('productivity_tool')

# -----------------------------------------------------------------------------
# END OF PRODUCTIVITY TOOL
# -----------------------------------------------------------------------------

# -------------------------------F O R M A T-----------------------------------
#   * MAIN MODULE : OVERTIME √
#   > EMPLOYEES <
#       > ADD OVERTIME √
#           * add_overtime
#
#       > FILED OVERTIME
#           * overtime_request
#           * overtime_request_details/id
#
#       > OVERTIME SUMMARY
#           * overtime_summary
#           * excel_summary_of_overtime
#           * pdf_summary_of_overtime
#           * csv_summary_of_overtime
#           * json_summary_of_overtime
#
#   > SUPERVISOR / Approvers / HR <
#       > APPROVAL REQUESTS
#           * overtime_approval
#           * overtime_approval_details/id
#
#       > REPORTS
#           * reports_overtime
#           * excel_overtime
#           * pdf_overtime
#           * csv_overtime
#           * json_overtime
#       > DELETE √
#           * deleteOvertime
# -------------------------E N D--O F--F O R M A T-----------------------------

# -----------------------------------------------------------------------------
# OVERTIME
# -----------------------------------------------------------------------------


@login_required
def overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    return render(request,
                  'app_forms/Overtime/overtime.html')


@login_required
def add_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    name = request.user.get_full_name()
    if request.method == 'POST':
        form = OvertimeForm(request.POST)
        if form.is_valid():
            dateFiled = datetime.date.today()
            author = request.user
            department = form.cleaned_data['department']
            date_ot = form.cleaned_data['date_ot']
            timeFrom = form.cleaned_data['timeFrom']
            timeTo = form.cleaned_data['timeTo']
            num_of_hrs = form.cleaned_data['num_of_hrs']
            reason = form.cleaned_data['reason']
            project_name = form.cleaned_data['project_name']
            status = 'None'
            Overtime.objects.create(
                dateFiled=dateFiled,
                name=name, author=author, department=department,
                date_ot=date_ot, num_of_hrs=num_of_hrs,
                timeFrom=timeFrom, timeTo=timeTo,
                reason=reason, project_name=project_name,
                status=status,
            ).save()
            return HttpResponseRedirect('overtime')
    else:
        form = OvertimeForm()
    return render(request,
                  'app_forms/Overtime/add_overtime.html',
                  {'form': form,
                   'name': name})


@login_required
def overtime_request(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    ots = Overtime.objects.filter(author=request.user)
    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            if dateFrom:
                ots = Overtime.objects.filter(
                    author=request.user,
                    date_ot__range=(dateFrom, dateTo)
                ).order_by('date_ot')
            if dateTo:
                ots = Overtime.objects.filter(
                    author=request.user,
                    date_ot__range=(dateFrom, dateTo)
                ).order_by('date_ot')
        else:
            form = FilterForm()
            ots = Overtime.objects.filter(author=request.user)
    else:
        form = FilterForm()
        ots = Overtime.objects.filter(author=request.user)
    return render(request,
                  'app_forms/Overtime/overtime_request.html',
                  {'ots': ots,
                   'form': form})


@login_required
def overtime_request_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    ots = Overtime.objects.get(id=pk)
    # ON CLICK OF ENTRY, SHOW DETAILS
    return render(request,
                  'app_forms/Overtime/overtime_request_details.html',
                  {'ots': ots})


@login_required
def overtime_summary(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_summary_of_ot
    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            status = form.cleaned_data['status']
            if status:
                ots = Overtime.objects.filter(
                    author=request.user,
                    status=status
                ).order_by('date_ot')
            if status == 'All':
                ots = Overtime.objects.filter(
                    author=request.user,
                    status__icontains='e'
                ).order_by('date_ot')
            if dateFrom:
                ots = Overtime.objects.filter(
                    author=request.user,
                    date_ot__range=(dateFrom, dateTo)
                ).order_by('date_ot')
            if dateTo:
                ots = Overtime.objects.filter(
                    author=request.user,
                    date_ot__range=(dateFrom, dateTo)
                ).order_by('date_ot')
            global_summary_of_ot = ots
        else:
            form = FilterForm()
            ots = Overtime.objects.filter(
                author=request.user
            ).order_by('date_ot')
            global_summary_of_ot = ots
    else:
        form = FilterForm()
        ots = Overtime.objects.filter(
            author=request.user
        ).order_by('date_ot')
        global_summary_of_ot = ots
    return render(request,
                  'app_forms/Overtime/overtime_summary.html',
                  {'form': form,
                   'ots': ots})
    return global_summary_of_ot


@login_required
def excel_summary_of_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_overtime_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_Overtime')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True
    columns = ['Date Filed', 'Name',
               'Department', 'Date overtime',
               'Time From', 'Time To',
               'Number of Hours', 'Project',
               'Reason', 'Status',
               'Approved By', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = global_summary_of_ot.values_list('dateFiled', 'name',
                                            'department', 'date_ot',
                                            'timeFrom', 'timeTo',
                                            'num_of_hrs', 'project_name',
                                            'reason', 'status',
                                            'approvedBy')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_summary_of_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_overtime_reports.' + str(Now) + '.pdf'
    context = {"overtime": global_summary_of_ot,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/Overtime/pdf_template.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_summary_of_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_overtime_reports.' + str(Now) + '.csv'
    overtime_resource = OvertimeResource()
    queryset = global_summary_of_ot
    dataset = overtime_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_summary_of_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_overtime_reports.' + str(Now) + '.json'
    overtime_resource = OvertimeResource()
    queryset = global_summary_of_ot
    dataset = overtime_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.json, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def overtime_approval(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global exclude_group, grpSupervisor, grpHRD, grpApprovers
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():  # SEARCH BUTTON
            searchBox = form.cleaned_data['searchBox']
            if searchBox:
                if grpHRD in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        name__icontains=searchBox
                    ).order_by('date_ot')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        name__icontains=searchBox,
                        department__icontains=request.user.groups.exclude(
                            name__in=exclude_group
                        ).first()).order_by('date_ot')
        else:  # RESET BUTTON
            form = SearchForm()
            if grpHRD in request.user.groups.all():
                ots = Overtime.objects.all()
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                ots = Overtime.objects.filter(
                    department__icontains=request.user.groups.exclude(
                        name__in=exclude_group).first())
    else:
        form = SearchForm()
        if grpHRD in request.user.groups.all():
            ots = Overtime.objects.all()
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            ots = Overtime.objects.filter(
                department__icontains=request.user.groups.exclude(
                    name__in=exclude_group).first())
    return render(request,
                  'app_forms/Overtime/overtime_approval.html',
                  {'ots': ots,
                   'form': form})


@login_required
def overtime_approval_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    ots = Overtime.objects.get(id=pk)
    if request.method == 'POST':
        form = RemarksForm(request.POST)
        ots = Overtime.objects.get(pk=pk)
        if form.is_valid():
            remarks = form.cleaned_data['remarks']
            status = form.cleaned_data['status']
            approvedBy = request.user.get_full_name()
            ots.remarks = remarks
            ots.status = status
            ots.approvedBy = approvedBy
            ots.dateApproved = datetime.date.today()
            ots.save()
            get_user = User.objects.get(
                username=ots.author
            )
            get_user_email = get_user.email
            status_email = ""
            if(status == 'False'):
                status_email = "declined"
            elif(status == 'True'):
                status_email = "approved"
            send_mail(
                'Request for Overtime Approval',  # SUBJECT
                'Your request for Overtime :' +
                '\n Date : ' + str(ots.date_ot) +
                '\n Project : ' + str(ots.project_name) +
                '\n Number of Hours : ' + str(ots.num_of_hrs) +
                '\n has been ' + status_email +
                ' by ' + approvedBy,  # MESSAGE
                'E-Forms.electronicscience.com',  # FROM
                [get_user_email],  # TO
                fail_silently=False,
            )
        return HttpResponseRedirect('overtime_approval')
    else:
        form = RemarksForm()
    return render(request,
                  'app_forms/Overtime/overtime_approval_details.html',
                  {'ots': ots,
                   'form': form})


@login_required
def reports_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_ot, grpSupervisor, grpApprovers, grpHRD
    department = str(request.user.groups.exclude(
                name__in=exclude_group).first())
    if grpHRD in request.user.groups.all():
                    ots = Overtime.objects.all().order_by('date_ot')
    elif grpSupervisor or grpApprovers in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        department=department
                    ).order_by('date_ot')

    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            status = form.cleaned_data['status']
            if status:
                if grpHRD in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        status=status
                    ).order_by('date_ot')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        status=status,
                        department=department
                    ).order_by('date_ot')
            if status == 'All':
                if grpHRD in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        date_ot__range=(dateFrom, dateTo),
                        status__icontains='e'
                    ).order_by('date_ot')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        date_ot__range=(dateFrom, dateTo),
                        status__icontains='e',
                        department=department
                    ).order_by('date_ot')
            if dateFrom:
                if grpHRD in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        date_ot__range=(dateFrom, dateTo)
                    ).order_by('date_ot')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        date_ot__range=(dateFrom, dateTo),
                        department=department
                    ).order_by('date_ot')
            if dateTo:
                if grpHRD in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        date_ot__range=(dateFrom, dateTo)
                    ).order_by('date_ot')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    ots = Overtime.objects.filter(
                        date_ot__range=(dateFrom, dateTo),
                        department=department
                    ).order_by('date_ot')
            global_ot = ots
        else:
            form = FilterForm()
            if grpHRD in request.user.groups.all():
                ots = Overtime.objects.all().order_by('date_ot')
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                ots = Overtime.objects.filter(
                    department=department
                ).order_by('date_ot')
            global_ot = ots
    else:
        form = FilterForm()
        if grpHRD in request.user.groups.all():
            ots = Overtime.objects.all().order_by('date_ot')
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            ots = Overtime.objects.filter(
                department=department
            ).order_by('date_ot')
        global_ot = ots
    return render(request,
                  'app_forms/Overtime/reports_overtime.html',
                  {'form': form,
                   'ots': ots,
                   'global_ot': global_ot})
    return global_ot


@login_required
def excel_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'overtime_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_Overtime')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True
    columns = ['Date Filed', 'Name',
               'Department', 'Date Overtime',
               'Number of Hours', 'Project',
               'Reason', 'Status',
               'Approved By', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = global_ot.values_list('dateFiled', 'name',
                                 'department', 'date_ot',
                                 'num_of_hrs', 'project_name',
                                 'reason', 'status',
                                 'approvedBy')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'overtime_reports.' + str(Now) + '.pdf'
    context = {"overtime": global_ot,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/Overtime/pdf_template.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    if user.mfa_code is not None:
        return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'overtime_reports.' + str(Now) + '.csv'
    overtime_resource = OvertimeResource()
    queryset = global_ot
    dataset = overtime_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_overtime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'overtime_reports.' + str(Now) + '.json'
    overtime_resource = OvertimeResource()
    queryset = global_ot
    dataset = overtime_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.json, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def deleteOvertime(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    if request.method == 'DELETE':
        ots = get_object_or_404(Overtime, pk=pk)
        ots.delete()
    return HttpResponseRedirect('overtime')

# -----------------------------------------------------------------------------
# END OF OVERTIME
# -----------------------------------------------------------------------------

# -------------------------------F O R M A T-----------------------------------
#   * MAIN MODULE : UNDERTIME
#   > EMPLOYEES <
#       > ADD UNDERTIME
#           * add_undertime
#
#       > FILED UNDERTIME
#           * undertime_request
#           * undertime_request_details/id
#
#       > UNDERTIME SUMMARY
#           * undertime_summary
#           * excel_summary_of_undertime
#           * pdf_summary_of_undertime
#           * csv_summary_of_undertime
#           * json_summary_of_undertime
#
#   > SUPERVISOR / TEAM LEAD / HR <
#       > APPROVAL REQUESTS
#           * undertime_approval
#           * undertime_approval_details/id
#
#       > REPORTS
#           * reports_undertime
#           * excel_undertime
#           * pdf_undertime
#           * csv_undertime
#           * json_undertime
#       > DELETE √
#           * deleteUndertime
# -------------------------E N D--O F--F O R M A T-----------------------------

# -----------------------------------------------------------------------------
# UNDERTIME
# -----------------------------------------------------------------------------


@login_required
def undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    return render(request,
                  'app_forms/Undertime/undertime.html')


@login_required
def add_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    name = request.user.get_full_name()
    if request.method == 'POST':
        form = UndertimeForm(request.POST)
        if form.is_valid():
            dateFiled = datetime.date.today()
            author = request.user
            department = form.cleaned_data['department']
            date_ut = form.cleaned_data['date_ut']
            timeFrom = form.cleaned_data['timeFrom']
            timeTo = form.cleaned_data['timeTo']
            num_of_hrs = form.cleaned_data['num_of_hrs']
            reason = form.cleaned_data['reason']
            status = 'None'
            Undertime.objects.create(
                dateFiled=dateFiled,
                name=name, author=author, department=department,
                date_ut=date_ut, num_of_hrs=num_of_hrs,
                timeFrom=timeFrom, timeTo=timeTo,
                reason=reason, status=status,
            ).save()
            return HttpResponseRedirect('undertime')
    else:
        form = UndertimeForm()
    return render(request,
                  'app_forms/Undertime/add_undertime.html',
                  {'form': form,
                   'name': name})


@login_required
def undertime_request(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    uts = Undertime.objects.filter(author=request.user)
    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            if dateFrom:
                uts = Undertime.objects.filter(
                    author=request.user,
                    date_ut__range=(dateFrom, dateTo)
                ).order_by('date_ut')
            if dateTo:
                uts = Undertime.objects.filter(
                    author=request.user,
                    date_ut__range=(dateFrom, dateTo)
                ).order_by('date_ut')
        else:
            form = FilterForm()
            uts = Undertime.objects.filter(author=request.user)
    else:
        form = FilterForm()
        uts = Undertime.objects.filter(author=request.user)
    return render(request,
                  'app_forms/Undertime/undertime_request.html',
                  {'uts': uts,
                   'form': form})


@login_required
def undertime_request_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    uts = Undertime.objects.get(id=pk)
    # ON CLICK OF ENTRY, SHOW DETAILS
    return render(request,
                  'app_forms/Undertime/undertime_request_details.html',
                  {'uts': uts})


@login_required
def undertime_summary(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_summary_of_ut
    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            status = form.cleaned_data['status']
            if status:
                uts = Undertime.objects.filter(
                    author=request.user,
                    status=status
                ).order_by('date_ut')
            if status == 'All':
                uts = Undertime.objects.filter(
                    author=request.user,
                    status__icontains='e'
                ).order_by('date_ut')
            if dateFrom:
                uts = Undertime.objects.filter(
                    author=request.user,
                    date_ut__range=(dateFrom, dateTo)
                ).order_by('date_ut')
            if dateTo:
                uts = Undertime.objects.filter(
                    author=request.user,
                    date_ut__range=(dateFrom, dateTo)
                ).order_by('date_ut')
            global_summary_of_ut = uts
        else:
            form = FilterForm()
            uts = Undertime.objects.filter(
                author=request.user
            ).order_by('date_ut')
            global_summary_of_ut = uts
    else:
        form = FilterForm()
        uts = Undertime.objects.filter(
            author=request.user
        ).order_by('date_ut')
        global_summary_of_ut = uts
    return render(request,
                  'app_forms/Undertime/undertime_summary.html',
                  {'form': form,
                   'uts': uts})
    return global_summary_of_ut


@login_required
def excel_summary_of_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_undertime_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_Undertime')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True
    columns = ['Date Filed', 'Name',
               'Department', 'Date Undertime',
               'Time From', 'Time To'
               'Number of Hours', 'Reason',
               'Status', 'Approved By', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = global_summary_of_ut.values_list('dateFiled', 'name',
                                            'department', 'date_ut',
                                            'timeFrom', 'timeTo',
                                            'num_of_hrs', 'reason',
                                            'status', 'approvedBy')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_summary_of_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_undertime_reports.' + str(Now) + '.pdf'
    context = {"undertime": global_summary_of_ut,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/Undertime/pdf_template.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_summary_of_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_undertime_reports.' + str(Now) + '.csv'
    undertime_resource = UndertimeResource()
    queryset = global_summary_of_ut
    dataset = undertime_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_summary_of_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'summary_undertime_reports.' + str(Now) + '.json'
    undertime_resource = UndertimeResource()
    queryset = global_summary_of_ut
    dataset = undertime_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.json, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def undertime_approval(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global exclude_group, grpSupervisor, grpHRD, grpApprovers
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():  # SEARCH BUTTON
            searchBox = form.cleaned_data['searchBox']
            if searchBox:
                if grpHRD in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        name__icontains=searchBox
                    ).order_by('date_ut')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        name__icontains=searchBox,
                        department__icontains=request.user.groups.exclude(
                            name__in=exclude_group
                        ).first()).order_by('date_ut')
        else:  # RESET BUTTON
            if grpHRD in request.user.groups.all():
                form = SearchForm()
                uts = Undertime.objects.all()
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                form = SearchForm()
                uts = Undertime.objects.filter(
                    department__icontains=request.user.groups.exclude(
                        name__in=exclude_group).first())
    else:
        if grpHRD in request.user.groups.all():
            form = SearchForm()
            uts = Undertime.objects.all()
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            form = SearchForm()
            uts = Undertime.objects.filter(
                department__icontains=request.user.groups.exclude(
                    name__in=exclude_group).first())
    return render(request,
                  'app_forms/Undertime/undertime_approval.html',
                  {'uts': uts,
                   'form': form})


@login_required
def undertime_approval_details(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    uts = Undertime.objects.get(id=pk)
    if request.method == 'POST':
        form = RemarksForm(request.POST)
        uts = Undertime.objects.get(pk=pk)
        if form.is_valid():
            remarks = form.cleaned_data['remarks']
            status = form.cleaned_data['status']
            approvedBy = request.user.get_full_name()
            uts.remarks = remarks
            uts.status = status
            uts.approvedBy = approvedBy
            uts.dateApproved = datetime.date.today()
            uts.save()
            get_user = User.objects.get(
                username=uts.author
            )
            get_user_email = get_user.email
            status_email = ""
            if(status == 'False'):
                status_email = "declined"
            elif(status == 'True'):
                status_email = "approved"
            send_mail(
                'Request for Undertime Approval',  # SUBJECT
                'Your request for Undertime :' +
                '\n Date : ' + str(uts.date_ut) +
                '\n Number of Hours : ' + str(uts.num_of_hrs) +
                '\n has been ' + status_email +
                ' by ' + approvedBy,  # MESSAGE
                'E-Forms.electronicscience.com',  # FROM
                [get_user_email],  # TO
                fail_silently=False,
            )
        return HttpResponseRedirect('undertime_approval')
    else:
        form = RemarksForm()
    return render(request,
                  'app_forms/Undertime/undertime_approval_details.html',
                  {'uts': uts,
                   'form': form})


@login_required
def reports_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    global global_ut, grpSupervisor, grpApprovers, grpHRD
    department = str(request.user.groups.exclude(
                name__in=exclude_group).first())
    if grpHRD in request.user.groups.all():
                    uts = Undertime.objects.all().order_by('date_ut')
    elif grpSupervisor or grpApprovers in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        department=department
                    ).order_by('date_ut')

    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            dateFrom = form.cleaned_data['dateFrom']
            dateTo = form.cleaned_data['dateTo']
            status = form.cleaned_data['status']
            if status:
                if grpHRD in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        status=status
                    ).order_by('date_ut')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        status=status,
                        department=department
                    ).order_by('date_ut')
            if status == 'All':
                if grpHRD in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        status__icontains='e'
                    ).order_by('date_ut')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        status__icontains='e',
                        department=department
                    ).order_by('date_ut')
            if dateFrom:
                if grpHRD in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        date_ut__range=(dateFrom, dateTo)
                    ).order_by('date_ut')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        date_ut__range=(dateFrom, dateTo),
                        department=department
                    ).order_by('date_ut')
            if dateFrom:
                if grpHRD in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        date_ut__range=(dateFrom, dateTo),
                    ).order_by('date_ut')
                elif grpSupervisor or grpApprovers in request.user.groups.all():
                    uts = Undertime.objects.filter(
                        date_ut__range=(dateFrom, dateTo),
                        department=department
                    ).order_by('date_ut')
            global_ut = uts
        else:
            form = FilterForm()
            if grpHRD in request.user.groups.all():
                uts = Undertime.objects.all().order_by('date_ut')
            elif grpSupervisor or grpApprovers in request.user.groups.all():
                uts = Undertime.objects.filter(
                    department=department
                ).order_by('date_ut')
            global_ut = uts
    else:
        form = FilterForm()
        if grpHRD in request.user.groups.all():
            uts = Undertime.objects.all().order_by('date_ut')
        elif grpSupervisor or grpApprovers in request.user.groups.all():
            uts = Undertime.objects.filter(
                department=department
            ).order_by('date_ut')
        global_ut = uts
    return render(request,
                  'app_forms/Undertime/reports_undertime.html',
                  {'form': form,
                   'uts': uts,
                   'global_ut': global_ut})
    return global_ut


@login_required
def excel_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'undertime_reports.' + str(Now) + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Reports_Undertime')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.num_format_str = 'dd/MM/yyyy'
    font_style.font.bold = True
    columns = ['Date Filed', 'Name',
               'Department', 'Date Undertime',
               'Number of Hours', 'Reason',
               'Status', 'Approved By', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = global_ut.values_list('dateFiled', 'name',
                                 'department', 'date_ut',
                                 'num_of_hrs', 'reason',
                                 'status', 'approvedBy')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
def pdf_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'undertime_reports.' + str(Now) + '.pdf'
    context = {"undertime": global_ut,
               "file_name": file_name, }
    pdf = render_to_pdf('app_forms/Undertime/pdf_template.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    if pdf:
        return response
    return HttpResponse("Not Found")


@login_required
def csv_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'undertime_reports.' + str(Now) + '.csv'
    undertime_resource = UndertimeResource()
    queryset = global_ut
    dataset = undertime_resource.export(queryset)
    dataset.csv
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def json_undertime(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    Now = datetime.date.today()
    file_name = 'undertime_reports.' + str(Now) + '.json'
    undertime_resource = UndertimeResource()
    queryset = global_ut
    dataset = undertime_resource.export(queryset)
    dataset.json
    response = HttpResponse(dataset.json, content_type='application/json')
    response['Content-Disposition'] = 'attachment;filename=' + file_name
    return response


@login_required
def deleteUndertime(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    if request.method == 'DELETE':
        uts = get_object_or_404(Undertime, pk=pk)
        uts.delete()
    return HttpResponseRedirect('undertime')

# -----------------------------------------------------------------------------
# END OF UNDERTIME
# -----------------------------------------------------------------------------

# -------------------------------F O R M A T-----------------------------------
#   * MAIN MODULE : BROADCAST
#       > ADD BROADCAST
#           * add_broadcast
#
#       > DELETE √
#           * bcast_delete
# -------------------------E N D--O F--F O R M A T-----------------------------

# -----------------------------------------------------------------------------
# BROADCAST
# -----------------------------------------------------------------------------


@login_required
def add_broadcast(request):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    author = request.user
    name = request.user.get_full_name()
    if request.method == 'POST':
        form = BroadcastForm(request.POST, request.FILES)
        if form.is_valid():
            bcast_rec = form.cleaned_data['bcast_rec']
            bcast_subj = form.cleaned_data['bcast_subj']
            bcast_desc = form.cleaned_data['bcast_desc']
            bcast_image = form.cleaned_data['bcast_image']
            bcast_file = form.cleaned_data['bcast_file']
            Broadcast.objects.create(
                name=name, author=author, bcast_rec=bcast_rec,
                bcast_subj=bcast_subj, bcast_desc=bcast_desc,
                bcast_image=bcast_image, bcast_file=bcast_file,
            ).save()
        return HttpResponseRedirect('dashboard')
    else:
        form = BroadcastForm()
    return render(request,
                  'app_forms/Broadcast/add_broadcast.html',
                  {'form': form})


@login_required
def bcast_delete(request, pk):
    user = UserProfile.objects.get(username=request.user)
    # if user.mfa_code is not None:
    #     return HttpResponseRedirect('logout')
    if request.method == 'DELETE':
        bcast = get_object_or_404(Broadcast, pk=pk)
        bcast.delete()
    return HttpResponseRedirect('dashboard')
