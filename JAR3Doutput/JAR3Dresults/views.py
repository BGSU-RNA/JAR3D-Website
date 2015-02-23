
from django.shortcuts import render_to_response

from django.http import HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse

from JAR3Dresults.models import Query_info
from JAR3Dresults.models import Query_sequences
from JAR3Dresults.models import Query_loop_positions
from JAR3Dresults.models import Results_by_loop
from JAR3Dresults.models import Results_by_loop_instance
from JAR3Dresults.models import Loop_query_info
from JAR3Dresults.models import Correspondence_results

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
        q.formatted_input = make_input_alignment(q.parsed_input,q.query_type)
        return render_to_response('JAR3Doutput/base_result_done.html',
                                  {'query_info': q, 'num': results.input_stats,
                                   'results': zippedResults},
                                  context_instance=RequestContext(request))
    elif q.status == 0 or q.status == 2:
        q.formatted_input = make_input_alignment(q.parsed_input,q.query_type)
        return render_to_response('JAR3Doutput/base_result_pending.html',
                                  {'query_info': q, 'num': results.input_stats},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('JAR3Doutput/base_result_failed.html',
                                  {'query_info': q, 'num': results.input_stats},
                                  context_instance=RequestContext(request))

def single_result(request,uuid,loopid,motifgroup):
    q = Loop_query_info.objects.filter(query_id=uuid).filter(loop_id=loopid).filter(motif_group=motifgroup)
    rows = []
    if q:
        q = q[0]  # We are interested only in the first one
    else:
        query = Loop_query_info(query_id = uuid, loop_id = loopid, status = 0, motif_group = motifgroup)
        query.save();
        return render_to_response('JAR3Doutput/base_result_loop_pending.html',
                                  {'query_info': q,
                                  'loopnum': loopid, 'motifid': motifgroup},
                                  context_instance=RequestContext(request))
    seq_res = Results_by_loop_instance.objects.filter(query_id=uuid).filter(loop_id=loopid).filter(motif_id=motifgroup)
    for indx, res in enumerate(seq_res):
        corrs = Correspondence_results.objects.filter(result_instance_id = res.id)
        line_base = 'Sequence_' + str(res.seq_id)
        for corr_line in corrs:
            seq = Query_sequences.objects.filter(query_id = uuid, seq_id = res.seq_id, loop_id = loopid)[0].loop_sequence
            line = (line_base + '_Position_' + str(corr_line.sequence_position) + '_' +
                seq[corr_line.sequence_position-1] + ' aligns_to_JAR3D ' + res.motif_id + '_Node_' + str(corr_line.node) +
                '_Position_' + corr_line.node_position)
            if corr_line.is_insertion:
                line = line + '_Insertion'
            rows.append(line)
        name = Query_sequences.objects.filter(query_id = uuid, seq_id = res.seq_id, loop_id = loopid)[0].user_seq_id
        if len(name) == 0:
            name = 'Sequence' + str(indx)
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
    instance_text = '\n'.join(rows)
    # This is cheesy, fix asap
    filenamewithpath = '/Users/api/Models/IL/1.13/lib/' + motifgroup + '_correspondences.txt'
    with open(filenamewithpath,"r") as f:
        model_text = f.readlines()
    header, motifalig, sequencealig = alignsequencesandinstancesfromtext(model_text,rows)
    seq_text = '\n'.join(rows)
    model_text = '\n'.join(model_text)
    body_lines = []
    col_nums = ['Column']
    for i in range(1, len(header['nodes'])+1):
        col_nums.append(i)
    col_nums = col_nums + ['','','Interior','Full']
    position = ['Position'] + header['positions'] + ['','Cutoff','Edit','Edit']
    insertions = []
    for item in header['insertions']:
        insertions.append(item.replace('Insertion', 'I'))
    insertions = ['Insertion'] + insertions + ['Cutoff','Score','Distance','Distance']
    header_zip = zip(col_nums,position,insertions)
    mkeys = sorted(motifalig.keys())
    for key in mkeys:
        line = motifalig[key]
        body_lines.append([key] + line + ['','','',''])
    skeys = sorted(sequencealig.keys())
    for indx, res in enumerate(seq_res):
        key = 'Sequence_' + str(indx)
        name = Query_sequences.objects.filter(query_id = uuid, seq_id = res.seq_id, loop_id = loopid)[0].user_seq_id
        if len(name) == 0:
            name = 'Sequence' + str(indx)
        cutoff = 'True'
        if res.cutoff == 0:
            cutoff = 'False'
        line = [name] + sequencealig[key] + [cutoff,res.cutoff_score,res.interioreditdist,res.fulleditdist]
        body_lines.append(line)
    q = Query_info.objects.filter(query_id=uuid)
    q = q[0]  # We are interested only in the first one
    return render_to_response('JAR3Doutput/base_result_loop_done.html',
                                  {'query_info': q, 'header_zip': header_zip,
                                  'body_lines': body_lines, 'seq_text': seq_text,
                                  'model_text': model_text},
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
    return sorted_lists

def sort_sequences(indices, sequences):
    mins = [ min(inds.split(', '), key = int) for inds in indices ]
    mins = [ str(x) for x in mins ]
    sorted_lists = sorted(zip(sequences, indices, mins), key = lambda x: int(x[2]))
    return sorted_lists

def make_input_alignment(parsed_input, query_type):
    #If inut is just one loop, return
    loops = ['isFastaSingleLoop',
            'isNoFastaSingleLoop',
            'isFastaMultipleLoops',
            'isNoFastaMultipleLoops']
    if query_type in loops:
       return parsed_input
    #Get info about query
    query_lines = parsed_input.splitlines()
    has_ss = False;
    has_fasta = False;
    fasta = ['isFastaSingleSequenceSS',
            'isFastaMultipleSequencesSS',
            'isFastaSingleSequenceNoSS',
            'isFastaMultipleSequencesNoSS']
    SSs =   ['isFastaSingleSequenceSS',
            'isNoFastaSingleSequenceSS',
            'isFastaMultipleSequencesSS',
            'isNoFastaMultipleSequencesSS']
    if query_type in fasta:
        has_fasta = True
    if query_type in SSs:
        has_ss = True
    #Make formatted alignment for display
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
            l.append(str(i%100//10))
        l.append('\n')
    for i in range(1, seq_length+1):
        l.append(str(i%10))
    l.append('\n')
    l.append('='*seq_length+'\n')
    line = 0
    while line < len(query_lines):
        l.append(query_lines[line] + '\n')
        line += 1
    out = ''.join(l)
    return out

def alignsequencesandinstancesfromtext(MotifCorrespondenceText,SequenceCorrespondenceText):

  InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn = readcorrespondencesfromtext(MotifCorrespondenceText)[:5]
  NotInstanceToGroup, NotInstanceToPDB, NotInstanceToSequence, NotGroupToModel, NotModelToColumn, SequenceToModel = readcorrespondencesfromtext(SequenceCorrespondenceText)[:6]

  motifalig = {}

  for a in InstanceToGroup.iterkeys():
    m = re.search("(Instance_[0-9]+)",a)
    motifalig[m.group(1)] = [''] * len(ModelToColumn)     # start empty

  for a in sorted(InstanceToGroup.iterkeys()):
    m = re.search("(Instance_[0-9]+)",a)
    t = int(ModelToColumn[GroupToModel[InstanceToGroup[a]]])
    motifalig[m.group(1)][t-1] += a[len(a)-1]

  sequencealig = {}

  for a in SequenceToModel.iterkeys():
    m = re.search("(Sequence_[0-9]+)",a)
    sequencealig[m.group(1)] = [''] * len(ModelToColumn)  # start empty

  for a in sorted(SequenceToModel.iterkeys()):
    m = re.search("(Sequence_[0-9]+)",a)
    t = int(ModelToColumn[SequenceToModel[a]])
    sequencealig[m.group(1)][t-1] += a[len(a)-1]

  header = {}              # new dictionary
  header['columnname'] = [''] * len(ModelToColumn)
  header['nodes'] = [''] * len(ModelToColumn)
  header['positions'] = [''] * len(ModelToColumn)
  header['insertions'] = [''] * len(ModelToColumn)

  for a in ModelToColumn.iterkeys():
    header['columnname'][int(ModelToColumn[a])-1] = a

  for i in range(0,len(ModelToColumn)):
    m = re.search("Node_([0-9]+)",header['columnname'][i])
    a = m.group(1)
    header['nodes'][i] = a
    if re.search("Insertion",header['columnname'][i]):
      header['insertions'][i] = 'Insertion'

  for a in GroupToModel.iterkeys():
    m = re.search("Column_([0-9]+)$",a)
    if m is not None:
      colnum = ModelToColumn[GroupToModel[a]]
      header['positions'][int(colnum)] = m.group(1)

  return header, motifalig, sequencealig

def readcorrespondencesfromtext(lines):

  InstanceToGroup = {}          # instance of motif to conserved group position
  InstanceToPDB = {}            # instance of motif to NTs in PDBs
  InstanceToSequence = {}       # instance of motif to position in fasta file
  GroupToModel = {}             # positions in motif group to nodes in JAR3D model
  ModelToColumn = {}            # nodes in JAR3D model to display columns
  HasName = {}                  # organism name in FASTA header
  SequenceToModel = {}          # sequence position to node in JAR3D model
  HasScore = {}                 # score of sequence against JAR3D model
  HasInteriorEdit = {}          # minimum interior edit distance to 3D instances from the motif group
  HasFullEdit = {}              # minimum full edit distance to 3D instances from the motif group
  HasCutoffValue = {}           # cutoff value 'true' or 'false'
  HasCutoffScore = {}           # cutoff score, 100 is perfect, 0 is accepted, negative means reject
  HasAlignmentScoreDeficit = {} # alignment score deficit, how far below the best score among 3D instances in this group

  for line in lines:
    if re.search("corresponds_to_group",line):
        m = re.match("(.*) (.*) (.*)",line)
        InstanceToGroup[m.group(1)] = m.group(3)
    elif re.search("corresponds_to_PDB",line):
        m = re.match("(.*) (.*) (.*)",line)
        InstanceToPDB[m.group(1)] = m.group(3)
    elif re.search("corresponds_to_JAR3D",line):
        m = re.match("(.*) (.*) (.*)",line)
        GroupToModel[m.group(1)] = m.group(3)
    elif re.search("corresponds_to_sequence",line):
        m = re.match("(.*) (.*) (.*)",line)
        InstanceToSequence[m.group(1)] = m.group(3)
    elif re.search("appears_in_column",line):
        m = re.match("(.*) (.*) (.*)",line)
        ModelToColumn[m.group(1)] = m.group(3)
    elif re.search("aligns_to_JAR3D",line):
        m = re.match("(.*) (.*) (.*)",line)
        SequenceToModel[m.group(1)] = m.group(3)
    elif re.search("has_name",line):
        m = re.match("(.*) (.*) (.*)",line)
        HasName[m.group(1)] = m.group(3)
    elif re.search("has_score",line):
        m = re.match("(.*) (.*) (.*)",line)
        HasScore[m.group(1)] = m.group(3)
    elif re.search("has_minimum_interior_edit_distance",line):
        m = re.match("(.*) (.*) (.*)",line)
        HasInteriorEdit[m.group(1)] = m.group(3)
    elif re.search("has_minimum_full_edit_distance",line):
        m = re.match("(.*) (.*) (.*)",line)
        HasFullEdit[m.group(1)] = m.group(3)
    elif re.search("has_cutoff_value",line):
        m = re.match("(.*) (.*) (.*)",line)
        HasCutoffValue[m.group(1)] = m.group(3)
    elif re.search("has_cutoff_score",line):
        m = re.match("(.*) (.*) (.*)",line)
        HasCutoffScore[m.group(1)] = m.group(3)
    elif re.search("has_alignment_score_deficit",line):
        m = re.match("(.*) (.*) (.*)",line)
        HasAlignmentScoreDeficit[m.group(1)] = m.group(3)

  return InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn, SequenceToModel, HasName, HasScore, HasInteriorEdit, HasFullEdit, HasCutoffValue, HasCutoffScore, HasAlignmentScoreDeficit