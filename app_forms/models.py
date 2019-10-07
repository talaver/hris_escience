from django.db import models
from django.contrib.auth.models import User


class ChangeOfWorkSchedule(models.Model):
    name = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    department = models.TextField(null=True, blank=True, default=None)
    fromDate = models.DateField()
    fromTimeFrom = models.TimeField()
    fromTimeTo = models.TimeField()
    toDate = models.DateField()
    toTimeFrom = models.TimeField()
    toTimeTo = models.TimeField()
    reason = models.CharField(max_length=100)
    status = models.TextField(null=True, blank=True, default=None)
    remarks = models.TextField(null=True, blank=True, default=None)
    supervisor_name = models.CharField(max_length=100)
    dateApproved = models.DateField(null=True, blank=True, default=None)
    approvedBy = models.TextField(null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
            return f'{self.name} | {self.fromDate} | {self.toDate}'


class ProductivityTool(models.Model):
    name = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    department = models.TextField(null=True, blank=True, default=None)
    prodTool = models.CharField(max_length=100)
    price = models.CharField(max_length=100)
    reasons = models.CharField(max_length=100)
    status = models.TextField(null=True, blank=True, default=None)
    remarks = models.TextField(null=True, blank=True, default=None)
    dateApproved = models.DateField(null=True, blank=True, default=None)
    approvedBy = models.TextField(null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
            return f'{self.name} | {self.prodTool} | {self.price}'


class Overtime(models.Model):
    dateFiled = models.DateField()
    name = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    department = models.TextField(null=True, blank=True, default=None)
    date_ot = models.DateField()
    timeFrom = models.TimeField()
    timeTo = models.TimeField()
    num_of_hrs = models.TextField()
    reason = models.TextField()
    project_name = models.TextField()
    status = models.TextField(null=True, blank=True, default=None)
    remarks = models.TextField(null=True, blank=True, default=None)
    dateApproved = models.DateField(null=True, blank=True, default=None)
    approvedBy = models.TextField(null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} | {self.date_ot} | {self.project_name}'


class Undertime(models.Model):
    dateFiled = models.DateField()
    name = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    department = models.TextField(null=True, blank=True, default=None)
    date_ut = models.DateField()
    timeFrom = models.TimeField()
    timeTo = models.TimeField()
    num_of_hrs = models.TextField()
    reason = models.TextField()
    status = models.TextField(null=True, blank=True, default=None)
    remarks = models.TextField(null=True, blank=True, default=None)
    dateApproved = models.DateField(null=True, blank=True, default=None)
    approvedBy = models.TextField(null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} | {self.date_ut}'


class Leaves(models.Model):
    name = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    email = models.TextField()
    leaveType = models.TextField()
    dateFrom = models.DateField()
    dateTo = models.DateField()
    timeFrom = models.TimeField(null=True, blank=True, default=None)
    timeTo = models.TimeField(null=True, blank=True, default=None)
    reason = models.TextField()
    status = models.TextField()
    leaveCount = models.FloatField()
    remarks = models.TextField(null=True, blank=True, default=None)
    department = models.TextField(null=True, blank=True, default=None)
    approvedBy = models.TextField(null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} | {self.dateFrom} | {self.dateTo}'


class Broadcast(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=100)
    bcast_rec = models.TextField()
    bcast_subj = models.TextField()
    bcast_desc = models.TextField()
    bcast_image = models.ImageField(null=True, default=None)
    bcast_file = models.FileField(null=True, default=None)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.bcast_subj} | {self.bcast_rec} | {self.bcast_desc} | {self.bcast_image} | {self.bcast_file}'


class UserProfile(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=100)
    profilePic = models.ImageField(null=True, default=None, blank=True)
    phoneNum = models.TextField(null=True, default=None, blank=True)
    mfa_code = models.TextField(null=True, default=None, blank=True)

    def __str__(self):
        return f'{self.username} | {self.name} | {self.phoneNum}'
