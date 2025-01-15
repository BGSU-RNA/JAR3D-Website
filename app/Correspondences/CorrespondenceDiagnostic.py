# CorrespondenceReader.py reads a text file listing correspondences between
# 3D motifs, motif groups, JAR3D models, and fasta files

import sys
import os
import re
import string

from CorrespondenceUtilities import readcorrespondencesfromfile
from CorrespondenceUtilities import alignmentrows
from CorrespondenceUtilities import alignmentheader

# python CorrespondenceDiagnostic.py "C:\\Documents and Settings\\zirbel\\My Documents\\My Dropbox\\BGSURNA\\Motifs\\diagnostic\\IL\\0.6\\bp_models\\"

def onemodeldiagnostic(directory,MN,prev,next):

  n = 1
  if n > 0:

    FN = directory + "\\" + MN + "_diagnostics.txt"

    InstanceToGroup, InstanceToPDB, InstanceToSequence, GroupToModel, ModelToColumn, SequenceToModel = readcorrespondencesfromfile(FN)

    DisplayColor = {}

    for i in InstanceToPDB.iterkeys():
      a = re.search("(Instance_[0-9]+)",i)
      DisplayColor[a.group(1)] = 'black'            # default display color

    for i in SequenceToModel.iterkeys():
      a = re.search("(Sequence_[0-9]+)",i)
      DisplayColor[a.group(1)] = 'black'            # default display color

    MisAlign = 0

    for nt in sorted(InstanceToPDB.iterkeys()):
      if GroupToModel[InstanceToGroup[nt]] != SequenceToModel[InstanceToSequence[nt]]:
        print(nt + ' belongs to ' + GroupToModel[InstanceToGroup[nt]] + ' but was aligned to ' + SequenceToModel[InstanceToSequence[nt]])
        MisAlign += 0.5
        a = re.search("(Instance_[0-9]+)",nt)
        DisplayColor[a.group(1)] = 'red'
        a = re.search("(Sequence_[0-9]+)",InstanceToSequence[nt])
        DisplayColor[a.group(1)] = 'red'

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
        aligdata[a].append('')
                                                      # sorting by key should keep insertions in order
    for a in sorted(InstanceToGroup.iterkeys()):
      m = re.search("(Instance_[0-9]+)",a)
      t = int(ModelToColumn[GroupToModel[InstanceToGroup[a]]])
      aligdata[m.group(1)][t-1] += a[len(a)-1]

    for a in sorted(SequenceToModel.iterkeys()):
      m = re.search("(Sequence_[0-9]+)",a)
      t = int(ModelToColumn[SequenceToModel[a]])
      aligdata[m.group(1)][t-1] += a[len(a)-1]

    #for a,b in aligdata.iteritems():
    #  for i in range(0,len(b)-1):
    #    print('<td>'+aligdata[a][i]+'</td>'),
    #  print

    f = open(directory+MN+"_diagnostics.html","w")
    f.write("<html>"+MN+" alignment\n")
    f.write("<a href=\"" + prev + "\">Previous</a>   ")
    f.write("<a href=\"" + next + "\">Next</a>   ")
    f.write("<a href=\"http://rna.bgsu.edu/rna3dhub/motif/view/" + MN + "\">Motif atlas entry</a>  ")
    f.write("<table>")
    f.write(alignmentheader(ModelToColumn)+'\n')
    f.write(alignmentrows(DisplayColor,aligdata))
    f.write("</table>")

    libDirectory = re.sub('diagnostic','lib',directory)
    ModelFile = libDirectory + "\\" + MN + "_model.txt"

    f.write('<pre>')
    with open(ModelFile,"r") as mf:
        for line in mf.readlines():
          f.write(line)

    f.write("</html>")
    f.close()

    print("Wrote html file with alignment of 3D instances and sequences for " + MN)

    return aligdata, MisAlign

def allmodelsdiagnostic(directory):

  print("Starting all models diagnostic")
  dirList = sorted(os.listdir(directory))
#  print(dirList)

  libDirectory = re.sub('diagnostic','lib',directory)
  interDirectory = re.sub('bp_models','interactions',libDirectory)

  # iterate through files, call onemodeldiagnostic(MN,path)

  prev = ""

  tf = open(directory+"misalignment.html","w")
  tf.write("<html><body><h1>Mis-alignments between the motif group and JAR3D</h1>")
  for i in range(0,len(dirList)):
    fn = dirList[i]
    if re.search("diagnostics.txt",fn):
      next = dirList[min(i+1,len(dirList)-1)]
      next = re.sub('.txt','.html',next)
      print("Starting a new model")
      print(prev + " " + fn + " " + next)
      m = re.search("(.*)(_diagnostics)(.*)",fn)

      InteractionFile = interDirectory + m.group(1) + ".txt"
      with open(InteractionFile,"r") as intf:
        for line in intf.readlines():
          print(line),

      dfn = directory+re.sub('.txt','.html',fn)
      aligdata, MisAlign = onemodeldiagnostic(directory,m.group(1),prev,next)
      if MisAlign > 0:
        tf.write("<a href=\"" + dfn + "\">" + m.group(1) + "</a> had " + str(MisAlign) + " misalignments<br>")

      prev = fn
      prev = re.sub('.txt','.html',prev)

  tf.close()

  return dirList

if __name__ == "__main__":
  allmodelsdiagnostic(sys.argv[1])
