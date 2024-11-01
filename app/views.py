from django.shortcuts import render
from django.http import HttpResponse
# from django.http import JsonResponse
# from django.template import RequestContext
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

import html
import json
import logging
import os
import re
import sys
import time
from urllib.parse import urlparse
import uuid

from app.models import Query_info
from app.models import Query_sequences
from app.models import Query_loop_positions
from app.models import Results_by_loop
from app.models import Results_by_loop_instance
from app.models import Loop_query_info
from app.models import Correspondence_results

from config import settings

# Let's try to run this without a queue, because beanstalkc seems impossible to install
# and celery is not working
# from app import my_queue
from app.run_jar3d import score
from app.run_jar3d import align

sys.path.insert(2, '/usr/local/pipeline/RNAStructure')

from rnastructure.primary import fold
from rnastructure.secondary import dot_bracket as Dot

logger = logging.getLogger(__name__)


def home(request, uuid=None):
    """
    JAR3D home page
    If a query_id is passed in, then input sequences are retrieved,
    otherwise the usual homepage is shown
    https://rna.bgsu.edu/jar3d/result/43336382-ba12-4d72-9d5c-fa5fe9cf3c31/
    """

    # motif atlas versions to list and in what order
    versions = ["3.48", "3.2", "1.18", "1.17", "1.15", "1.14", "1.13", "1.12", "1.11", "1.10",
                "1.9", "1.8", "1.7", "1.6", "1.5", "1.4", "1.3", "1.2", "1.1", "1.0"]


    if uuid:
        q = Query_info.objects.filter(query_id=uuid)[0]
        if q:
            return render(request,'base_homepage.html',
                                      {'input': q.parsed_input,
                                       'options': versions})
        else:
            return render(request,'base_homepage.html',
                                      {'input': 'query id not found',
                                       'options': versions})
    else:
        # supply blank input variable to avoid key error
        return render(request,'base_homepage.html',{'input': '', 'options': versions})


def result(request, uuid):
    """
    Display the result of one query of one or more loops, with one or more sequences
    The uuid is the query_id and the results must be retrieved from the database.
    """

    # get basic information about the query from the uuid
    q = Query_info.objects.filter(query_id=uuid)
    if q:
        q = q[0]  # We are interested only in the first match
    else:
        return render(request,'base_result_not_found.html',{'query_id': uuid})
    version = q.group_set[2:q.group_set.index('/')]

    results = ResultsMaker(query_id=uuid)
    results.get_loop_results(version)
    results.get_input_stats()

    """
        status codes:
        -1 - failed
        0  - submitted to the queue
        1  - done
        2  - submitted to JAR3D
    """

    logger.debug("views.py: Got input stats")
    logger.debug(str(results))
    logger.debug(str(q))
    logger.debug("views.py: Database status: %s" % str(q.status))

    if q.status == 1:
        zippedResults = sort_loops(results.loops, results.indices, results.sequences)
        logger.debug("views.py: database status 1, about to run make_input_alignment")
        q.formatted_input = make_input_alignment(q.parsed_input, q.query_type)
        return render(request,'base_result_done.html',
                                  {'query_info': q, 'num': results.input_stats,
                                   'results': zippedResults, 'compress': False})
    elif q.status == 0 or q.status == 2:
        logger.debug("views.py: database status 0 or 2, about to run make_input_alignment")
        q.formatted_input = make_input_alignment(q.parsed_input, q.query_type)
        return render(request,'base_result_pending.html',
                                  {'query_info': q, 'num': results.input_stats})
    else:
        return render(request,'base_result_failed.html',
                                  {'query_info': q, 'num': results.input_stats})


