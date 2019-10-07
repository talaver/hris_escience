from django import forms


class ChangeOfWorkScheduleForm(forms.Form):
    name = forms.CharField(widget=forms.Textarea)
    designation = forms.CharField(widget=forms.Textarea)
    fromDate = forms.DateField(label="Date From (YYYY-MM-DD)")
    fromTimeFrom = forms.TimeField(label="Time From (YYYY-MM-DD)")
    fromTimeTo = forms.TimeField(label="Time To (YYYY-MM-DD)")
    toDate = forms.DateField(label="Date To (YYYY-MM-DD)")
    toTimeFrom = forms.TimeField(label="Time From (YYYY-MM-DD)")
    toTimeTo = forms.TimeField(label="Time To (YYYY-MM-DD)")
    reason = forms.CharField(widget=forms.Textarea)
    supervisor_name = forms.CharField(widget=forms.Textarea)


class ProductivityToolForm(forms.Form):
    name = forms.CharField(widget=forms.Textarea)
    prodTool = forms.CharField(widget=forms.Textarea)
    price = forms.CharField(widget=forms.Textarea)
    reasons = forms.CharField(widget=forms.Textarea)


class OvertimeForm(forms.Form):
    name = forms.CharField(widget=forms.Textarea)
    department = forms.CharField(widget=forms.Textarea)
    date_ot = forms.DateField(label="Date (YYYY-MM-DD)")
    timeFrom = forms.TimeField(label="Time From (YYYY-MM-DD)")
    timeTo = forms.TimeField(label="Time From (YYYY-MM-DD)")
    num_of_hrs = forms.CharField(widget=forms.Textarea)
    reason = forms.CharField(widget=forms.Textarea)
    project_name = forms.CharField(widget=forms.Textarea)


class UndertimeForm(forms.Form):
    name = forms.CharField(widget=forms.Textarea)
    department = forms.CharField(widget=forms.Textarea)
    date_ut = forms.DateField(label="Date (YYYY-MM-DD)")
    timeFrom = forms.TimeField(label="Time From (YYYY-MM-DD)")
    timeTo = forms.TimeField(label="Time From (YYYY-MM-DD)")
    num_of_hrs = forms.CharField(widget=forms.Textarea)
    reason = forms.CharField(widget=forms.Textarea)


class LeaveForm(forms.Form):
    halfDay = forms.CharField(widget=forms.Textarea, label="CHOOSE FIRST")
    leaveType = forms.CharField(label="Leave Type")
    dateFrom = forms.DateTimeField(label="Date From (YYYY-MM-DD)")
    dateTo = forms.DateTimeField(label="Date To (YYYY-MM-DD)")
    timeFrom = forms.TimeField(label="",
                               required=False)
    timeTo = forms.TimeField(label="",
                             required=False)
    reason = forms.CharField(widget=forms.Textarea)
    status = forms.BooleanField()


class BroadcastForm(forms.Form):
    bcast_rec = forms.CharField(widget=forms.Textarea)
    bcast_subj = forms.CharField(widget=forms.Textarea)
    bcast_desc = forms.CharField(widget=forms.Textarea, required=False)
    bcast_image = forms.ImageField(required=False)
    bcast_file = forms.FileField(required=False)


class SearchForm(forms.Form):
    searchBox = forms.CharField(widget=forms.Textarea, required=False)
    dateFrom = forms.DateField(label="Date From (YYYY-MM-DD)", required=False)
    dateTo = forms.DateField(label="Date To (YYYY-MM-DD)", required=False)


class FilterForm(forms.Form):
    status = forms.CharField(required=False)
    dateFrom = forms.DateField(label="Date From (YYYY-MM-DD)", required=False)
    dateTo = forms.DateField(label="Date To (YYYY-MM-DD)", required=False)


class RemarksForm(forms.Form):
    remarks = forms.CharField(widget=forms.Textarea)
    status = forms.CharField(widget=forms.Textarea)


class UpdateProfileForm(forms.Form):
    profilePic = forms.ImageField(required=False)
    phoneNum = forms.CharField(widget=forms.Textarea, required=False)


class AuthenticateForm(forms.Form):
    mfa_code = forms.CharField(widget=forms.Textarea)
