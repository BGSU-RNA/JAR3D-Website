from django.shortcuts import render_to_response
from JAR3Dresults.models import Query
from JAR3Dresults.models import Bygroup
from JAR3Dresults.models import Bysequence
    
def results(request, query_id):
    try:
        q = Bygroup.objects.filter(id=query_id)
    except Bygroup.DoesNotExist:
        raise Http404
    return render_to_response('JAR3Doutput/results.html', {'query': q})

def group_results(request, query_id, group_num):
    try:
        q = Bysequence.objects.filter(id=query_id, groupnum=group_num)
    except Bygroup.DoesNotExist:
        raise Http404
    return render_to_response('JAR3Doutput/group_results.html', {'query': q})