def all_result(request, uuid, loopid):

    q = Query_info.objects.filter(query_id=uuid)
    if q:
        q = q[0]  # We are interested only in the first one
    else:
        return render(request,'base_result_not_found.html',
                                  {'query_id': uuid})
    version = q.group_set[2:q.group_set.index('/')]

    results = ResultsMaker(query_id=uuid, loop=loopid, num=9999)
    results.get_loop_results(version)
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
        q.formatted_input = make_input_alignment(q.parsed_input, q.query_type)
        return render(request,'base_result_done.html',
                                  {'query_info': q, 'num': results.input_stats,
                                   'results': zippedResults, 'compress': True, 'loop_id': int(loopid)+1})
    elif q.status == 0 or q.status == 2:
        q.formatted_input = make_input_alignment(q.parsed_input, q.query_type)
        return render(request,'base_result_pending.html',
                                  {'query_info': q, 'num': results.input_stats})
    else:
        return render(request,'base_result_failed.html',
                                  {'query_info': q, 'num': results.input_stats})


def single_result(request, uuid, loopid, motifgroup):

    q = Loop_query_info.objects.filter(query_id=uuid, loop_id=loopid, motif_group=motifgroup)
    if q:
        q = q[0]  # We are interested only in the first one

    ShowResult = True

    # these jobs are accessed repeatedly by bots
    # it would be better to cache the results, but for now,
    # we'll just ignore these requests.  2021-07-23
    exclude_list = [
    '0aca9b23-945e-4a6e-8297-b46a35848396',
    '4295f189-9518-47f9-a4bb-e3d013c3c4f9',
    '96fb3f5b-a700-4fde-aa7a-8b33539d7c4e',
    '5d7362a1-61a0-476e-945d-c96e9aef90cf',
    'a223a5a5-67f9-4011-be6c-60be02d50134']

    if q and uuid in exclude_list:
        q.title = ''
        q.formatted_input = ''
        ShowResult = False
        logger.info("views.py is excluding %s" % uuid)
        return render(request,'base_result_loop_failed.html',
                                  {'query_info': q,
                                   'loop': loopid, 'group': motifgroup})

    title = Query_info.objects.filter(query_id=uuid)[0].title

    if q:
        q.title = title  # needed on the page below
        q.formatted_input = ''   # let's not work too hard for the pending/failed pages
        if q.status == 0:
            return render(request,'base_result_loop_pending.html',
                                      {'query_info': q,
                                       'loopnum': loopid, 'motifid': motifgroup})
        elif q.status == -1:
            ShowResult = False
            return render(request,'base_result_loop_failed.html',
                                      {'query_info': q,
                                       'loop': loopid, 'group': motifgroup})

    else:
        # no query yet stored in the database, so start the alignment process
        qi = Query_info.objects.filter(query_id=uuid)
        if qi:
            qi = qi[0]
            group_set = qi.group_set  # like HL3.48/IL3.48
            version = group_set.split('/')[0][2:]

            query = Loop_query_info(query_id=uuid, loop_id=loopid, status=0, motif_group=motifgroup)
            query.save()

            # align sequences of a specific loop to a specific motif group model
            align({
                'id': uuid,
                'loop_id': loopid,
                'motif_group': motifgroup,
                'version': version
            })

            # the .jar job runs quickly, but producing the alignment page is slow
            # if you prefer to send the user to the pending page in this case, change to True below
            # if we are using a queue, we need to wait for the worker to finish
            # but starting in October 2024 on rnaprod2, we just run the job while the user waits
            send_to_pending_page = False
            if send_to_pending_page:
                # need to make sure query has .title
                query.title = title
                return render(request,'base_result_loop_pending.html',
                                        {'query_info': query,
                                        'loopnum': loopid, 'motifid': motifgroup})

        else:
            return "Query %s not found" % uuid

    if ShowResult:
        qi = Query_info.objects.filter(query_id=uuid)
        if qi:
            qi = qi[0]
            group_set = qi.group_set  # like HL3.48/IL3.48
            version = group_set.split('/')[0][2:]
        else:
            return "Query %s not found" % uuid

        # retrieve alignment results for each sequence, this loop in the 2d, against this motif group
        seq_res = Results_by_loop_instance.objects.filter(query_id=uuid) \
                                          .filter(loop_id=loopid).filter(motif_id=motifgroup).order_by('seq_id')

        # for internal loops, we need to know which rotation to use
        rotation = Results_by_loop.objects.filter(query_id=uuid,
                                                  loop_id=loopid,
                                                  motif_id=motifgroup)[0].rotation

        loop_type = motifgroup.split('_')[0]

        # the sequences from this particular loop in the 2d
        seqs = Query_sequences.objects.filter(query_id=uuid, loop_id=loopid)

        rows = []
        for res in seq_res:
            # This seems to be the very slow query that bogs down the database
            # Maybe because it is repeated so many times
            corrs = Correspondence_results.objects.filter(result_instance_id=res.id)
            line_base = 'Sequence_' + str(res.seq_id)
            seq_r = seqs.filter(seq_id=res.seq_id)[0]
            seq = seq_r.loop_sequence
            seq = seq.replace('-', '')
            seq = seq.replace('_', '')
            if rotation == 1:
                strands = seq.split('*')
                seq = strands[1] + '*' + strands[0]
            # Reproduce text for alignment calculation
            for corr_line in corrs:
                line = (line_base + '_Position_' + str(corr_line.sequence_position) + '_' +
                        seq[corr_line.sequence_position-1] + ' aligns_to_JAR3D ' + res.motif_id +
                        '_Node_' + str(corr_line.node) + '_Position_' + corr_line.node_position)
                if corr_line.is_insertion:
                    line = line + '_Insertion'
                rows.append(line)
            name = seq_r.user_seq_id
            if len(name) == 0:
                name = 'Sequence_' + str(res.seq_id+1)   # label sequences starting from 1
            elif name[0] == '>':
                name = name[1:]
            cutoff = 'true'
            if res.cutoff == 0:
                cutoff = 'false'
            rows.append(line_base + ' has_name ' + name)
            rows.append(line_base + ' has_score ' + str(res.score))
            rows.append(line_base + ' hase_alignment_score_deficit ' + 'N/A')
            rows.append(line_base + ' has_minimum_interior_edit_distance ' + str(res.interioreditdist))
            rows.append(line_base + ' has_minimum_full_edit_distance ' + str(res.fulleditdist))
            rows.append(line_base + ' has_cutoff_value ' + cutoff)
            rows.append(line_base + ' has_cutoff_score ' + str(res.cutoff_score))

        # filenamewithpath = settings.MODELS + '/IL/' + version + '/lib/' + motifgroup + '_correspondences.txt'
        filenamewithpath = os.path.join(settings.MODELS,loop_type,version,'lib', motifgroup + '_correspondences.txt')
        with open(filenamewithpath, "r") as f:
            model_text = f.readlines()
        header, motifalig, sequencealig = align_sequences_and_instances_from_text(model_text, rows)
        seq_text = '\n'.join(rows)
        model_text = '\n'.join(model_text)
        seq_lines = []
        motif_lines = []
        motif_names = []
        col_nums = ['Column']
        for i in range(1, len(header['nodes'])+1):
            col_nums.append(i)
        col_nums = col_nums + ['', '', 'Interior', 'Full']
        position = ['Position'] + header['positions'] + ['Meets', 'Cutoff', 'Edit', 'Edit']
        if len(seq_res) <= 50:
            col_nums = col_nums + ['Alignment']*len(sequencealig)
            position = position + ['Distance to']*len(sequencealig)
        insertions = []
        for item in header['insertions']:
            insertions.append(item.replace('Insertion', 'I'))
        insertions = ['Insertion'] + insertions + ['Cutoff', 'Score', 'Distance', 'Distance']
        color_dict = {'0': '#f8f8f8', '1': '#f8eaea', '2': '#f1d4d4', '3': '#eabfbf', '4': '#e3aaaa', '5': '#dc9595'}
        edit_lines = []
        for res in seq_res:
            key = 'Sequence_' + str(res.seq_id)
            name = Query_sequences.objects.filter(query_id=uuid, seq_id=res.seq_id, loop_id=loopid)[0].user_seq_id
            if len(name) == 0:
                name = 'Sequence' + str(res.seq_id)
            elif name[0] == ">":
                name = name[1:]
            insertions.append(name)
            cutoff = 'True'
            if res.cutoff == 0:
                cutoff = 'False'
            line = [name] + sequencealig[key] + [cutoff, str(res.cutoff_score),
                                                 str(res.interioreditdist), str(res.fulleditdist)]
            seq_lines.append(line)
            ed_line = []
            if len(seq_res) <= 50:
                for res2 in seq_res:
                    line1 = sequencealig[key]
                    key2 = 'Sequence_' + str(res2.seq_id)
                    line2 = sequencealig[key2]
                    edit = str(compare_lists(line1, line2))
                    ed_line.append((edit, color_dict.setdefault(edit, '#df8080')))
            edit_lines.append(ed_line)
        header_zip = zip(col_nums, position, insertions)
        seq_zip = zip(seq_lines, edit_lines)
        mkeys = sorted(motifalig.keys())
        edit_lines = []
        color_dict['0'] = '#ffffff'
        for key in mkeys:
            line = motifalig[key]
            parts = key.split('_')
            motif_names.append(parts[2]+'_'+parts[3]+'_'+parts[4])
            line = line + ['', '', '', '']
            ed_line = []
            if len(seq_res) <= 50:
                for res2 in seq_res:
                    line1 = motifalig[key]
                    key2 = 'Sequence_' + str(res2.seq_id)
                    line2 = sequencealig[key2]
                    edit = str(compare_lists(line1, line2))
                    ed_line.append((edit, color_dict.setdefault(edit, '#df8080')))
            edit_lines.append(ed_line)
            motif_lines.append(line)
        motif_data = zip(motif_names, motif_lines, edit_lines)

        # filenamewithpath = settings.MODELS + '/IL/'+version+'/lib/' + motifgroup + '_interactions.txt'
        filenamewithpath = os.path.join(settings.MODELS,loop_type,version,'lib', motifgroup + '_interactions.txt')
        with open(filenamewithpath, "r") as f:
            interaction_text = f.read().replace(' ', '\t')
        return render(request,'base_result_loop_done.html',
                                  {'query_info': qi, 'header_zip': header_zip,
                                   'loopnum': loopid, 'motifid': motifgroup,
                                   'seq_zip': seq_zip, 'motif_data': motif_data, 'seq_text': seq_text,
                                   'model_text': model_text, 'inter_text': interaction_text,
                                   'rotation': rotation})


