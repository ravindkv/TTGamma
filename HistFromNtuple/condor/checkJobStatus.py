import os
import itertools
from optparse import OptionParser
from HistInputs import *

#----------------------------------------
#INPUT Command Line Arguments 
#----------------------------------------
parser = OptionParser()
parser.add_option("-y", "--year", dest="year", default="2016",type='str',
                     help="Specifyi the year of the data taking" )
parser.add_option("-c", "--channel", dest="channel", default="Mu",type='str',
                     help="Specify which channel Mu or Ele? default is Mu" )
parser.add_option("-d", "--decay", dest="ttbarDecayMode", default="SemiLep",type='str',
                     help="Specify which decay moded of ttbar SemiLep or DiLep? default is SemiLep")
(options, args) = parser.parse_args()
year = options.year
channel = options.channel
decay   = options.ttbarDecayMode


#-----------------------------------------
#Path of the output histrograms
#----------------------------------------
inHistSubDir = "Hists/%s/%s/%s"%(year, decay, channel)
inHistFullDir = "%s/%s"%(condorHistDir, inHistSubDir)
condorLogDir = "%s/Log"%condorHistDir

#----------------------------------------
#Get all submitted jobs
#----------------------------------------
submittedDict = {}
if channel=="Mu": Samples = SampleListMu
else: Samples = SampleListEle
#Create for Base, Signal region
for sample in Samples:
    rootFile = "%s_Base_SR.root"%sample
    arguments = "%s %s %s %s"%(year, decay, channel, sample)
    submittedDict[rootFile] = arguments 

#Create for Base, Control region
for sample, cr in itertools.product(Samples, ControlRegion):
    rootFile = "%s_Base_CR_%s.root"%(sample, cr)
    arguments = "%s %s %s %s %s"%(year, decay, channel, sample, cr)
    submittedDict[rootFile] = arguments

#Create for Syst, Signal region
for sample, syst, level in itertools.product(Samples, Systematics, SystLevel):
    rootFile = "%s_%s%s_SR.root"%(sample, syst, level)
    arguments = "%s %s %s %s %s %s"%(year, decay, channel, sample, syst, level)
    if not sample in ["DataMu", "DataEle", "QCD_DD"]:
        submittedDict[rootFile] = arguments

#Create for Syst, Control region
for sample, syst, level, cr in itertools.product(Samples, Systematics, SystLevel, ControlRegion):
    rootFile = "%s_%s%s_CR_%s.root"%(sample, syst, level, cr)
    arguments = "%s %s %s %s %s %s %s"%(year, decay, channel, sample, syst, level, cr)
    if not sample in ["DataMu", "DataEle", "QCD_DD"]:
        submittedDict[rootFile] = arguments

print "Total submitted jobs: %s"%len(submittedDict.keys())
for key, value in submittedDict.items():
    pass
    #print key
def returnNotMatches(a, b):
    return [[x for x in a if x not in b], [x for x in b if x not in a]]

#----------------------------------------
#Get all finished jobs
#----------------------------------------
finishedList = os.listdir(inHistFullDir)
print "Total finished jobs: %s"%len(finishedList)

#----------------------------------------
#Get all un-finished jobs
#----------------------------------------
print "Unfinished jobs: %s\n"%(len(submittedDict.keys()) - len(finishedList))
unFinishedList = returnNotMatches(finishedList, submittedDict.keys())   
for unFinished in unFinishedList[1]:
    print submittedDict[unFinished]

#----------------------------------------
#Get finished but corrupted jobs
#----------------------------------------
corruptedList = []
for finished in finishedList:
    fullPath = "%s/%s"%(inHistFullDir, finished)
    sizeInBytes = os.path.getsize(fullPath)
    if sizeInBytes < 3000:
        corruptedList.append(finished)

print "\nFinished but corrupted jobs: %s"%len(corruptedList)
for corrupted in corruptedList:
    print corrupted

#----------------------------------------
# Check log fils as well
#----------------------------------------
grepName = "grep -rn nan %s -A 6 -B 2 "%condorLogDir
print "\n Nan/Inf is propgrated for the following jobs\n"
#os.system(grepName)

#----------------------------------------
#Create jdl file to be resubmitted
#----------------------------------------
if not os.path.exists("jdl"):
    os.makedirs("jdl")
condorLogDir = "%s/Log"%(condorHistDir)
common_command = \
'Universe   = vanilla\n\
should_transfer_files = YES\n\
when_to_transfer_output = ON_EXIT\n\
use_x509userproxy = true\n\
Output = %s/log_$(cluster)_$(process).stdout\n\
Error  = %s/log_$(cluster)_$(process).stderr\n\
Log    = %s/log_$(cluster)_$(process).condor\n\n'%(condorLogDir, condorLogDir, condorLogDir)


#----------------------------------------
#Create jdl files
#----------------------------------------
print len(unFinishedList)
print unFinishedList
print len(corruptedList)
if len(unFinishedList) ==0 and len(corruptedList)==0:
    print "Noting to be resubmitted"
else:
    jdlFileName = 'jdl/resubmitJobs_%s%s%s.jdl'%(year, decay, channel)
    localFileName = open('../runFailedJobs_%s%s%s.sh'%(year, decay, channel), 'w')
    jdlFile = open(jdlFileName,'w')
    jdlFile.write('Executable =  remoteRun.sh \n')
    jdlFile.write(common_command)
    for unFinished in unFinishedList[1]:
        run_command =  \
		'arguments  = %s \n\
queue 1\n\n' %(submittedDict[unFinished])
    	jdlFile.write(run_command)
    for corrupted in corruptedList:
        run_command =  \
		'arguments  = %s \n\
queue 1\n\n' %(submittedDict[corrupted])
    	jdlFile.write(run_command)
    print "condor_submit %s"%jdlFileName
    jdlFile.close() 
