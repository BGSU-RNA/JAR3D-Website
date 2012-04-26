from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, render
from django.template import RequestContext

from JAR3Dresults.models import Query
from JAR3Dresults.models import Bygroup
from JAR3Dresults.models import Bysequence
from JAR3Dresults.models import Query_info

from django.views.decorators.csrf import csrf_exempt
import uuid
import json

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

def home(request):
    return render_to_response('JAR3Doutput/homepage.html',
                              {},
                              context_instance=RequestContext(request))

@csrf_exempt
def process_input(request):
    response_data = dict()
    response_data['uuid'] = str( uuid.uuid4() )

    q = Query_info(query_id = response_data['uuid'], status = 0)
    q.save()

    return HttpResponse(json.dumps(response_data), mimetype="application/json")

def result(request, uuid):
    q = Query_info.objects.get(query_id=uuid)

    if q.status == 1:
        return render_to_response('JAR3Doutput/result_done.html',
                                  {'query_id': uuid},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('JAR3Doutput/result_pending.html',
                                  {'query_id': uuid},
                                  context_instance=RequestContext(request))