@csrf_exempt
def process_input(request):
    validator = JAR3DValidator()
    return validator.validate(request)


def pre_request_hook(req):
    if 'Host' not in req.headers:
        # hostname = urlparse(req.full_url)[1]
        hostname = urlparse(req.full_url()).hostname
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

    def validate(self, request_raw):
        query_id = str(uuid.uuid4())

        # redirect_url = reverse('app.views.result', args=[query_id])
        redirect_url = reverse('result', args=[query_id])

        request = json.loads(request_raw.body)

        # fasta = request.POST.getlist('fasta[]')
        fasta = request.get('fasta', [])

        # uppercase all strings and translate DNA to RNA
        # data = [x.upper().replace('T', 'U') for x in request.POST.getlist('data[]')]
        data = [x.upper().replace('T', 'U') for x in request.get('data', [])]

        # query_type = request.POST.get('query_type', 'Unknown query type')
        # ss = request.POST.get('ss', 'No secondary structure')
        # parsed_input = request.POST.get('parsed_input', 'No parsed input')
        # title = request.POST.get('title', 'JAR3D Search')
        # version = request.POST['version']

        query_type = request.get('query_type', 'Unknown query type')
        ss = request.get('ss', 'No secondary structure')
        parsed_input = request.get('parsed_input', 'No parsed input')
        title = request.get('title', 'JAR3D Search')
        version = request.get('version','3.48')

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

        query_info = self.make_query_info(query_id, query_type, parsed_input, title, version)
        query_sequences = self.make_query_sequences(loops, fasta, query_id)
        query_positions = self.make_query_indices(indices, query_id)

        # don't proceed unless there are internal loops
        if not query_sequences:
            return self.respond("No internal loops found in the input")

        # todo: if all loops have status = -1, then set query_info.status to 1

        # persist the entries in the database starting with sequences
        # query_sequences, query_positions, mins = zip(*sort_sequences(query_positions, query_sequences))
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
        except Exception:
            return self.respond("Couldn't save query_info")

        logger.debug('views.py: About to score the query')
        exit_status = score({'id': query_id, 'version': version})

        if exit_status == 0:
            # everything went well, return redirect url
            logger.debug('views.py: exit_status 0, figure that scoring went fine')
            return self.respond(redirect_url, 'redirect')
        else:
            # sleep for 2 seconds and then redirect
            time.sleep(2)
            return self.respond(redirect_url, 'redirect')

            logger.debug('views.py: exit_status not 0, figure that scoring went wrong')
            return self.respond("Couldn't score the loops in the query")


    def make_query_sequences(self, loops, fasta, query_id):
        query_sequences = []
        loop_types = ['internal', 'hairpin']
        loop_pattern = '(^[acgu](.+)?[acgu](\*[acgu](.+)?[acgu])?$)'
        internal_id = 0
        for id_tuple, loop in loops.items():
            (loop_type, seq_id, loop_id) = id_tuple
            if loop_type not in loop_types:
                continue
            loop_type = 'IL' if loop_type == 'internal' else 'HL'
            internal_id += 1

            # query_id is always 1 in tests, seq_id is always 0, not sure why

            print('make_query_sequences')
            print('make_query_sequences: query_id:    %s' % query_id)
            print('make_query_sequences: seq_id:      %s' % seq_id)
            print('make_query_sequences: loop_id:     %s' % loop_id)
            print('make_query_sequences: loop_type:   %s' % loop_type)
            print('make_query_sequences: loop:        %s' % loop)
            print('make_query_sequences: internal_id: %s' % internal_id)

            query_sequences.append(Query_sequences(query_id=query_id,
                                                   seq_id=seq_id,
                                                   loop_id=loop_id,
                                                   loop_type=loop_type,
                                                   loop_sequence=loop,
                                                   internal_id='>seq%i' % internal_id,
                                                   user_seq_id='' if len(fasta) == 0 else fasta[seq_id],
                                                   status=0 if re.match(loop_pattern, loop, flags=re.IGNORECASE)
                                                   else -1))
        return query_sequences

    def make_query_indices(self, indices, query_id):
        query_positions = []
        loop_id = 0
        for loop_types, loops in indices.items():
            for loop in loops:
                for side in loop:
                    for index in side:
                        query_positions.append(Query_loop_positions(query_id=query_id,
                                                                    loop_id=loop_id,
                                                                    column_index=index))
                loop_id = loop_id + 1
        return query_positions

    def make_query_info(self, query_id, query_type, parsed_input, title="testing", version="3.48"):
        query_info = Query_info(query_id=query_id,
                                group_set='IL' + version + '/HL' + version,
                                model_type='default',  # change this
                                query_type=query_type,
                                title=title,
                                structured_models_only=0,
                                email='',
                                status=0,
                                parsed_input=html.unescape(parsed_input))
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
            for loop_type, loop_instances in loops.items():  # HL or IL
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
            for loop_type, loop_instances in loops.items():  # HL or IL
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
            for loop_type, loop_instances in loops.items():  # HL or IL
                for loop in loop_instances:
                    results[(loop_type, seq_id, loop_id)] = loop
                    loop_id += 1
        return results, indices


