from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

# from django.http import JsonResponse
# from django.template import RequestContext

import html
import json
import logging
import os
import re
import sys
import time
import urllib
from urllib.parse import urlparse
import uuid

from app.models import Query_info
from app.models import Query_sequences
from app.models import Query_loop_positions
from app.models import Results_by_loop
from app.models import Results_by_loop_instance
from app.models import Loop_query_info
from app.models import Correspondence_results

from app.rfam_to_fasta import process_rfam_alignment

from config import settings

# Let's try to run this without a queue, because beanstalkc seems impossible to install
# and celery is not working
# from app import my_queue
from app.run_jar3d import score
from app.run_jar3d import align

sys.path.insert(2, '/usr/local/pipeline/RNAStructure')

# Rfam families for certain molecule types
LSU = ['RF02543','RF02540','RF02541','RF02546']
SSU = ['RF01960','RF01959','RF00177','RF02545','RF02542']
tRNA = ['RF00005']

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

    # recognize and bounce LSU, SSU, tRNA Rfam families
    if re.match(r'^RF[0-9]{5}-[0-9]+\.[0-9]+$', uuid):
        rfam_result = True
        rfam_family = uuid.split('-')[0]
        value = ""
        if rfam_family in LSU:
            value = 'Rfam ribosomal LSU families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + rfam_family
        elif rfam_family in SSU:
            value = 'Rfam ribosomal SSU families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + rfam_family
        elif rfam_family in tRNA:
            value = 'Rfam ribosomal tRNA families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + rfam_family
        if value:
            return HttpResponse(value)
    else:
        rfam_result = False
        rfam_family = ""

    # get basic information about the query from the uuid
    q = Query_info.objects.filter(query_id=uuid)
    if q:
        q = q[0]  # We are interested only in the first match
    else:
        if rfam_result:
            # process the request like a brand new one
            validator = JAR3DValidator()
            return validator.validate(uuid)

            # when the Rfam family is not found, or has no secondary structure,
            # this code is not aware of that, and sends you to the pending page.

            # redirect to the pending page
            query_info = {}
            query_info['query_id'] = uuid
            query_info['title'] = 'Rfam family ' + uuid
            query_info['formatted_input'] = ""

            num = {}
            num["seq"] = 0
            num["loop_instances"] = 0

            return render(request,'base_result_pending.html',
                                  {'query_info': query_info, 'num': num})

            # redirect to the url again, now the results should be visible
            # but it seems that it does the redirect too soon, and the
            # results are not yet available
            redirect_url = reverse('result', args=[uuid])
            return HttpResponse(json.dumps({'redirect': redirect_url}))
        else:
            return render(request,'base_result_not_found.html',{'query_id': uuid})

    version = q.group_set[2:q.group_set.index('/')]

    results = ResultsMaker(query_id=uuid)
    results.get_loop_results(version)
    results.get_input_stats()

    """
        status codes:
        -1 - failed
        0  - submitted to the queue ... but now in 2025, this also happens when successful
        1  - done
        2  - submitted to JAR3D
    """

    logger.debug("views.py: Got input stats")
    logger.debug(str(results))
    logger.debug(str(q))
    logger.debug("views.py: Database status: %s" % str(q.status))

    if q.status == 1:
        # successful results for one or more loops
        # zippedResults gives back loops, sequences, indices, mins in that order
        zippedResults = dont_sort_loops(results.loops, results.indices, results.sequences)

        if rfam_result:
            rfam_to_pdb_chains = get_rfam_to_pdb_chains()
            pdb_count = len(rfam_to_pdb_chains.get(rfam_family, []))
            # print(rfam_family)
            # print(rfam_to_pdb_chains)
        else:
            pdb_count = -1

        logger.debug("views.py: database status 1, about to run make_input_alignment")
        q.formatted_input = make_input_alignment(q.parsed_input, q.query_type)
        return render(request,'base_result_done.html',
                                  {'query_info': q, 'num': results.input_stats, 'pdb_count': pdb_count, 'rfam_family': rfam_family,
                                   'results': zippedResults, 'compress': False, 'hide_refine_button': rfam_result})
    elif q.status == 0 or q.status == 2:
        logger.debug("views.py: database status 0 or 2, about to run make_input_alignment")
        q.formatted_input = make_input_alignment(q.parsed_input, q.query_type)
        return render(request,'base_result_pending.html',
                                  {'query_info': q, 'num': results.input_stats})
    else:
        return render(request,'base_result_failed.html',
                                  {'query_info': q, 'num': results.input_stats})


