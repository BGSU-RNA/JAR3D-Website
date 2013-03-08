import re
import json
import uuid
import urlparse
import HTMLParser
from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt

from JAR3Dresults.models import QueryInfo
from JAR3Dresults.models import QuerySequences
from JAR3Dresults.models import ResultsByLoop

from rnastructure.primary import fold
from rnastructure.secondary import dot_bracket as Dot


def home(request, uuid=None):
    """
        If a query_id is passed in, then input sequences are retrieved,
        otherwise the usual homepage is shown
    """
    data = {}
    if uuid:
        q = QueryInfo.objects.filter(query_id=uuid)[0]
        if q:
            data = {'input': q.parsed_input}
        else:
            data = {'input': 'query id not found'}
    return render(request, 'JAR3Doutput/base_homepage.html', data)


def result(request, uuid):

    q = QueryInfo.objects.filter(query_id=uuid)

    if not q:
        return render(request, 'JAR3Doutput/base_result_not_found.html',
                      {'query_id': uuid})

    q = q[0]  # We are interested only in the first one

    results = ResultsMaker(query_id=uuid)
    results.get_loop_results()
    results.get_input_stats()
    results.get_loop_sequences()

    """
        status codes:
        -1 - failed
        0  - submitted to the queue
        1  - done
        2  - submitted to JAR3D
    """

    page = 'JAR3Doutput/base_result_failed.html'
    data = {'query_info': q, 'num': results.input_stats}

    if q.status == 1:
        data['loops'] = []
        for index, matches in enumerate(results.loops):
            info = {'matches': matches,
                    'sequence': results.sequences[index]}
            data['loops'].append(info)

        page = 'JAR3Doutput/base_result_done.html'
    elif q.status == 0 or q.status == 2:
        page = 'JAR3Doutput/base_result_pending.html'

    return render(request, page, data)


@csrf_exempt
def process_input(request):
    validator = JAR3DValidator()
    return validator.validate(request)


def pre_request_hook(req):
    if 'Host' not in req.headers:
        hostname = urlparse(req.full_url)[1]
        req.headers['Host'] = hostname


class JAR3DValidator(object):
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
        data = request.POST.getlist('data[]')
        data = [x.upper().replace('T', 'U') for x in data]
        query_type = request.POST.get('query_type')
        ss = request.POST.get('ss', None)
        parsed_input = request.POST.get('parsed_input')

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
                return self.respond("Folding timed out")
            except fold.FoldingFailedError:
                return self.respond("Folding failed")
            except:
                return self.respond("Couldn't extract loops")

        else:
            return self.respond("Unrecognized query type")

        # create loop objects
        h = HTMLParser.HTMLParser()
        query_info = QueryInfo(query_id=query_id,
                               group_set='IL0.6/HL0.2',  # TODO: Change this
                               model_type='default',  # TODO: Change this
                               query_type=query_type,
                               structured_models_only=0,
                               email='',
                               status=0,
                               parsed_input=h.unescape(parsed_input))

        query_sequences = []
        loop_types = ['internal']  # TODO: ['internal', 'hairpin']
        loop_pattern = '^[acgu](.+)?[acgu](\*[acgu](.+)?[acgu])$'
        internal_id = 0
        all_invalid = True

        for id_tuple, loop in loops.iteritems():
            (loop_type, seq_id, loop_id) = id_tuple

            if loop_type not in loop_types:
                continue
            loop_type = 'IL' if loop_type == 'internal' else 'HL'

            internal_id += 1
            id_string = '>seq%i' % internal_id

            status = -1
            if re.match(loop_pattern, loop, flags=re.IGNORECASE):
                status = 0

            if status == 0:
                all_invalid = False

            user_id = ''
            if len(fasta) != 0:
                user_id = fasta[seq_id]

            query_sequences.append(QuerySequences(query_id=query_id,
                                                  seq_id=seq_id,
                                                  loop_id=loop_id,
                                                  loop_type=loop_type,
                                                  loop_sequence=loop,
                                                  internal_id=id_string,
                                                  user_seq_id=user_id,
                                                  status=status))

        # don't proceed unless there are internal loops
        if not query_sequences:
            return self.respond("No internal loops found in the input")

        if all_invalid:
            query_info.status = 1

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
            loops[(loop_type, seq_id, loop_id)] = loop
        return loops

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
        results = dict()

        for seq_id, seq in enumerate(sequences):
            loops = parser.loops(seq, flanking=True)
            loop_id = 0
            for loop_type, loop_instances in loops.iteritems():  # HL or IL
                for loop in loop_instances:
                    results[(loop_type, seq_id, loop_id)] = loop
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
            for loop_type, loop_instances in loops.iteritems():  # HL or IL
                for loop in loop_instances:
                    results[(loop_type, seq_id, loop_id)] = loop
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
            for loop_type, loop_instances in loops.iteritems():  # HL or IL
                for loop in loop_instances:
                    results[(loop_type, seq_id, loop_id)] = loop
                    loop_id += 1
        return results


class ResultsMaker(object):
    """
        Class for producing html of JAR3D results
    """

    def __init__(self, query_id=None):
        self.query_id = query_id
        self.loops = []
        self.input_stats = dict()
        self.problem_loops = []
        self.sequences = []
        self.TOPRESULTS = 10
        self.RNA3DHUBURL = 'http://rna.bgsu.edu/rna3dhub/motif/view/'
        self.SSURL = 'http://rna.bgsu.edu/img/MotifAtlas/IL0.6/'

    def get_loop_sequences(self):
        """
            Generate an array of the form:
                sequences[0] = "AAAA\nCCCC\nGGGG"
            where the index is the loop id for that query. Must be run after
            get_loop_results.
        """
        results = QuerySequences.objects.filter(query_id=self.query_id) \
                                        .order_by('loop_id', 'seq_id')

        container = defaultdict(list)
        for result in results.all():
            container[result.loop_id].append(result.loop_sequence)

        for loop_id in sorted(container.keys()):
            sequences = container[loop_id]
            self.sequences.append('\n'.join(sequences))
        print(self.sequences)

    def get_loop_results(self):
        results = ResultsByLoop.objects.filter(query_id=self.query_id) \
                                       .order_by('loop_id', '-meanscore')
        """
        build a 2d list
        loops[0][0] = result 0 for loop 0
        loops[0][1] = result 1 for loop 0
        """

        for result in results:
            result.motif_url = self.RNA3DHUBURL + result.motif_id
            result.ssurl = self.SSURL + result.motif_id + '.png'

            if len(self.loops) <= result.loop_id:
                self.loops.append([result])
            else:
                if len(self.loops[-1]) < self.TOPRESULTS:
                    self.loops[-1].append(result)

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
        s = QuerySequences.objects.filter(query_id=self.query_id) \
                                  .order_by('-seq_id')[0]
        self.input_stats['seq'] = s.seq_id + 1
        s = QuerySequences.objects.filter(query_id=self.query_id) \
                                  .order_by('-loop_id')[0]
        self.input_stats['loops'] = s.loop_id + 1
        s = QuerySequences.objects.filter(query_id=self.query_id)
        self.input_stats['loop_instances'] = s.count

    def get_loop_instance_results(self):
        q = QueryInfo.objects.get(query_id=self.query_id)
        if q:
            pass
        else:
            pass