class ResultsMaker():
    """
        Class for producing html of JAR3D results
    """
    def __init__(self, query_id=None, loop=-1, num=10):
        self.query_id = query_id
        self.loop_id = loop
        self.loops = []
        self.input_stats = dict()
        self.problem_loops = []
        self.TOPRESULTS = num
        self.RNA3DHUBURL = getattr(settings, 'RNA3DHUB',
                                   'https://rna.bgsu.edu/rna3dhub/')
        self.SSURL = getattr(settings, 'SSURL',
                             'https://rna.bgsu.edu/img/MotifAtlas/')
        self.sequences = []
        self.indices = []

    def get_loop_results(self, version):
        ignore_cutoff = False   # Only show results with cutoff precent > 0
        if self.loop_id == -1:
            results = Results_by_loop.objects.filter(query_id=self.query_id) \
                                             .order_by('loop_id',
                                                       '-cutoff_percent',
                                                       '-mean_cutoff_score')
        else:
            ignore_cutoff = True   # Show results regardless of cutoff
            results = Results_by_loop.objects.filter(query_id=self.query_id, loop_id=self.loop_id) \
                                             .order_by('-cutoff_percent',
                                                       '-mean_cutoff_score')
        if results:
            """
            build a 2d list
            loops[0][0] = result 0 for loop 0
            loops[0][1] = result 1 for loop 0
            """
            loop_ids = []
            res_list = set()  # List of tuples to avoid duplicate entries
            for result in results:
                if int(self.loop_id) >= 0:
                    count_id = 0
                else:
                    count_id = result.loop_id
                tup = (result.loop_id, result.motif_id)
                if tup in res_list:
                    continue
                else:
                    res_list.add(tup)
                result.motif_url = self.RNA3DHUBURL + 'motif/view/' + result.motif_id
                result.align_url = '/jar3d/result/%s/%s/' % (result.query_id, result.loop_id)
                result.ssurl = self.SSURL + result.motif_id[0:2] + version + '/' + result.motif_id + '.png'
                if not(result.loop_id in loop_ids):
                    loop_ids.append(result.loop_id)
                if len(self.loops) <= count_id:
                    if result.cutoff_percent > 0 or ignore_cutoff:
                        self.loops.append([result])
                    else:
                        self.loops.append([])
                else:
                    if len(self.loops[-1]) < self.TOPRESULTS and (result.cutoff_percent > 0 or ignore_cutoff):
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
                # Convert inds to ranges
                ranges = []
                last = -2
                start = -1
                for item in inds:
                    if item != last+1:
                        if start != -1:
                            if start != last:
                                ranges.append(str(start+1)+"-"+str(last+1))
                            else:
                                ranges.append(str(start+1))
                        start = item
                    last = item
                if start != last:
                    ranges.append(str(start+1)+"-"+str(last+1))
                else:
                    ranges.append(str(start+1))
                self.sequences.append(seqs)
                self.indices.append(", ".join(ranges))

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


