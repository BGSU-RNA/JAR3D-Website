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
import urllib2


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

@csrf_exempt
def process_input(request):

    query_id = str( uuid.uuid4() )

    # todo - save entire json query just in case
    query_info = Query_info(query_id = query_id,
                            group_set = 'default',
                            model_type = 'default',
                            query_type = request.POST['query_type'],
                            structured_models_only = 0,
                            email = '',
                            status = 0).save()

    return HttpResponse( json.dumps(dict({'uuid': query_id})) )

    fasta = request.POST.getlist('fasta[]')
    data  = request.POST.getlist('data[]')

    # generate internal ids
    seq_ids = [ 'seq' + str(i) for x in xrange(len(fasta)) ]

    ready_loops = ['isFastaSingleLoop', 'isNoFastaSingleLoop',
                   'isFastaMultipleLoops', 'isNoFastaMultipleLoops']

    fold_and_extract_loops = ['isFastaSingleSequenceNoSS', 'isNoFastaSingleSequenceNoSS',
                              'isFastaMultipleSequencesNoSS', 'isNoFastaMultipleSequencesNoSS']

    extract_loops = ['isFastaSingleSequenceSS', 'isNoFastaSingleSequenceSS',
                     'isFastaMultipleSequencesSS', 'isNoFastaMultipleSequencesSS']

    if request.POST['query_type'] in fold_and_extract_loops:
        pass
    elif request.POST['query_type'] in extract_loops:
        # loops = extract_loops(request.POST)
        pass
    elif request.POST['query_type'] in ready_loops:
        pass
    else:
        return HttpResponse('Error: Unrecognized query type')

    for i, loop in enumerate(loops):
        if loop.find('*') > 0:
            loop_type = 'IL'
        else:
            loop_type = 'HL'

        query_sequences = Query_sequences(query_seq_id = '_'.join([query_id, seq_ids[i]]),
                                          query_id = query_id,
                                          seq_id = seq_ids[i],
                                          loop_type = loop_type,
                                          loop_sequence = '', # change this
                                          user_seq_id = '', # change this
                                          status = 0).save()


def extract_loops(data):
    """
    """
    url = 'http://rna.bgsu.edu/api/secondary'
    params = json.dumps({
        'dot-bracket': data['ss'],
        'sequences': data.getlist('data[]')
    })
    req = urllib2.Request(url=url, data=params)
    return urllib2.urlopen(req).read()