def all_result(request, uuid, loopid):
    """
    View all the matches to a given loop
    """

    # recognize and bounce LSU, SSU, tRNA Rfam families
    if re.match(r'^RF[0-9]{5}-[0-9]+\.[0-9]+$', uuid):
        rfam_result = True
        rfam_family = uuid.split('-')[0]
        value = ""
        if rfam_family in LSU:
            value = 'Rfam ribosomal LSU families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + rfam_family
        elif rfam_family in SSU:
            value = 'Rfam ribosomal SSU families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + rfam_family
        elif rfam_family in tRNA:
            value = 'Rfam ribosomal tRNA families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + rfam_family
        if value:
            return HttpResponse(value)
    else:
        rfam_result = False
        rfam_family = ""

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
        # sort loops by the minimum index in each column ... bad idea, breaks the
        # connection between the name of the loop on the page, which is a for loop index,
        # and the actual loop index in the database; it's not a +1 problem, either
        # Why is this even here?  Here we have just one loop being shown
        zippedResults = dont_sort_loops(results.loops, results.indices, results.sequences)

        if rfam_result:
            rfam_to_pdb_chains = get_rfam_to_pdb_chains()
            # print(rfam_family)
            # print(rfam_to_pdb_chains)
            pdb_count = len(rfam_to_pdb_chains.get(rfam_family, []))
        else:
            pdb_count = -1

        q.formatted_input = make_input_alignment(q.parsed_input, q.query_type)
        return render(request,'base_result_done.html',
                                  {'query_info': q, 'num': results.input_stats, 'pdb_count': pdb_count, 'rfam_family': rfam_family,
                                   'results': zippedResults, 'compress': True, 'loop_id': int(loopid)})
    elif q.status == 0 or q.status == 2:
        q.formatted_input = make_input_alignment(q.parsed_input, q.query_type)
        return render(request,'base_result_pending.html',
                                  {'query_info': q, 'num': results.input_stats})
    else:
        return render(request,'base_result_failed.html',
                                  {'query_info': q, 'num': results.input_stats})


def motif_hits(request, motifgroup):
    """
    Query the database to find all Rfam families with a good hit for one motif group
    """

    # here is the mysql query for how to get the list of hits:
    # SELECT query_id, loop_id, motif_id, cutoff_percent FROM jar3d_results_by_loop WHERE cutoff_percent > 80 AND query_id LIKE 'RF%-%.%' AND motif_id in ('IL_04346.4','IL_35110.4');

    motif_groups = motifgroup.split(",")
    cutoff_percent = 80
    results = (
        Results_by_loop.objects.filter(
            cutoff_percent__gt=cutoff_percent,  # cutoff_percent > 80
            query_id__regex=r'^RF[0-9]+-[0-9]+\.[0-9]+$',  # query_id LIKE 'RF%-%.%'
            # motif_id__in=['IL_04346.4', 'IL_35110.4']  # motif_id IN (...)
            motif_id__in=motif_groups  # motif_id IN (...)
        )
        .values('query_id', 'loop_id', 'motif_id', 'cutoff_percent', 'medianinterioreditdist', 'medianfulleditdist', 'mean_cutoff_score')  # SELECT specific fields
    )

    # Sort by query_id, then loop_id, then motif_id
    results = sorted(results, key=lambda x: (x['query_id'], x['loop_id'], x['motif_id']))

    version = '3.48'
    for result in results:
        print(result)
        query_id = result['query_id']
        fields = query_id.split('-')
        if len(fields) == 2:
            version = fields[1]
            break


    motif_id_to_annotation = get_motif_annotations(version)
    for result in results:
        motif_id = result['motif_id']
        if motif_id in motif_id_to_annotation:
            result['annotation'] = motif_id_to_annotation[motif_id]
        else:
            result['annotation'] = ''

    # response_text = "Results:\n"
    # for result in results:
    #     response_text += f"Query ID: {result['query_id']}, Loop ID: {result['loop_id']}, "
    #     response_text += f"Motif ID: {result['motif_id']}, Cutoff Percent: {result['cutoff_percent']}\n"

    # # Return the response as plain text
    # return HttpResponse(response_text, content_type="text/plain")

    return render(request,'base_loop_rfam.html',
                        {'motif_ids': motif_groups, 'results': results})


