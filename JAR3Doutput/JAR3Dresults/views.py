
from django.shortcuts import render_to_response

from django.http import HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse

from JAR3Dresults.models import Query_info
from JAR3Dresults.models import Query_sequences
from JAR3Dresults.models import Query_loop_positions
from JAR3Dresults.models import Results_by_loop

from rnastructure.primary import fold
from rnastructure.secondary import dot_bracket as Dot

from django.views.decorators.csrf import csrf_exempt
import uuid
import json
import urlparse
import HTMLParser
import logging
import re

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
        q = q[0]  # We are interested only in the first one
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
        zippedResults = sort_loops(results.loops, results.indices, results.sequences)
        return render_to_response('JAR3Doutput/base_result_done.html',
                                  {'query_info': q, 'num': results.input_stats,
                                   'results': zippedResults},
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
        query_id = str(uuid.uuid4())
        redirect_url = reverse('JAR3Dresults.views.result', args=[query_id])
        fasta = request.POST.getlist('fasta[]')
        # uppercase all strings and translate DNA to RNA
        data = [x.upper().replace('T', 'U') for x in request.POST.getlist('data[]')]
        query_type = request.POST['query_type']
        ss = request.POST['ss']
        parsed_input = request.POST['parsed_input']

        if query_type in self.query_types['UNAfold_extract_loops']:
            try:
                loops, indices = self.UNAfold_extract_loops(data)
            except fold.FoldingTimeOutError:
                return self.respond("Folding timed out")
            except fold.FoldingFailedError:
                return self.respond("Folding failed")
            except:
                return self.respond("Couldn't fold and extract loops")

        elif query_type in self.query_types['isfolded_extract_loops']:
            try:
                loops, indices = self.isfolded_extract_loops(ss, data)
            except fold.FoldingTimeOutError:
                return self.respond("Folding timed out")
            except fold.FoldingFailedError:
                return self.respond("Folding failed")
            except:
                return self.respond("Couldn't extract loops")

        elif query_type in self.query_types['loops']:
            try:
                loops, indices = self.format_extracted_loops(data)
            except:
                return self.respond("Unknown Error")

        elif query_type in self.query_types['RNAalifold_extract_loops']:
            try:
                loops, indices = self.RNAalifold_extract_loops(data)
            except fold.FoldingTimeOutError:
                return self.respond("Folding timed out")
            except fold.FoldingFailedError:
                return self.respond("Folding failed")
            except:
                return self.respond("Couldn't extract loops")

        else:
            return self.respond("Unrecognized query type")

        query_info = self.make_query_info(query_id, query_type, parsed_input)
        query_sequences = self.make_query_sequences(loops, fasta, query_id)
        query_positions = self.make_query_indices(indices, query_id)

        # don't proceed unless there are internal loops
        if not query_sequences:
            return self.respond("No internal loops found in the input")

        # todo: if all loops have status = -1, then set query_info.status to 1

        # persist the entries in the database starting with sequences
        try:
            for seq in query_sequences:
                seq.save()
        except:
            return self.respond("Couldn't save query_sequences")
        try:
            for ind in query_positions:
                ind.save()
        except:
            return self.respond("Couldn't save query_positions")
        try:
            query_info.save()
        except:
            return self.respond("Couldn't save query_info")
        # everything went well, return redirect url
        return self.respond(redirect_url, 'redirect')

    def make_query_sequences(self, loops, fasta, query_id):
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
            query_sequences.append(Query_sequences(query_id=query_id,
                                                   seq_id=seq_id,
                                                   loop_id=loop_id,
                                                   loop_type=loop_type,
                                                   loop_sequence=loop,
                                                   internal_id='>seq%i' % internal_id,
                                                   user_seq_id='' if len(fasta)==0 else fasta[seq_id],
                                                   status=0 if re.match(loop_pattern, loop, flags=re.IGNORECASE) else -1))
        return query_sequences

    def make_query_indices(self, indices, query_id):
        query_positions = []
        loop_id = 0
        for loop_types, loops in indices.iteritems():
            for loop in loops:
                for side in loop:
                    for index in side:
                        query_positions.append(Query_loop_positions(query_id=query_id,
                                                                    loop_id=loop_id,
                                                                    column_index=index))
                loop_id = loop_id + 1
        return query_positions

    def make_query_info(self, query_id, query_type, parsed_input):
        h = HTMLParser.HTMLParser()
        query_info = Query_info(query_id=query_id,
                                group_set='IL1.13/HL1.13',  # change this
                                model_type='default',  # change this
                                query_type=query_type,
                                structured_models_only=0,
                                email='',
                                status=0,
                                parsed_input=h.unescape(parsed_input))
        return query_info

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
            dot_string = '(' + '.'*(len(loop)-2) + ')'
            if loop_type == 'internal':
                break_point = loop.find('*')
                dot_string = dot_string[:break_point-2] + '()' + dot_string[break_point+2:]
            loops[(loop_type, seq_id, loop_id)] = loop
            parser = Dot.Parser(dot_string)
            indices = parser.indices(flanking=True)
        return loops, indices

    def respond(self, value, key='error'):
        """convenience function
           if key == error, the message will be shown to the user"""
        return HttpResponse(json.dumps({key: value}))

    def isfolded_extract_loops(self, dot_string, sequences):
        """
            Input: secondary structure + list of sequences
            Output:
                results[('internal',0,0)] = 'CAG*CAAG'
                results[('internal',1,0)] = 'CAG*CAUG'
        """
        parser = Dot.Parser(dot_string)
        indices = parser.indices(flanking=True)
        results = dict()

        for seq_id, seq in enumerate(sequences):
            loops = parser.loops(seq, flanking=True)
            loop_id = 0
            for loop_type, loop_instances in loops.iteritems(): # HL or IL
                for loop in loop_instances:
                    results[(loop_type, seq_id, loop_id)] = loop
                    loop_id += 1
        return results, indices

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
            indices = folded[0].indices(flanking=True)
            loops = folded[0].loops(flanking=True)
            loop_id = 0
            for loop_type, loop_instances in loops.iteritems():  # HL or IL
                for loop in loop_instances:
                    results[(loop_type, seq_id, loop_id)] = loop
                    loop_id += 1
        return results, indices

    def RNAalifold_extract_loops(self, sequences):
        """
            Input: list of sequences
            Output:
                results[('internal',0,0)] = 'CAG*CAAG'
                results[('internal',1,0)] = 'CAG*CAUG'
        """
        folded = fold.RNAalifold().fold(sequences)
        indices = folded[0].indices(flanking=True)
        results = dict()

        for seq_id, seq in enumerate(sequences):
            loops = folded[0].loops(seq, flanking=True)
            loop_id = 0
            for loop_type, loop_instances in loops.iteritems():  # HL or IL
                for loop in loop_instances:
                    results[(loop_type, seq_id, loop_id)] = loop
                    loop_id += 1
        return results, indices


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
        self.indices = []

    def get_loop_results(self):
        results = Results_by_loop.objects.filter(query_id=self.query_id) \
                                         .order_by('loop_id',
                                                   '-cutoff_percent',
                                                   '-meanscore')

        if results:
            """
            build a 2d list
            loops[0][0] = result 0 for loop 0
            loops[0][1] = result 1 for loop 0
            """
            loop_ids = []
            for result in results:
                result.motif_url = self.RNA3DHUBURL + result.motif_id
                result.ssurl = self.SSURL + result.motif_id[0:2] + '1.13/' + result.motif_id + '.png'
                if not(result.loop_id in loop_ids):
                    loop_ids.append(result.loop_id)
                if len(self.loops) <= result.loop_id:
                    self.loops.append([result])
                else:
                    if len(self.loops[-1]) < self.TOPRESULTS:
                        self.loops[-1].append(result)

            for loop_id in loop_ids:
                query_seqs = Query_sequences.objects.filter(query_id=self.query_id, loop_id=loop_id)
                loop_inds = Query_loop_positions.objects.filter(query_id=self.query_id, loop_id=loop_id)
                inds = []
                seqs = []
                for entries in query_seqs:
                    seqs.append(entries.loop_sequence)
                for ind in loop_inds:
                    if not(ind.column_index in inds):
                        inds.append(ind.column_index)
                self.sequences.append(seqs)
                self.indices.append(", ".join(map(lambda i: str(i + 1), inds)))

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
        s = Query_sequences.objects.filter(query_id=self.query_id).order_by('-seq_id')[0]
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

def sort_loops(loops, indices, sequences):
    mins = [ min(inds.split(', '), key = int) for inds in indices ]
    mins = [ str(x) for x in mins ]
    sorted_lists = sorted(zip(loops, sequences, indices, mins), key = lambda x: int(x[3]))
    return zip(loops, sequences, indices, mins)