from django.db import models
from django.utils import timezone

# Create your models here.
"""
tweet:
    text
"""
class Label(models.Model):
    name = models.CharField(max_length=255, unique=True)
    lower_range = models.FloatField(null=True, blank=True)
    upper_range = models.FloatField(null=True, blank=True)
    category = models.ForeignKey('Category', default=1, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return self.name


class AlternateLabel(models.Model):
    name = models.CharField(max_length=55, blank=False)
    label = models.ForeignKey(to=Label, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('name', 'label')
    def __str__(self) -> str:
        return f"{self.name}"
    
    def __repr__(self) -> str:
        return f"{self.name}"


class Tweet(models.Model):
    text = models.TextField( max_length=255 )


class Patient(models.Model):
    fname = models.CharField(max_length=255)
    lname = models.CharField(max_length=255)
    address = models.TextField(max_length=255)
    zip = models.IntegerField()

    def __str__(self):
        return f"{self.fname} {self.lname}"

class Document(models.Model):
    #Foreignkey -> ManytoOne
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    document = models.FileField(upload_to='media/')
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.name


class TestResult(models.Model):
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    
    #name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    value = models.FloatField()
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.label} {self.unit}"



class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, null=True)
    priority = models.IntegerField(blank=False, null=True, default=0)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name