# CorrespondenceReader.py reads a text file listing correspondences between
# 3D motifs, motif groups, JAR3D models, and fasta files

import sys
import os
import re
import string

# python CorrespondenceDiagnostic.py "C:\\Documents and Settings\\zirbel\\My Documents\\My Dropbox\\BGSURNA\\Motifs\\diagnostic\\IL\\0.6\\bp_models\\"

def readcorrespondencesfromtext(text):

  InstanceToGroup = {}          # instance of motif to conserved group position
  InstanceToPDB = {}            # instance of motif to NTs in PDBs
  InstanceToSequence = {}       # instance of motif to position in fasta file
  GroupToModel = {}             # positions in motif group to nodes in JAR3D model
  ModelToColumn = {}            # nodes in JAR3D model to display columns

  SequenceToModel = {}          # sequence position to node in JAR3D model

# I need help on the next line:

  for line in re.finditer("[0-9]{4}",line):
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

  return InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn, SequenceToModel


def readcorrespondencesfromfile(filenamewithpath):

# future plan:
# open file
# read lines into a text string
# pass that text string to readcorrespondencesfromtext
# for now, just keep it this way

    InstanceToGroup = {}          # instance of motif to conserved group position
    InstanceToPDB = {}            # instance of motif to NTs in PDBs
    InstanceToSequence = {}       # instance of motif to position in fasta file
    GroupToModel = {}             # positions in motif group to nodes in JAR3D model
    ModelToColumn = {}            # nodes in JAR3D model to display columns

    SequenceToModel = {}          # sequence position to node in JAR3D model

    text = ""
        
    with open(filenamewithpath,"r") as f:
        for line in f.readlines():
            text = text + line
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

#   InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn, SequenceToModel = readcorrespondencesfromtext(text)

    return InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn, SequenceToModel

def alignmentrows(DisplayColor,aligdata):

  t = ""

  for a in sorted(aligdata.iterkeys()):
    t = t + '<tr><td><font color = "' + DisplayColor[a]+ '">'+a+'</td>'
    for i in range(0,len(aligdata[a])-1):
      t = t + '<td><font color = "' + DisplayColor[a] + '">'+aligdata[a][i]+'</td>'
    t = t + '</tr>\n'
  
  return t

def alignmentheader(ModelToColumn):

  ColumnHeader = [''] * len(ModelToColumn)
  for a in ModelToColumn.iterkeys():
    ColumnHeader[int(ModelToColumn[a])-1] = a

  t = '<tr valign=top><th></th>'
  for i in range(0,len(ModelToColumn)):
    t = t + '<th>'
    t = t + 'C<br>'
    t = t + str(i+1) + '<br>'
    m = re.search("Node_([0-9]+)",ColumnHeader[i])
    a = m.group(1)
    t = t + 'N<br>'
    t = t + a + '<br>'
#    for j in range(0,len(a)):
#      t = t + a[j] + '<br>'
    if re.search("Insertion",ColumnHeader[i]):
      t = t + 'I<br>'
    t = t + '</th>'
  t = t + '</tr>'

  return t

# Use JAR3D to create a file of sequence to model correspondences
# Next, specify a motif correspondence file and a file of sequence to model correspondences

def alignsequencesandinstancesfromfiles(MotifCorrespondenceFile,SequenceCorrespondenceFile):

    InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn, NotSequenceToModel = readcorrespondencesfromfile(MotifCorrespondenceFile)

    NotInstanceToGroup, NotInstanceToPDB, NotInstanceToSequence, NotGroupToModel, NotModelToColumn, SequenceToModel = readcorrespondencesfromfile(SequenceCorrespondenceFile)
    
    DisplayColor = {}
    
    for i in InstanceToPDB.iterkeys():
      a = re.search("(Instance_[0-9]+)",i)
      DisplayColor[a.group(1)] = 'black'            # default display color
      
    for i in SequenceToModel.iterkeys():
      a = re.search("(Sequence_[0-9]+)",i)
      DisplayColor[a.group(1)] = 'black'            # default display color
                
    # Loop through instances from 3D and from the sequence alignment and put in an alignment to display
     
    aligdata = {}                                      # new dictionary
    
    for a in InstanceToGroup.iterkeys():
      m = re.search("(Instance_[0-9]+)",a)
      aligdata[m.group(1)] = []
    
    for a in SequenceToModel.iterkeys():
      m = re.search("(Sequence_[0-9]+)",a)
      aligdata[m.group(1)] = []
      
    for a in aligdata.iterkeys():
      for j in range(0,len(ModelToColumn)):
        aligdata[a].append('')                        # clumsy but effective
                                                      # sorting by key should keep insertions in order
    for a in sorted(InstanceToGroup.iterkeys()):
      m = re.search("(Instance_[0-9]+)",a)
      t = int(ModelToColumn[GroupToModel[InstanceToGroup[a]]])
      aligdata[m.group(1)][t-1] += a[len(a)-1]
    
    for a in sorted(SequenceToModel.iterkeys()):
      m = re.search("(Sequence_[0-9]+)",a)
      t = int(ModelToColumn[SequenceToModel[a]])
      aligdata[m.group(1)][t-1] += a[len(a)-1]

    t = '<table>'
    t = t + alignmentheader(ModelToColumn)+'\n'
    t = t + alignmentrows(DisplayColor,aligdata)
    t = t + '<table>'
  
    return t
      
      
# python CorrespondenceUtilities.py "C:\\Documents and Settings\\zirbel\\My Documents\\My Dropbox\\BGSURNA\\Motifs\\lib\\IL\\0.6\\bp_models\\IL_01239.1_correspondences.txt" "C:\\Documents and Settings\\zirbel\\My Documents\\My Dropbox\\BGSURNA\\Motifs\\diagnostic\\IL\\0.6\\bp_models\\IL_01239.1_diagnostics.txt"      
      
if __name__ == "__main__":
  t = alignsequencesandinstancesfromfiles(sys.argv[1],sys.argv[2])  
  print t
