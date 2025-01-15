# python keytest.py C:\Users\zirbel\Documents\JAR3D\IL\1.13\lib\IL_85647.3_correspondences.txt C:\Users\zirbel\Documents\JAR3D\IL\1.13\diagnostic\IL_85647.3_diagnostics.txt

import sys
import re

def alignsequencesandinstancesfromtext(MotifCorrespondenceText,SequenceCorrespondenceText):

  InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn, NotSequenceToModel, HasName = readcorrespondencesfromtext(MotifCorrespondenceText)[:7]
  NotInstanceToGroup, NotInstanceToPDB, NotInstanceToSequence, NotGroupToModel, NotModelToColumn, SequenceToModel = readcorrespondencesfromtext(SequenceCorrespondenceText)[:6]

  motifalig = {}

  for a in InstanceToGroup.iterkeys():
    m = re.search("(.+Instance_[0-9]+)",a)
    print(m.group(1))
    Name = HasName[m.group(1)]                               # use the name as the key; very informative
    motifalig[Name] = [''] * len(ModelToColumn)     # start empty

  for a in sorted(InstanceToGroup.iterkeys()):
    m = re.search("(.+Instance_[0-9]+)",a)
    print(m.group(1))
    Name = HasName[m.group(1)]                               # use the name as the key; very informative
    t = int(ModelToColumn[GroupToModel[InstanceToGroup[a]]])
    motifalig[Name][t-1] += a[len(a)-1]

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
      header['positions'][int(colnum)-1] = m.group(1)

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


def alignsequencesandinstancesfromfiles(MotifCorrespondenceFile,SequenceCorrespondenceFile):

  with open(MotifCorrespondenceFile,"r") as f:
    MotifLines = f.readlines()

  print("Read motif correspondence file " + MotifCorrespondenceFile)

  with open(SequenceCorrespondenceFile,"r") as f:
    SequenceLines = f.readlines()

  print("Read sequence correspondence file " + SequenceCorrespondenceFile)

  header, motifalig, sequencealig = alignsequencesandinstancesfromtext(MotifLines,SequenceLines)

  return header, motifalig, sequencealig

if __name__ == "__main__":
#  alignsequencesandinstancesfromfiles(sys.argv[1],sys.argv[2])
#  print(t

  header, motifalig, sequencealig = alignsequencesandinstancesfromfiles(sys.argv[1],sys.argv[2])
  print("Result from alignsequencesandinstancesfromfiles: ")
  print(header)
  print(motifalig)
  print(sequencealig)