def single_result(request, uuid, loopid, motifgroup):
    """
    View the alignment of one loop against one motif group
    """

    # recognize and bounce LSU, SSU, tRNA Rfam families
    if re.match(r'^RF[0-9]{5}-[0-9]+\.[0-9]+$', uuid):
        rfam_family = uuid.split('-')[0]
        value = ""
        if rfam_family in LSU:
            value = 'Rfam ribosomal LSU families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + rfam_family
        elif rfam_family in SSU:
            value = 'Rfam ribosomal SSU families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + rfam_family
        elif rfam_family in tRNA:
            value = 'Rfam ribosomal tRNA families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + rfam_family
        if value:
            return HttpResponse(value)

    # I'm not happy about this, but it seems to help
    java_loopid = str(int(loopid) - 1)

    # query jar3d_loop_results_queue to see if the job already ran successfully
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
        # logger.info("views.py is excluding %s" % uuid)
        return render(request,'base_result_loop_failed.html',
                                  {'query_info': q,
                                   'loop': loopid, 'group': motifgroup})

    title = Query_info.objects.filter(query_id=uuid)[0].title

    if q:
        q.title = title  # needed on the page below
        q.formatted_input = ''   # let's not work too hard for the pending/failed pages

        # in 2025, q.status seems to be set to 0 even when successful
        if False and q.status == 0:
            # query has already been started, back in the day when there was a queue
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

            # get information about the query
            query = Loop_query_info(query_id=uuid, loop_id=loopid, status=0, motif_group=motifgroup)
            # save it in jar3d_loop_results_queue
            query.save()

            # align sequences of a specific loop to a specific motif group model
            align({
                'id': uuid,
                'loop_id': java_loopid,
                'motif_group': motifgroup,
                'version': version
            })
            # seems that status is updated by the java program once it finishes running

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
        # this query can only supply cutoff score, edit distance, not a specific mapping
        seq_res = Results_by_loop_instance.objects.filter(query_id=uuid) \
                                          .filter(loop_id=java_loopid).filter(motif_id=motifgroup).order_by('seq_id')

        # for internal loops, we need to know which rotation to use
        # https://rna.bgsu.edu/jar3d/result/75df3aba-236a-4fec-9bc9-d214c53b5b58/1/IL_29509.1/ trouble
        # there is no index 0
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
            # This is where we get the correspondence between sequence positions
            # and model nodes
            # result_instance_id matches id from results_by_loop_instance
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

        # /var/www/html/data/jar3d/models/IL/3.48/lib/IL_01239.1_correspondences.txt
        # https://rna.bgsu.edu/data/jar3d/models/IL/3.48/lib/IL_01239.1_correspondences.txt
        # https://rna.bgsu.edu/data/jar3d/models/IL/3.48/lib/IL_34907.1_correspondences.txt
        # These files are not quite the same as what is in the jar3d_correspondences table
        # They have lines with things like
        # IL_34907.1_Instance_1_Column_1_C corresponds_to_PDB 4WF9.cifatoms|1|X|1388|C
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
                                         'isNoFastaMultipleSequencesSS',
                                         'isRfamFamily'],
        }

    def validate(self, request_raw):

        if type(request_raw) == str:
            if re.match(r'^RF[0-9]{5}-[0-9]+\.[0-9]+$', request_raw):
                # url like https://rna.bgsu.edu/jar3d/result/RF00003-3.48/
                # if request_raw matches the pattern RF[0-9]{5}-[0-9]+\.[0-9]+ ...
                # then it is an RFAM id and we need to process it

                query_id = request_raw

                request = {}
                request["parsed_input"] = request_raw.split('-')[0]
                request["version"] = request_raw.split('-')[1]
                request["query_type"] = "isRfamFamily"
                if not request["version"] in ["3.48"]:
                    request["version"] = "3.48"
            else:
                return self.respond("Could not make sense of %s" % (request_raw))
        else:
            # get the data from the json string in the request
            request = json.loads(request_raw.body)
            parsed_input = request.get('parsed_input', '')

            if re.match(r'^RF[0-9]{5}$', parsed_input):
                # typed and Rfam family like RF01234 in the input box and hit submit
                if not request.get("version","3.48") in ["3.48"]:
                    request["version"] = "3.48"
                query_id = parsed_input + '-' + request["version"]
            else:
                # create a new query id in the format 97f3fbcb-4f1d-4ab4-b179-3d1bce3c4595
                query_id = str(uuid.uuid4())

        version = request.get('version','3.48')

        # redirect_url = reverse('app.views.result', args=[query_id])
        redirect_url = reverse('result', args=[query_id])

        if request.get('query_type', '') == 'isRfamFamily':
            rfam_family = request.get('parsed_input', '')
            print("JAR3D is processing %s with %s" % (rfam_family,version))

            group_set='IL' + version + '/HL' + version

            # query table jar3d_query_info for an entry where the email column
            # is equal to the rfam_family and the version matches as well
            q = Query_info.objects.filter(email=rfam_family,group_set=group_set).first()
            if q:
                q_id = q.query_id
                redirect_url = reverse('result', args=[q_id])
                # redirect user to output page for this query_id
                return self.respond(redirect_url, 'redirect')
            else:
                # process this Rfam family for the first time
                fasta_all, title = process_rfam_alignment(rfam_family)

                if not fasta_all:
                    return self.respond("Could not find a seed alignment for %s" % (rfam_family))

                lines = fasta_all.split('\n')
                ss = lines[0]

                # print("Secondary structure: %s" % ss)

                if not ss:
                    return self.respond("Could not find secondary structure, got %s and title %s" % (ss,title))

                if len(ss) == 0:
                    return self.respond("Could not find secondary structure, got %s and title %s" % (ss,title))

                # header lines starting with entry 1 and taking every other line
                fasta = lines[1::2]

                # print("Fasta: %s" % fasta)
                # sequence lines starting with entry 2 and taking every other line
                data = lines[2::2]

                # print("Data: %s" % data)

                # single text string separated by \n
                parsed_input = fasta_all

                # use the email column to store the Rfam family; sloppy, but it works
                email = rfam_family

        else:
            title = request.get('title', 'JAR3D Search')
            # secondary structure
            ss = request.get('ss', 'No secondary structure')
            # header lines
            fasta = request.get('fasta', [])
            # sequence lines
            data = request.get('data', [])
            # single text string separated by \n
            parsed_input = request.get('parsed_input', 'No parsed input')
            email = ""

        # uppercase all base strings and translate DNA to RNA
        data = [x.upper().replace('T', 'U') for x in data]
        query_type = request.get('query_type', 'Unknown query type')

        if query_type in self.query_types['UNAfold_extract_loops']:
            try:
                loops, indices = self.UNAfold_extract_loops(data)
            except fold.FoldingTimeOutError:
                return self.respond("Folding timed out")
            except fold.FoldingFailedError:
                return self.respond("Folding failed")
            except:
                return self.respond("Could not fold and extract loops")

        elif query_type in self.query_types['isfolded_extract_loops']:
            # the main case, where the user provides a secondary structure
            try:
                loops, indices = self.isfolded_extract_loops(ss, data, query_type)
            except fold.FoldingTimeOutError:
                return self.respond("Folding timed out")
            except fold.FoldingFailedError:
                return self.respond("Folding failed")
            except:
                return self.respond("Could not extract loops")

        elif query_type in self.query_types['loops']:
            # individual loops that don't need a secondary structure
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
                return self.respond("Could not extract loops")

        else:
            return self.respond("Unrecognized query type")

        # put code here that turns loops, indices into loops_list, indices_list
        # where the two lists are in sync and the indices are sorted by minimum index
        # so that loops can be listed on the page in order across the alignment columns
        # then code above will continue to work
        indices_list, new_loops = self.renumber_loops(loops, indices)

        query_info = self.make_query_info(query_id, query_type, parsed_input, title, version, email)
        query_sequences = self.make_query_sequences(new_loops, fasta, query_id)
        query_positions = self.make_query_indices_from_list(indices_list, query_id)

        # don't proceed unless there are loops
        if not query_sequences:
            return self.respond("No loops found in the input")

        # todo: if all loops have status = -1, then set query_info.status to 1

        # persist the entries in the database starting with sequences
        # query_sequences, query_positions, mins = zip(*sort_sequences(query_positions, query_sequences))
        try:
            if query_type == "isRfamFamily":
                for seq in query_sequences:
                    # save all the sequences
                    seq.save()

                    # if sequence is defective in some way, then don't save the sequence
                    # if seq.status != -1:
                    #     seq.save()
            else:
                for seq in query_sequences:
                    seq.save()

        except:
            return self.respond("Could not save query_sequences")
        try:
            for ind in query_positions:
                ind.save()
        except:
            return self.respond("Could not save query_positions")
        try:
            query_info.save()
        except Exception:
            return self.respond("Could not save query_info")

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
            return self.respond("Could not score the loops in the query")


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

            # print('make_query_sequences')
            # print('make_query_sequences: query_id:    %s' % query_id)
            # print('make_query_sequences: seq_id:      %s' % seq_id)
            # print('make_query_sequences: loop_id:     %s' % loop_id)
            # print('make_query_sequences: loop_type:   %s' % loop_type)
            # print('make_query_sequences: loop:        %s' % loop)
            # print('make_query_sequences: internal_id: %s' % internal_id)

            # check to see if the sequence can make the indicated type of loop
            # old, which did not entirely work
            # HL_pattern = '(^[acgu](.+)?[acgu])'
            # IL_pattern = '(^[acgu](.+)?[acgu](\*[acgu](.+)?[acgu])?$)'

            # HL pattern: At least two characters that are ACGU and not '-'
            HL_pattern = r'^(?=(.*[ACGU]){2})[ACGU-]+$'

            status = -1
            if loop_type == "HL":
                if re.match(HL_pattern, loop, flags=re.IGNORECASE):
                    status = 0
            elif loop_type == "IL":
                strands = loop.split("*")
                if len(strands) == 2:
                    if re.match(HL_pattern, strands[0], flags=re.IGNORECASE):
                        if re.match(HL_pattern, strands[1], flags=re.IGNORECASE):
                            status = 0

            query_sequences.append(Query_sequences(query_id=query_id,
                                                   seq_id=seq_id,
                                                   loop_id=loop_id,
                                                   loop_type=loop_type,
                                                   loop_sequence=loop,
                                                   internal_id='>seq%i' % internal_id,
                                                   user_seq_id='' if len(fasta) == 0 else fasta[seq_id],
                                                   status=status))
        return query_sequences

    def make_query_indices(self, indices, query_id):
        """
        Pre-2024 code, where indices is a dictionary from keys like
        'internal', 'hairpin', and 'external' to a list of tuples of lists of indices
        For hairpins, the second entry in the tuple is simply not there, not even an empty list
        """
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

    def make_query_indices_from_list(self, indices_list, query_id):
        """
        New code in 2024 treats indices as a list of tuples of lists of indices
        The tuples are in order of minimum index so they display nicely
        It's a little more complicated than that, here is an example:
        [(([0, 1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12, 13]), 1, 0)]
        new_loop_id runs 1, 2, 3, ...
        mins might start at 0, it's the smallest column index
        """
        query_positions = []
        loop_id = 0
        for loop, new_loop_id, mins in indices_list:
            for side in loop:
                for index in side:
                    query_positions.append(Query_loop_positions(query_id=query_id,
                                                                loop_id=new_loop_id,
                                                                column_index=index))
            loop_id = loop_id + 1
        return query_positions

    def renumber_loops(self, loops, indices):
        # loops is a dictionary from (loop_type, seq_id, loop_id) to loop_sequence
        # indices is a dictionary from loop_type to a list of tuples of lists of indices
        # the problem is that the loop_id is not in a nice order and the order is
        # not very reliable when there are external loops in addition to internal and hairpin loops
        # also we want to display loops on the screen in order of minimum index,
        # but re-ordering indices without re-ordering loops wreaks havoc.
        # we should map the loop ids so they are in order of minimum index
        # we should also not number loops that are not HL or IL

        # collect the loop types in the same order as they were stored, by sorting by
        # original loop_id, which is the third element of the key
        loop_types = []
        triples = sorted(loops.keys(), key=lambda x: (x[2]))
        for loop_type, seq_id, loop_id in triples:
            if not loop_type in loop_types:
                loop_types.append(loop_type)

        # print to error_log for debugging
        print('indices', indices)

        # accumulate the tuples of column indices in the same order as they were stored
        loop_id = 0        # original loop id according to the parser
        indices_list = []  # indices for hairpin, internal loops only
        for loop_type in loop_types:
            for index_tuple in indices[loop_type]:
                if loop_type in ['hairpin', 'internal']:
                    # only store the HL and IL, not external or whatnot
                    min_index = min(index_tuple[0])
                    indices_list.append((index_tuple, loop_id, min_index))
                # count all the loops so we stay consistent with original loop id
                loop_id += 1

        # original loop_id is now common to both triples and indices_list and can
        # be used to get them in a different order

        # sort index tuples by min_index, the order we want to display them in
        indices_list = sorted(indices_list, key=lambda x: x[2])

        # print to error_log for debugging
        print('indices_list', indices_list)

        # map original loop_id to new loop_id starting at 1
        original_id_to_new_id = {}
        for new_loop_id, (indices, loop_id, min_index) in enumerate(indices_list):
            original_id_to_new_id[loop_id] = new_loop_id + 1

        # print to error_log for debugging
        print('original_id_to_new_id', original_id_to_new_id)

        # replace indices_list with a list that uses the new loop_id
        new_indices_list = []
        for indices, loop_id, min_index in indices_list:
            new_loop_id = original_id_to_new_id[loop_id]
            new_indices_list.append((indices, new_loop_id, min_index))

        # print to error_log for debugging
        print('new_indices_list', new_indices_list)

        # replace loops dictionary with a new dictionary with new loop_id
        # as the third element of the key
        new_loops = {}
        for key, loop in loops.items():
            loop_type, seq_id, loop_id = key
            if loop_id in original_id_to_new_id:
                new_loop_id = original_id_to_new_id[loop_id]
                new_loops[(loop_type, seq_id, new_loop_id)] = loop

        return new_indices_list, new_loops

    def make_query_info(self, query_id, query_type, parsed_input, title="testing", version="3.48", email=""):
        query_info = Query_info(query_id=query_id,
                                group_set='IL' + version + '/HL' + version,
                                model_type='default',  # change this
                                query_type=query_type,
                                title=title,
                                structured_models_only=0,
                                email=email,
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
            dot_string = '(' + '.'*(len(loop)-2) + ')'
            strands = loop.split('*')
            if len(strands) == 1:
                loop_type = 'hairpin'
            elif len(strands) == 2:
                loop_type = 'internal'
                break_point = loop.find('*')
                dot_string = dot_string[:break_point-1] + '(.)' + dot_string[break_point+2:]
            else:
                loop_type = 'junction'

            loops[(loop_type, seq_id, loop_id)] = loop
            parser = Dot.Parser(dot_string)
            indices = parser.indices(flanking=True)
        return loops, indices

    def respond(self, value, key=None):
        """
        if key == error, the message will be shown to the user
        """
        if key:
            return HttpResponse(json.dumps({key: value}))
        else:
            return HttpResponse(value)


    def isfolded_extract_loops(self, dot_string, sequences, query_type):
        """
        This is the primary way that loops are extracted from the dot-bracket structure

        Input: secondary structure + list of sequences
            sequences is a list of tuples (seq_id, sequence)
        Output:
            results[('internal',0,0)] = 'CAG*CAAG'
            results[('internal',1,0)] = 'CAG*CAUG'
        """
        parser = Dot.Parser(dot_string)
        indices = parser.indices(flanking=True)
        results = dict()

        # loop over every input sequence, keeping the sequences in order
        for seq_id, seq in enumerate(sequences):
            # loops is a dictionary from loop type to a list of loops of that type
            loops = parser.loops(seq, flanking=True)
            loop_id = 0
            for loop_type, loop_instances in loops.items():  # hairpin or internal or external
                for loop in loop_instances:
                    results[(loop_type, seq_id, loop_id)] = loop
                    loop_id += 1

        # indices is a dictionary from loop type to a list of lists of indicess
        # results has loop_id as a kind of index, and that is the only connection
        # between which loop goes with which index.  That is loose and fragile.
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
        if self.loop_id == -1:
            # showing summary across all loops
            ignore_cutoff = False   # Only show results with cutoff precent > 0
            results = Results_by_loop.objects.filter(query_id=self.query_id) \
                                             .order_by('loop_id',
                                                       '-cutoff_percent',
                                                       '-mean_cutoff_score')
        else:
            # showing all results for a specific loop
            ignore_cutoff = True   # Show results for all motif groups regardless of cutoff
            results = Results_by_loop.objects.filter(query_id=self.query_id, loop_id=self.loop_id) \
                                             .order_by('-cutoff_percent',
                                                       '-mean_cutoff_score')
        if results:
            """
            build a 2d list
            loops[1][0] = result 0 for loop 1
            loops[1][1] = result 1 for loop 1
            """

            motif_id_to_annotation = get_motif_annotations(version)


            loop_ids = []     # all the loop ids returned by the result
            res_list = set()  # List of tuples, to avoid duplicate entries
            for result in results:
                # if int(self.loop_id) >= 0:
                #     # showing all results for a specific loop
                #     count_id = 0
                # else:
                #     # showing top results for all loops
                #     count_id = result.loop_id

                tup = (result.loop_id, result.motif_id)
                if tup in res_list:
                    continue
                else:
                    res_list.add(tup)

                result.motif_url = self.RNA3DHUBURL + 'motif/view/' + result.motif_id
                result.align_url = '/jar3d/result/%s/%s/' % (result.query_id, result.loop_id)
                result.ssurl = self.SSURL + result.motif_id[0:2] + version + '/' + result.motif_id + '.png'
                result.annotation = motif_id_to_annotation.get(result.motif_id, 'No annotation')

                if not result.loop_id in loop_ids:
                    # new loop_id found
                    loop_ids.append(result.loop_id)
                    if result.cutoff_percent > 0 or ignore_cutoff:
                        # start a new list with results
                        self.loops.append([result])
                    else:
                        # start a new list with no results
                        self.loops.append([])
                else:
                    # self.loops is going to be a list of lists of length up to TOPRESULTS
                    if ignore_cutoff or (len(self.loops[-1]) < self.TOPRESULTS and result.cutoff_percent > 0):
                        # when the last list is not already too long, add to it
                        self.loops[-1].append(result)

            # retrieve information about sequences and indices for the loops seen here
            for loop_id in loop_ids:
                query_seqs = Query_sequences.objects.filter(query_id=self.query_id, loop_id=loop_id).order_by('seq_id')
                loop_inds = Query_loop_positions.objects.filter(query_id=self.query_id, loop_id=loop_id).order_by('loop_id','column_index')

                seqs = []
                for entries in query_seqs:
                    seqs.append(entries.loop_sequence)
                self.sequences.append(seqs)

                inds = []
                for ind in loop_inds:
                    if not ind.column_index in inds:
                        inds.append(ind.column_index)

                # suddenly these are not coming out sorted, so sort here
                inds = sorted(inds)

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


def get_rfam_to_pdb_chains():
    """
    Read the file of mappings from PDB chains to Rfam families
    Return a dictionary that maps Rfam family to a list of PDB chains
    RF00001	4v4h	BA	3	118	77.20	6.4e-17	1	119	8484c0
    """

    url = 'https://rna.bgsu.edu/data/pdb_chain_to_rfam.txt'

    try:
        response = urllib.request.urlopen(url)
        data = response.read()
        text = data.decode('utf-8')
    except:
        return {}

    rfam_to_pdb_chains = {}
    for line in text.split("\n"):
        fields = line.split("\t")
        if len(fields) == 10:
            rfam = fields[0]
            pdb  = fields[1]
            chain = fields[2]
            if not rfam in rfam_to_pdb_chains:
                rfam_to_pdb_chains[rfam] = []
            rfam_to_pdb_chains[rfam].append(pdb.upper() + "|1|" + chain)

    return rfam_to_pdb_chains


def get_motif_annotations(version):

    motif_id_annotation_to_count = {}

    # get HL and IL annotations by visiting https://rna.bgsu.edu/rna3dhub/motifs/release/il/3.48/annotations
    for loop_type in ['hl', 'il']:
        url = 'https://rna.bgsu.edu/rna3dhub/motifs/release/' + loop_type + '/' + version + '/annotations'
        try:
            response = urllib.request.urlopen(url)
            data = response.read()
            text = data.decode('utf-8')
        except:
            text = ""

        for line in text.split("\n"):
            if line:
                motif_id, loop_id, annotation, mapped_annotation = line.split("\t")
                if not motif_id in motif_id_annotation_to_count:
                    motif_id_annotation_to_count[motif_id] = {}
                if not annotation in motif_id_annotation_to_count[motif_id]:
                    motif_id_annotation_to_count[motif_id][annotation] = 0
                motif_id_annotation_to_count[motif_id][annotation] += 1

    motif_id_to_annotation = {}
    for motif_id, annotations in motif_id_annotation_to_count.items():
        max_annotation = max(annotations, key=annotations.get)
        motif_id_to_annotation[motif_id] = max_annotation

    return motif_id_to_annotation

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


def dont_sort_loops(loops, indices, sequences):
    mins = []
    for ranges in indices:
        mins.append(ranges.replace(',', '-').split("-")[0])
    unsorted_lists = list(zip(loops, sequences, indices, mins))
    return unsorted_lists


# def sort_sequences(indices, sequences):
#     mins = [min(inds.split(', '), key=int) for inds in indices]
#     mins = [str(x) for x in mins]
#     sorted_lists = sorted(zip(sequences, indices, mins), key=lambda x: int(x[2]))
#     return sorted_lists


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
    # has_ss = False
    # has_fasta = False
    # fasta = ['isFastaSingleSequenceSS',
    #          'isFastaMultipleSequencesSS',
    #          'isFastaSingleSequenceNoSS',
    #          'isFastaMultipleSequencesNoSS',
    #          'isRfamFamily']
    # SSs = ['isFastaSingleSequenceSS',
    #        'isNoFastaSingleSequenceSS',
    #        'isFastaMultipleSequencesSS',
    #        'isNoFastaMultipleSequencesSS']
    # if query_type in fasta:
    #     has_fasta = True
    # if query_type in SSs:
    #     has_ss = True

    # Make formatted alignment for display
    # Use the last sequence line to get the length
    seq_length = len(query_lines[-1])

    # make header lines telling column number; nice if we could make it not scroll
    l = []
    # 1000s place
    if seq_length >= 1000:
        for i in range(1, seq_length+1):
            l.append(str(i % 10000//1000))
        l.append('\n')
    # 100s place
    if seq_length >= 100:
        for i in range(1, seq_length+1):
            l.append(str(i % 1000//100))
        l.append('\n')
    if seq_length >= 10:
        for i in range(1, seq_length+1):
            l.append(str(i % 100//10))
        l.append('\n')
    for i in range(1, seq_length+1):
        l.append(str(i % 10))
    l.append('\n')
    # l.append('='*seq_length+'\n')
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
