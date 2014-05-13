# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models

class Query_info(models.Model):
    query_id = models.CharField(max_length=36, primary_key=True, db_index=True)
    group_set = models.CharField(max_length=20, default='default') #motifs release
    model_type = models.CharField(max_length=20, default='default') #bph_stack etc
    query_type = models.CharField(max_length=35)
    structured_models_only = models.IntegerField(default=0)
    email = models.CharField(blank=True, max_length=100)
    status = models.IntegerField(default=0)
    parsed_input = models.TextField()
    time_submitted = models.DateTimeField(auto_now_add=True)
    time_completed = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = u'jar3d_query_info'

class Query_loop_positions(models.Model):
    query_id = models.CharField(max_length=36, db_index=True)
    loop_id = models.SmallIntegerField()
    column_index = models.IntegerField()
    class Meta:
        db_table = u'jar3d_loop_positions'

class Query_sequences(models.Model):
    query_id = models.CharField(max_length=36, db_index=True)
    seq_id = models.SmallIntegerField()
    loop_id = models.SmallIntegerField()
    loop_type = models.CharField(max_length=2)
    loop_sequence = models.TextField()
    internal_id = models.CharField(max_length=8)
    user_seq_id = models.TextField()
    status = models.SmallIntegerField(default=0)
    time_submitted = models.DateTimeField(auto_now_add=True)
    time_completed = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = u'jar3d_query_sequences'

class Results_by_loop_instance(models.Model):
    query_id = models.CharField(max_length=36, db_index=True)
    seq_id = models.SmallIntegerField()
    loop_id = models.SmallIntegerField()
    motif_id = models.CharField(max_length=11)
    cutoff =  models.SmallIntegerField()
    score = models.DecimalField(max_digits=10, decimal_places=6)
    percentile = models.DecimalField(max_digits=10, decimal_places=6)
    interioreditdist = models.SmallIntegerField()
    fulleditdist = models.SmallIntegerField()
    rotation = models.SmallIntegerField()
    class Meta:
        db_table = u'jar3d_results_by_loop_instance'

class Results_by_loop(models.Model):
    query_id = models.CharField(max_length=36, db_index=True)
    loop_id = models.SmallIntegerField()
    motif_id = models.CharField(max_length=11)
    cutoff_percent = models.DecimalField(max_digits=10, decimal_places=6)
    meanscore = models.DecimalField(max_digits=10, decimal_places=6)
    meanpercentile = models.DecimalField(max_digits=10, decimal_places=6)
    meaninterioreditdist = models.DecimalField(max_digits=10, decimal_places=6)
    meanfulleditdist = models.DecimalField(max_digits=10, decimal_places=6)
    medianscore = models.DecimalField(max_digits=10, decimal_places=6)
    medianpercentile = models.DecimalField(max_digits=10, decimal_places=6)
    medianinterioreditdist = models.DecimalField(max_digits=10, decimal_places=6)
    medianfulleditdist = models.DecimalField(max_digits=10, decimal_places=6)
    signature = models.CharField(max_length=150)
    rotation = models.SmallIntegerField()
    correspondences = models.TextField()
    class Meta:
        db_table = u'jar3d_results_by_loop'