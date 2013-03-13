from django.db.models import Model
from django.db.models import CharField
from django.db.models import TextField
from django.db.models import DecimalField
from django.db.models import IntegerField
from django.db.models import DateTimeField
from django.db.models import SmallIntegerField


class QueryInfo(Model):
    query_id = CharField(max_length=36, primary_key=True, db_index=True)
    group_set = CharField(max_length=20, default='default')
    model_type = CharField(max_length=20, default='default')
    query_type = CharField(max_length=35)
    structured_models_only = IntegerField(default=0)
    email = CharField(blank=True, max_length=100)
    status = IntegerField(default=0)
    parsed_input = TextField()
    time_submitted = DateTimeField(auto_now_add=True)
    time_completed = DateTimeField(blank=True, null=True)

    class Meta:
        db_table = u'jar3d_query_info'


class QuerySequences(Model):
    query_id = CharField(max_length=36, db_index=True)
    seq_id = SmallIntegerField()
    loop_id = SmallIntegerField()
    loop_type = CharField(max_length=2)
    loop_sequence = TextField()
    internal_id = CharField(max_length=8)
    user_seq_id = TextField()
    status = SmallIntegerField(default=0)
    time_submitted = DateTimeField(auto_now_add=True)
    time_completed = DateTimeField(blank=True, null=True)

    class Meta:
        db_table = u'jar3d_query_sequences'


class QueryStructure(Model):
    query_id = CharField(max_length=36)
    dot_bracket = TextField()
    json_airport = TextField()
    json_pairs = TextField()

    class Meta:
        db_table = u'jar3d_query_structure'


class ResultsByLoopInstance(Model):
    query_id = CharField(max_length=36, db_index=True)
    seq_id = SmallIntegerField()
    loop_id = SmallIntegerField()
    motif_id = CharField(max_length=11)
    score = DecimalField(max_digits=10, decimal_places=6)
    percentile = DecimalField(max_digits=10, decimal_places=6)
    interioreditdist = SmallIntegerField()
    fulleditdist = SmallIntegerField()
    rotation = SmallIntegerField()

    class Meta:
        db_table = u'jar3d_results_by_loop_instance'


class ResultsByLoop(Model):
    query_id = CharField(max_length=36, db_index=True)
    loop_id = SmallIntegerField()
    motif_id = CharField(max_length=11)
    meanscore = DecimalField(max_digits=10, decimal_places=6)
    meanpercentile = DecimalField(max_digits=10, decimal_places=6)
    meaninterioreditdist = DecimalField(max_digits=10, decimal_places=6)
    meanfulleditdist = DecimalField(max_digits=10, decimal_places=6)
    medianscore = DecimalField(max_digits=10, decimal_places=6)
    medianpercentile = DecimalField(max_digits=10, decimal_places=6)
    medianinterioreditdist = DecimalField(max_digits=10, decimal_places=6)
    medianfulleditdist = DecimalField(max_digits=10, decimal_places=6)
    signature = CharField(max_length=150)
    rotation = SmallIntegerField()
    correspondences = TextField()

    class Meta:
        db_table = u'jar3d_results_by_loop'
