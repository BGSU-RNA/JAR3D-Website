
from django.shortcuts import render_to_response

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.core.urlresolvers import reverse

from JAR3Dresults.models import Query_info
from JAR3Dresults.models import Query_sequences
from JAR3Dresults.models import Results_by_loop
from JAR3Dresults.models import Results_by_loop_instance

from rnastructure.primary import fold
from rnastructure.secondary import dot_bracket as Dot

from django.views.decorators.csrf import csrf_exempt
import uuid
import json
import urlparse
import requests
import urllib2
import HTMLParser
import logging
import pdb
import re


logging.basicConfig(filename="/Users/api/apps/jar3d_dev/logs/django.log", level=logging.DEBUG)
# logging.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

def home(request, uuid=None):
    """
        If a query_id is passed in, then input sequences are retrieved,
        otherwise the usual homepage is shown
    """
    if uuid:
        q = Query_info.objects.filter(query_id=uuid)[0]
        if q:
            return render_to_response('JAR3Doutput/base_homepage.html',
                                      {'input': q.parsed_input},
                                      context_instance=RequestContext(request))
        else:
            return render_to_response('JAR3Doutput/base_homepage.html',
                                      {'input': 'query id not found'},
                                      context_instance=RequestContext(request))
    else:
        return render_to_response('JAR3Doutput/base_homepage.html',
                                  {},
                                  context_instance=RequestContext(request))

