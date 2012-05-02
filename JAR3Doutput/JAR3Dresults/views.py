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
import urlparse
import requests
import urllib2

import logging

logging.basicConfig(filename="/Users/api/apps/jar3d_dev/logs/django.log", level=logging.DEBUG)
# logging.setLevel(logging.DEBUG)

# Get an instance of a logger
logger = logging.getLogger(__name__)


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

def home(request, uuid=None):
    """
    """
    if uuid:
        q = Query_info.objects.get(query_id=uuid)
        if q:
            return render_to_response('JAR3Doutput/base_homepage.html',
                                      {'input': q.query_type},
                                      context_instance=RequestContext(request))
        else:
            return render_to_response('JAR3Doutput/base_homepage.html',
                                      {'input': 'query not found'},
                                      context_instance=RequestContext(request))
    else:
        return render_to_response('JAR3Doutput/base_homepage.html',
                                  {},
                                  context_instance=RequestContext(request))

def result(request, uuid):
    q = Query_info.objects.get(query_id=uuid)

    if q.status == 1:
        return render_to_response('JAR3Doutput/base_result_done.html',
                                  {'query_id': uuid},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('JAR3Doutput/base_result_pending.html',
                                  {'query_id': uuid},
                                  context_instance=RequestContext(request))

@csrf_exempt
def process_input(request):

    query_id = str( uuid.uuid4() )
    redirect_url = 'http://rna.bgsu.edu/jar3d_dev/result/' + query_id

    # todo - save entire json query just in case
    query_info = Query_info(query_id = query_id,
                            group_set = 'default', # change this
                            model_type = 'default', # change this
                            query_type = request.POST['query_type'],
                            structured_models_only = 0,
                            email = '',
                            status = 0)
    try:
        query_info.save()
    except:
        return HttpResponse( json.dumps({'error': "Couldn't save query_info"}) )

    return HttpResponse( json.dumps({'redirect': redirect_url}) )

    fasta = request.POST.getlist('fasta[]')
    data  = request.POST.getlist('data[]')
    ss    = request.POST['ss']

    # generate internal ids
    seq_ids = [ 'seq' + str(x) for x in xrange(len(fasta)) ]

    ready_loops = ['isFastaSingleLoop',
                   'isNoFastaSingleLoop',
                   'isFastaMultipleLoops',
                   'isNoFastaMultipleLoops']

    fold_and_extract_loops = ['isFastaSingleSequenceNoSS',
                              'isNoFastaSingleSequenceNoSS',
                              'isFastaMultipleSequencesNoSS',
                              'isNoFastaMultipleSequencesNoSS']

    extract_loops = ['isFastaSingleSequenceSS',
                     'isNoFastaSingleSequenceSS',
                     'isFastaMultipleSequencesSS',
                     'isNoFastaMultipleSequencesSS']

    if request.POST['query_type'] in fold_and_extract_loops:
#         try:
        loops = local_fold_and_extract_loops(data)
#         except:
#             return HttpResponse( "Error: couldn't fold and extract loops" )
    elif request.POST['query_type'] in extract_loops:
        try:
            loops = local_extract_loops(data)
        except:
            return HttpResponse( "Error: couldn't extract loops" )
    elif request.POST['query_type'] in ready_loops:
        pass
    else:
        return HttpResponse('Error: Unrecognized query type')

    for loop_list in enumerate(loops):
        for i, loop in enumerate(loop_list):
            logging.info( loop )
            loop_type = 'IL' if loop.find('*') > 0 else 'HL'
            query_sequences.append(Query_sequences(query_seq_id = '_'.join([query_id, seq_ids[i]]),
                                                   query_id = query_id,
                                                   seq_id = seq_ids[i],
                                                   loop_type = loop_type,
                                                   loop_sequence = '', # change this
                                                   user_seq_id = '', # change this
                                                   status = 0))

    # persist the entries in the database starting with sequences
    try:
        [seq.save() for seq in query_sequences]
    except:
        return HttpResponse("Error: couldn't save query_sequences")
    try:
        query_info.save()
    except:
        return HttpResponse( "Error: couldn't save query_info" )

    return HttpResponse( json.dumps({'uuid': query_id}) )


def pre_request_hook(req):
    if 'Host' not in req.headers:
        hostname = urlparse(req.full_url)[1]
        req.headers['Host'] = hostname

@csrf_exempt
def test_for_blake(request):
    hooks = {'pre_request': pre_request_hook}
    proxies = { "http": "129.1.149.201:3030" }
    req = requests.Request('http://rna.bgsu.edu')
    logging.error(req)
    logging.error(req.headers)
    resp = requests.get("http://rna.bgsu.edu", proxies=proxies, hooks=hooks)
    print(resp)
    return resp
    # url = 'http://www.google.com'
    # req = urllib2.Request(url=url)
    # return urllib2.urlopen(req).read()

def local_extract_loops(sequences):
    """
    """
    pass

def local_fold_and_extract_loops(sequences):
    """
        Input: list of sequences
        Output: list of dictionaries
        loops[0]['internal'], loops[0]['hairpin']
    """
    import rnastructure, pdb
    from rnastructure.primary import fold
    folder = fold.UNAfold()
    loops = []
    for seq in sequences:
        logger.info(seq)
        results = folder.fold(seq)
        loops.append( results[0].loops(flanking=True) )
    return loops

def cloud_extract_loops(data):
    """
    """
    url = 'http://rna.bgsu.edu/api/secondary'
    params = json.dumps({
        'dot-bracket': data['ss'],
        'sequences': data.getlist('data[]')
    })
    req = urllib2.Request(url=url, data=params)
    return urllib2.urlopen(req).read()
