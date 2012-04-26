# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models


class Query(models.Model):
    id = models.CharField(max_length=20, blank=True, primary_key=True)
    sequences = models.TextField(blank=True)
    numseqs = models.IntegerField(null=True, blank=True)
    gset = models.CharField(max_length=50, blank=True)
    class Meta:
        db_table = u'query'

class Bygroup(models.Model):
    P_id = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=20, blank=True)
    meanscore = models.DecimalField(max_digits=10, decimal_places=6,blank=True) # This field type is a guess.  Fixed?
    meanpercentile = models.DecimalField(max_digits=10, decimal_places=6,blank=True) # This field type is a guess. Fixed?
    meaneditdist = models.IntegerField(null=True, blank=True)
    medianscore = models.DecimalField(max_digits=10, decimal_places=6,blank=True) # This field type is a guess. Fixed?
    medianpercentile = models.DecimalField(max_digits=10, decimal_places=6,blank=True) # This field type is a guess. Fixed?
    medianeditdist = models.IntegerField(null=True, blank=True)
    signature = models.CharField(max_length=150, blank=True)
    groupurl = models.CharField(max_length=256, blank=True)
    imageurl = models.CharField(max_length=256, blank=True)
    rotation = models.IntegerField(null=True, blank=True)
    groupnum = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'bygroup'

class Bysequence(models.Model):
    P_id = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=20, blank=True)
    seqnum = models.IntegerField(null=True, blank=True)
    sequence = models.CharField(max_length=50, blank=True)
    score = models.DecimalField(max_digits=10, decimal_places=6,blank=True) # This field type is a guess.  Fixed?
    percentile = models.DecimalField(max_digits=10, decimal_places=6,blank=True) # This field type is a guess.  Fixed?
    editdist = models.IntegerField(null=True, blank=True)
    rotation = models.IntegerField(null=True, blank=True)
    groupnum = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'bysequence'

class Query_info(models.Model):
    query_id = models.CharField(max_length=36, primary_key=True)
    loop_type = models.CharField(max_length=2)
    group_set = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20)
    query_type = models.IntegerField(null=True, blank=True)
    structured = models.IntegerField(null=True, blank=True)
    email = models.CharField(max_length=50)
    status = models.IntegerField(null=True, blank=True)
    time_submitted = models.DateTimeField(auto_now_add=True)
    time_completed = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = u'query_info'