def compare_lists(l1, l2):
    edits = 0
    lists = zip(l1, l2)
    for item1, item2 in lists:
        if item1 != item2 and item1 != '*' and item2 != '*':
            edits += levenshtein(item1, item2)
    return edits


# From http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance on 4/17/2015
def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def sort_loops(loops, indices, sequences):
    mins = []
    for ranges in indices:
        mins.append(ranges.replace(',', '-').split("-")[0])
    sorted_lists = sorted(zip(loops, sequences, indices, mins), key=lambda x: int(x[3]))
    return sorted_lists


def sort_sequences(indices, sequences):
    mins = [min(inds.split(', '), key=int) for inds in indices]
    mins = [str(x) for x in mins]
    sorted_lists = sorted(zip(sequences, indices, mins), key=lambda x: int(x[2]))
    return sorted_lists


def make_input_alignment(parsed_input, query_type):
    # If input is just one loop, just return the sequences
    loops = ['isFastaSingleLoop',
             'isNoFastaSingleLoop',
             'isFastaMultipleLoops',
             'isNoFastaMultipleLoops']
    if query_type in loops:
        return parsed_input
    # Get info about query
    query_lines = parsed_input.splitlines()
    has_ss = False
    has_fasta = False
    fasta = ['isFastaSingleSequenceSS',
             'isFastaMultipleSequencesSS',
             'isFastaSingleSequenceNoSS',
             'isFastaMultipleSequencesNoSS']
    SSs = ['isFastaSingleSequenceSS',
           'isNoFastaSingleSequenceSS',
           'isFastaMultipleSequencesSS',
           'isNoFastaMultipleSequencesSS']
    if query_type in fasta:
        has_fasta = True
    if query_type in SSs:
        has_ss = True
    # Make formatted alignment for display
    first_seq_row = 0
    if has_ss:
        first_seq_row += 1
    if has_fasta:
        first_seq_row += 1
    seq_length = len(query_lines[first_seq_row])
    l = []
    if seq_length >= 100:
        for i in range(1, seq_length+1):
            l.append(str(i//100))
        l.append('\n')
    if seq_length >= 10:
        for i in range(1, seq_length+1):
            l.append(str(i % 100//10))
        l.append('\n')
    for i in range(1, seq_length+1):
        l.append(str(i % 10))
    l.append('\n')
    l.append('='*seq_length+'\n')
    line = 0
    while line < len(query_lines):
        l.append(query_lines[line] + '\n')
        line += 1
    out = ''.join(l)
    return out


def align_sequences_and_instances_from_text(MotifCorrespondenceText, SequenceCorrespondenceText):

    InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn, NotSequenceToModel, \
        HasName = read_correspondences_from_text(MotifCorrespondenceText)[:7]
    NotInstanceToGroup, NotInstanceToPDB, NotInstanceToSequence, NotGroupToModel, NotModelToColumn, \
        SequenceToModel = read_correspondences_from_text(SequenceCorrespondenceText)[:6]

    motifalig = {}

    for a in InstanceToGroup.keys():
        m = re.search("(.+Instance_[0-9]+)", a)
        Name = HasName[m.group(1)]                      # use the name as the key; very informative
        motifalig[Name] = [''] * len(ModelToColumn)     # start empty

    for a in sorted(InstanceToGroup.keys()):
        m = re.search("(.+Instance_[0-9]+)", a)
        Name = HasName[m.group(1)]                      # use the name as the key; very informative
        t = int(ModelToColumn[GroupToModel[InstanceToGroup[a]]])
        motifalig[Name][t-1] += a[len(a)-1]

    sequencealig = {}

    for a in SequenceToModel.keys():
        m = re.search("(Sequence_[0-9]+)", a)
        sequencealig[m.group(1)] = [''] * len(ModelToColumn)  # start empty

    for a in sorted(SequenceToModel.keys()):
        m = re.search("(Sequence_[0-9]+)", a)
        t = int(ModelToColumn[SequenceToModel[a]])
        sequencealig[m.group(1)][t-1] += a[len(a)-1]

    header = {}              # new dictionary
    header['columnname'] = [''] * len(ModelToColumn)
    header['nodes'] = [''] * len(ModelToColumn)
    header['positions'] = [''] * len(ModelToColumn)
    header['insertions'] = [''] * len(ModelToColumn)

    for a in ModelToColumn.keys():
        header['columnname'][int(ModelToColumn[a])-1] = a

    for i in range(0, len(ModelToColumn)):
        m = re.search("Node_([0-9]+)", header['columnname'][i])
        a = m.group(1)
        header['nodes'][i] = a
        if re.search("Insertion", header['columnname'][i]):
            header['insertions'][i] = 'Insertion'

    for a in GroupToModel.keys():
        m = re.search("Column_([0-9]+)$", a)
        if m is not None:
            colnum = ModelToColumn[GroupToModel[a]]
            header['positions'][int(colnum)-1] = m.group(1)

    return header, motifalig, sequencealig


def read_correspondences_from_text(lines):

    InstanceToGroup = {}           # instance of motif to conserved group position
    InstanceToPDB = {}             # instance of motif to NTs in PDBs
    InstanceToSequence = {}        # instance of motif to position in fasta file
    GroupToModel = {}              # positions in motif group to nodes in JAR3D model
    ModelToColumn = {}             # nodes in JAR3D model to display columns
    HasName = {}                   # organism name in FASTA header
    SequenceToModel = {}           # sequence position to node in JAR3D model
    HasScore = {}                  # score of sequence against JAR3D model
    HasInteriorEdit = {}           # minimum interior edit distance to 3D instances from the motif group
    HasFullEdit = {}               # minimum full edit distance to 3D instances from the motif group
    HasCutoffValue = {}            # cutoff value 'true' or 'false'
    HasCutoffScore = {}            # cutoff score, 100 is perfect, 0 is accepted, negative means reject
    HasAlignmentScoreDeficit = {}  # alignment score deficit, how far below the best score among 3D instances

    for line in lines:
        if re.search("corresponds_to_group", line):
            m = re.match("(.*) (.*) (.*)", line)
            InstanceToGroup[m.group(1)] = m.group(3)
        elif re.search("corresponds_to_PDB", line):
            m = re.match("(.*) (.*) (.*)", line)
            InstanceToPDB[m.group(1)] = m.group(3)
        elif re.search("corresponds_to_JAR3D", line):
            m = re.match("(.*) (.*) (.*)", line)
            GroupToModel[m.group(1)] = m.group(3)
        elif re.search("corresponds_to_sequence", line):
            m = re.match("(.*) (.*) (.*)", line)
            InstanceToSequence[m.group(1)] = m.group(3)
        elif re.search("appears_in_column", line):
            m = re.match("(.*) (.*) (.*)", line)
            ModelToColumn[m.group(1)] = m.group(3)
        elif re.search("aligns_to_JAR3D", line):
            m = re.match("(.*) (.*) (.*)", line)
            SequenceToModel[m.group(1)] = m.group(3)
        elif re.search("has_name", line):
            m = re.match("(.*) (.*) (.*)", line)
            HasName[m.group(1)] = m.group(3)
        elif re.search("has_score", line):
            m = re.match("(.*) (.*) (.*)", line)
            HasScore[m.group(1)] = m.group(3)
        elif re.search("has_minimum_interior_edit_distance", line):
            m = re.match("(.*) (.*) (.*)", line)
            HasInteriorEdit[m.group(1)] = m.group(3)
        elif re.search("has_minimum_full_edit_distance", line):
            m = re.match("(.*) (.*) (.*)", line)
            HasFullEdit[m.group(1)] = m.group(3)
        elif re.search("has_cutoff_value", line):
            m = re.match("(.*) (.*) (.*)", line)
            HasCutoffValue[m.group(1)] = m.group(3)
        elif re.search("has_cutoff_score", line):
            m = re.match("(.*) (.*) (.*)", line)
            HasCutoffScore[m.group(1)] = m.group(3)
        elif re.search("has_alignment_score_deficit", line):
            m = re.match("(.*) (.*) (.*)", line)
            HasAlignmentScoreDeficit[m.group(1)] = m.group(3)

    return InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn, \
        SequenceToModel, HasName, HasScore, HasInteriorEdit, HasFullEdit, HasCutoffValue, \
        HasCutoffScore, HasAlignmentScoreDeficit