def result(request, uuid):

    q = Query_info.objects.filter(query_id=uuid)
    if q:
        q = q[0] #we are interested only in the first one
    else:
        return render_to_response('JAR3Doutput/base_result_not_found.html',
                                  {'query_id': uuid},
                                  context_instance=RequestContext(request))

    results = ResultsMaker(query_id=uuid)
    results.get_loop_results()
    results.get_input_stats()

    """
        status codes:
        -1 - failed
        0  - submitted to the queue
        1  - done
        2  - submitted to JAR3D
    """

    if q.status == 1:
        return render_to_response('JAR3Doutput/base_result_done.html',
                                  {'query_info': q, 'num': results.input_stats, 'loops': results.loops, 'sequences': results.sequences},
                                  context_instance=RequestContext(request))
    elif q.status == 0 or q.status == 2:
        return render_to_response('JAR3Doutput/base_result_pending.html',
                                  {'query_info': q, 'num': results.input_stats},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('JAR3Doutput/base_result_failed.html',
                                  {'query_info': q, 'num': results.input_stats},
                                  context_instance=RequestContext(request))

@csrf_exempt
def process_input(request):
    validator = JAR3DValidator()
    return validator.validate(request)

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



class JAR3DValidator():
    """
    Input processing and validation
    """
    def __init__(self):
        self.query_types = {
            'loops':                    ['isFastaSingleLoop',
                                         'isNoFastaSingleLoop',
                                         'isFastaMultipleLoops',
                                         'isNoFastaMultipleLoops'],
            'UNAfold_extract_loops':    ['isFastaSingleSequenceNoSS',
                                         'isNoFastaSingleSequenceNoSS'],
            'RNAalifold_extract_loops': ['isFastaMultipleSequencesNoSS',
                                         'isNoFastaMultipleSequencesNoSS'],
            'isfolded_extract_loops':   ['isFastaSingleSequenceSS',
                                         'isNoFastaSingleSequenceSS',
                                         'isFastaMultipleSequencesSS',
                                         'isNoFastaMultipleSequencesSS'],
        }


    def validate(self, request):
        query_id = str( uuid.uuid4() )
        redirect_url = reverse('JAR3Dresults.views.result', args=[query_id])
        fasta = request.POST.getlist('fasta[]')
        # uppercase all strings and translate DNA to RNA
        data = [ x.upper().replace('T','U') for x in request.POST.getlist('data[]') ]
        query_type = request.POST['query_type']
        ss = request.POST['ss']
        parsed_input = request.POST['parsed_input']

        if query_type in self.query_types['UNAfold_extract_loops']:
            try:
                loops = self.UNAfold_extract_loops(data)
            except fold.FoldingTimeOutError:
                return self.respond("Folding timed out")
            except fold.FoldingFailedError:
                return self.respond("Folding failed")
            except:
                return self.respond("Couldn't fold and extract loops")

        elif query_type in self.query_types['isfolded_extract_loops']:
            try:
                loops = self.isfolded_extract_loops(ss, data)
            except fold.FoldingTimeOutError:
                return self.respond("Folding timed out")
            except fold.FoldingFailedError:
                return self.respond("Folding failed")
            except:
                return self.respond("Couldn't extract loops")

        elif query_type in self.query_types['loops']:
            loops = self.format_extracted_loops(data)

        elif query_type in self.query_types['RNAalifold_extract_loops']:
            try:
                loops = self.RNAalifold_extract_loops(data)
            except fold.FoldingTimeOutError:
                return respond("Folding timed out")
            except fold.FoldingFailedError:
                return self.respond("Folding failed")
            except:
                return self.respond("Couldn't extract loops")

        else:
            return self.respond("Unrecognized query type")

        # create loop objects
        h = HTMLParser.HTMLParser()
        query_info = Query_info(query_id = query_id,
                                group_set = 'IL1.8/HL1.8', # change this
                                model_type = 'default', # change this
                                query_type = query_type,
                                structured_models_only = 0,
                                email = '',
                                status = 0,
                                parsed_input = h.unescape(parsed_input))

        query_sequences = []
        loop_types = ['internal', 'hairpin']
        loop_pattern = '(^[acgu](.+)?[acgu](\*[acgu](.+)?[acgu])?$)'
        internal_id = 0
        for id_tuple, loop in loops.iteritems():
            (loop_type, seq_id, loop_id) = id_tuple
            if loop_type not in loop_types:
                continue
            loop_type = 'IL' if loop_type == 'internal' else 'HL'
            internal_id += 1
            query_sequences.append(Query_sequences(query_id = query_id,
                                                   seq_id = seq_id,
                                                   loop_id = loop_id,
                                                   loop_type = loop_type,
                                                   loop_sequence = loop,
                                                   internal_id = '>seq%i' % internal_id,
                                                   user_seq_id = '' if len(fasta)==0 else fasta[seq_id],
                                                   status = 0 if re.match(loop_pattern, loop, flags=re.IGNORECASE) else -1))
        # don't proceed unless there are internal loops
        if not query_sequences:
            return self.respond("No internal loops found in the input")

        # todo: if all loops have status = -1, then set query_info.status to 1

        # persist the entries in the database starting with sequences
        try:
            [seq.save() for seq in query_sequences]
        except:
            return self.respond("Couldn't save query_sequences")
        try:
            query_info.save()
        except:
            return self.respond("Couldn't save query_info")

        # everything went well, return redirect url
        return self.respond(redirect_url, 'redirect')

    def format_extracted_loops(self, data):
        """
            Input: list of loop instances
            Output:
                results[('internal',0,0)] = 'CAG*CAAG'
                results[('internal',1,0)] = 'CAG*CAUG'
        """
        loop_id = 0
        loops = dict()
        for seq_id, loop in enumerate(data):
            loop_type = 'internal' if '*' in loop else 'hairpin'
            loops[(loop_type,seq_id,loop_id)] = loop
        return loops

    def respond(self, value, key='error'):
        """convenience function
           if key == error, the message will be shown to the user"""
        return HttpResponse( json.dumps({key: value}) )

    def isfolded_extract_loops(self, dot_string, sequences):
        """
            Input: secondary structure + list of sequences
            Output:
                results[('internal',0,0)] = 'CAG*CAAG'
                results[('internal',1,0)] = 'CAG*CAUG'
        """
        parser = Dot.Parser(dot_string)
        results = dict()

        for seq_id, seq in enumerate(sequences):
            loops = parser.loops(seq, flanking=True)
            loop_id = 0
            for loop_type, loop_instances in loops.iteritems(): # HL or IL
                for loop in loop_instances:
                    results[(loop_type,seq_id,loop_id)] = loop
                    loop_id += 1
        return results

    def UNAfold_extract_loops(self, sequences):
        """
            Input: list of sequences
            Output:
                results[('internal',0,0)] = 'CAG*CAAG'
                results[('internal',1,0)] = 'CAG*CAUG'
        """
        folder = fold.UNAfold()
        results = dict()

        for seq_id, seq in enumerate(sequences):
            folded = folder.fold(seq)
            loops = folded[0].loops(flanking=True)
            loop_id = 0
            for loop_type, loop_instances in loops.iteritems(): # HL or IL
                for loop in loop_instances:
                    results[(loop_type,seq_id,loop_id)] = loop
                    loop_id += 1
        return results

    def RNAalifold_extract_loops(self, sequences):
        """
            Input: list of sequences
            Output:
                results[('internal',0,0)] = 'CAG*CAAG'
                results[('internal',1,0)] = 'CAG*CAUG'
        """
        folded = fold.RNAalifold().fold(sequences)
        results = dict()

        for seq_id, seq in enumerate(sequences):
            loops = folded[0].loops(seq, flanking=True)
            loop_id = 0
            for loop_type, loop_instances in loops.iteritems(): # HL or IL
                for loop in loop_instances:
                    results[(loop_type,seq_id,loop_id)] = loop
                    loop_id += 1
        return results


class ResultsMaker():
    """
        Class for producing html of JAR3D results
    """
    def __init__(self, query_id=None):
        self.query_id = query_id
        self.loops = []
        self.input_stats = dict()
        self.problem_loops = []
        self.TOPRESULTS = 10
        self.RNA3DHUBURL = 'http://rna.bgsu.edu/rna3dhub/motif/view/'
        self.SSURL = 'http://rna.bgsu.edu/img/MotifAtlas/'
        self.sequences = []

    def get_loop_results(self):
        results = Results_by_loop.objects.filter(query_id=self.query_id) \
                                         .order_by('loop_id', '-meanscore')

        if results:
            """
            build a 2d list
            loops[0][0] = result 0 for loop 0
            loops[0][1] = result 1 for loop 0
            """

            for result in results:
                result.motif_url = self.RNA3DHUBURL + result.motif_id
                result.ssurl = self.SSURL + result.motif_id[0:2] + '1.8/' + result.motif_id + '.png'
                query_seqs = Query_sequences.objects.filter(query_id=self.query_id,loop_id=result.loop_id)
                seqs = []
                for entries in query_seqs:
                    seqs.append(entries.loop_sequence)
                self.sequences.append(seqs)
                if len(self.loops) <= result.loop_id:
                    self.loops.append([result])
                else:
                    if len(self.loops[-1]) < self.TOPRESULTS:
                        self.loops[-1].append(result)
        else:
            pass

    def get_problem_loops(self):
        """
            Get information about loops with status equal to -1
            These loops haven't been submitted to JAR3D
        """
        pass

    def get_input_stats(self):
        """
            Get information about input sequences and loops
        """
        s  = Query_sequences.objects.filter(query_id=self.query_id).order_by('-seq_id')[0]
        self.input_stats['seq'] = s.seq_id + 1
        s = Query_sequences.objects.filter(query_id=self.query_id).order_by('-loop_id')[0]
        self.input_stats['loops'] = s.loop_id + 1
        s = Query_sequences.objects.filter(query_id=self.query_id)
        self.input_stats['loop_instances'] = s.count

    def get_loop_instance_results(self):
        q = Query_info.objects.get(query_id=self.query_id)
        if q:
            pass
        else:
            pass


