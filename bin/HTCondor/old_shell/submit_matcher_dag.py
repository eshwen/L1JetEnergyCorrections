#!/usr/bin/env python

"""
Submit matcher jobs on HTCondor using the DAGman feature.
- add in the relevant directories of L1Ntuple files you
wish to run over. Use absolute path!
- modify any matcher program settings

A pairs file will be created for each L1Ntuple file, in the same directory as
the L1Ntuple file. The pairs files will then be hadded and placed in a special
"pairs" directory, in the parent directory of the L1Ntuple files.
"""


import os
from subprocess import call
import re
from time import strftime
from distutils.spawn import find_executable
import shutil
import random
import string
import math
from itertools import izip_longest


# SETTINGS THE USER SHOULD CHANGE
# -----------------------------------------------------------------------------
# Locations of directories with L1Ntuple files to run over:
NTUPLE_DIRS = [
    # '/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_QCDFlatSpring15BX25HCALFix_22Nov_76X_mcRun2_asymptotic_v5_jetSeed1p5_noJec_v2/QCDFlatSpring15BX25PU10to30HCALFix',
    # '/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_QCDFlatSpring15BX25HCALFix_22Nov_76X_mcRun2_asymptotic_v5_jetSeed1p5_noJec_v2/QCDFlatSpring15BX25FlatNoPUHCALFix'
    # '/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_QCDFlatSpring15BX25HCALFix_26Nov_76X_mcRun2_asymptotic_v5_jetSeed1p5_jec22Nov/QCDFlatSpring15BX25PU10to30HCALFix'
    '/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_QCDFlatSpring15BX25HCALFix_26Nov_76X_mcRun2_asymptotic_v5_jetSeed1p5_noJec_v2/QCDFlatSpring15BX25PU10to30HCALFix',
    # '/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_Run260627/ntuples'
    # '/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_Run260627/Express'
    # '/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_Run2015D_260627_31Dec_760pre7_noJEC_HBHEnoise_v2/Express'
]

# Choose executable to run - must be located using `which <EXE>`
EXE = 'RunMatcherStage2'  # For Stage 2 MC
# EXE = 'RunMatcherData'  # For Stage 2 DATA

# DeltaR(L1, RefJet) for matching
DELTA_R = 0.4

# Minimum pt cut on reference jets
PT_REF_MIN = 10

# TDirectory name for the L1 jets
L1_DIR = 'l1UpgradeSimTreeMP'
# L1_DIR = 'l1UpgradeEmuTree'

# TDirectory name for the reference jets
REF_DIR = 'l1ExtraTreeGenAk4'
# REF_DIR = 'l1JetRecoTree'

# Output filename append string.
# The output filename is constructed as follows: for an input file named
# "L1Tree_ABCDEFG_HIJKL_21.root", the output will be
# "pairs_ABCDEFG_HIJKL_21_{append}.root", where {append} is defined here.
# The hadded pairs file will be named "pairs_ABCDEFG_HIJKL_{append}.root"
# (i.e. remove any index number at the end)
# Note that any decimal points in
# numbers will be converted to "p", e.g. 0.4 => 0p4
APPEND = 'MP_ak4_ref%dto5000_l10to5000_dr%s_testCalibratePU15to25_2048bins_maxCorr6' % (PT_REF_MIN, str(DELTA_R).replace('.', 'p'))
# APPEND = 'MP_ak4_ref%dto5000_l10to5000_dr%s_testCalibratePU15to25_mergeCrit1p01_maxCorr6' % (PT_REF_MIN, str(DELTA_R).replace('.', 'p'))
# APPEND = 'data_ref%dto5000_l10to5000_dr%s_noCleaning_fixedEF_CSCfilter_HBHENoise' % (PT_REF_MIN, str(DELTA_R).replace('.', 'p'))
# APPEND = 'data_ref%dto5000_l10to5000_dr%s_tightLepVeto' % (PT_REF_MIN, str(DELTA_R).replace('.', 'p'))

LOG_DIR = '/storage/%s/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/jobs/matcher/%s' % (os.environ['LOGNAME'], strftime("%d_%b_%y"))


# DO NOT EDIT BELOW HERE
# -----------------------------------------------------------------------------
def submit_matcher_dag(exe=EXE, ntuple_dirs=NTUPLE_DIRS, append_str=APPEND,
                       l1_dir=L1_DIR, ref_dir=REF_DIR,
                       deltaR=DELTA_R, ref_min_pt=PT_REF_MIN,
                       log_dir=LOG_DIR, force_submit=True):
    """Make DAG. Submit DAG."""
    # Before looping through the ntuple directories, we setup certain variables
    # and scripts as they only need to be done once

    # Update the matcher script for the worker nodes
    worker_script = 'condor_worker.sh'
    update_worker_script(worker_script,
                         os.environ['CMSSW_VERSION'],
                         os.environ['ROOTSYS'])

    # Update the hadd script for the worker node
    hadd_script = 'hadd.sh'
    update_hadd_script(hadd_script, os.environ['CMSSW_VERSION'])

    # Make a matcher condor job description file using the generic template
    # datestamp = strftime("%d_%b_%y")
    job_file = 'submit_matcher.condor'
    exe_path = find_executable(exe)
    if not exe_path:
        raise RuntimeError('Cannot find path for %s' % exe)
    # log_dir = 'jobs/matcher/%s' % datestamp
    # log_dir = '/storage/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/jobs/matcher/%s' % datestamp
    check_create_dir(log_dir)
    check_create_dir('jobs/hadd')  # for Hadd jobs
    create_condor_description(template_file='submit_template.condor',
                              job_file=job_file,
                              log_dir=log_dir,
                              exe_path=exe_path)

    # Create a DAG & submit for each set of NTuples
    # -------------------------------------------------------------------------
    status_files = []
    for tree_dir in ntuple_dirs:
        print '>>> Making jobs for', tree_dir

        # Copy executable to that directory for use later
        exe_path_hdfs = os.path.join(tree_dir, EXE)
        cmds = 'hadoop fs -copyFromLocal -f %s %s' % (exe_path, exe_path_hdfs.replace("/hdfs", ""))
        call(cmds.split())

        # Create unique DAG filename for this directory
        timestamp = strftime('%H%M%S')
        dag_file = 'pairs_%s_%s.dag' % (timestamp, rand_str())

        # Corresponding status filename
        status_file = dag_file.replace('.dag', '.status')
        status_files.append(status_file)

        job_names = []
        out_filenames = []

        # location of final hadded file
        hadd_dir = os.path.join(os.path.dirname(tree_dir.rstrip('/')), 'pairs')
        check_create_dir(hadd_dir, True)

        # final filepath
        final_file = ''

        # Add a matcher job for each file
        with open(dag_file, 'w') as dag:
            print 'Making DAG file', dag_file

            for ind, ntuple in enumerate(os.listdir(tree_dir)):
                if not ntuple.endswith(".root") or ntuple.startswith('pairs'):
                    # print "Skipping", ntuple
                    continue
                # if not ntuple == 'L1Tree_Data_260627_noL1JEC_HBHENoise.root':
                    # continue

                ntuple_name = os.path.splitext(os.path.basename(ntuple))[0]
                pairs_file = '%s_%s.root' % (ntuple_name.replace('L1Tree_', 'pairs_'),
                                             append_str)
                if not pairs_file.startswith('pairs'):
                    pairs_file = 'pairs_%s' % pairs_file

                out_file = os.path.join(tree_dir, pairs_file)
                out_filenames.append(out_file)

                index = ind
                finder = re.findall(r'_\d*$', ntuple_name)
                if finder:
                    index = finder[0]
                job_name = 'pairs%s' % index
                job_names.append(job_name)
                job_dict = dict(jobName=job_name, jobFile=job_file,
                                input=os.path.join(tree_dir, ntuple),
                                output=out_file,
                                exe=exe_path_hdfs,
                                l1Dir=l1_dir,
                                refDir=ref_dir,
                                deltaR=deltaR,
                                refMinPt=ref_min_pt)
                dag.write('JOB {jobName} {jobFile}\n'.format(**job_dict))
                dag.write('VARS {jobName} opts="{input} {output} {exe} '
                          '-I {input} -O {output} '
                          '--refDir {refDir} --l1Dir {l1Dir} '
                          '--draw 0 --deltaR {deltaR} '
                          '--refMinPt {refMinPt} --correct dummy"\n'.format(**job_dict))

            # Add jobs for hadd-ing
            # Create final filename - use dataset dir and append string
            final_file = 'pairs_%s_%s.root' % (os.path.basename(tree_dir.rstrip('/')), append_str)
            print final_file
            final_file = os.path.join(hadd_dir, final_file)

            hadd_dict = {k: v for k, v in zip(job_names, out_filenames)}
            # print hadd_dict
            dag.write(hadd_jobs_str(hadd_dict, hadd_dir, final_file))

            # Add status file output
            dag.write('NODE_STATUS_FILE %s 30\n' % status_file)

        # Submit, but check if it will overwrite anything
        # ---------------------------------------------------------------------
        if os.path.isfile(final_file) and not force_submit:
            print 'Cannot submit jobs - final file already exists.'
        else:
            print 'Submitting jobs'
            call(['condor_submit_dag', dag_file])
            print 'Check status with:'
            print 'DAGstatus.py', status_file
            print ''

    if len(status_files) > 1:
        print 'To check all statuses:'
        print 'DAGstatus.py %s' % ' '.join(status_files)


def update_worker_script(worker_script, cmssw_ver, root_dir):
    """Update condor worker script with correct CMSSW version and ROOT dir.

    worker_script: str
        Filename for condor worker script
    cmssw_ver: str
        CMSSW version
    root_dir: str
        Directory for ROOT. Must contain bin/thisroot.sh
    """
    sed_cmds = ['sed -i s/VER=CMSSW_.*/VER=%s/ %s' % (cmssw_ver, worker_script),
                'sed -i s@RDIR=/.*@RDIR=%s@ %s' % (root_dir, worker_script)]
    for cmd in sed_cmds:
        call(cmd.split())


def update_hadd_script(hadd_script, cmssw_ver):
    """Update condor worker script with correct CMSSW version and ROOT dir.

    hadd_script: str
        Filename for condor worker script
    cmssw_ver: str
        CMSSW version
    """
    sed_cmd = 'sed -i s/VER=CMSSW_.*/VER=%s/ %s' % (cmssw_ver, hadd_script)
    call(sed_cmd.split())


def create_condor_description(template_file, job_file, log_dir, exe_path):
    """Create a condor job description for matcher jobs.

    template_file: str
        File to use as job description template
    job_file: str
        File to write new condor job description.
    log_dir: str
        Directory to store STDOUT/ERR/log files
    exe_path: str
        Script/executable to run on worker node.
    """
    with open(template_file) as t:
        template = t.read()

    template += 'arguments = $(opts)\nqueue'

    template = template.replace("SEDNAME", os.path.join(log_dir, 'matcher'))
    template = template.replace("SEDEXE", 'condor_worker.sh')
    template = template.replace("SEDINPUTFILES", '')

    with open(job_file, 'w') as j:
        j.write(template)


def check_create_dir(directory, info=False):
    """Check dir exists, if not create"""
    if not os.path.isdir(directory):
        if os.path.isfile(directory):
            raise RuntimeError('%s already exists as a file' % directory)
        os.makedirs(directory)
        if info:
            print 'Making dir', directory


def hadd_jobs_str(job_dict, hadd_dir, final_file):
    """
    job_dict: dict[str: str]
        Dict of jobName:fileName, must be absolute path.
    hadd_dir: str
        Final directory for hadded files (and intermediates)
    """

    group_size = 200  # max files per hadding job
    # adjust to avoid hadding 1 file by itself
    n_jobs = len(job_dict.keys())
    if n_jobs % group_size == 0:
        group_size = 199
    n_inter_jobs = int(math.ceil(n_jobs * 1. / group_size))

    hadd_str = ''

    if n_inter_jobs == 1:
        hadd_str += 'JOB haddFinal hadd_big.condor\n'
        hadd_str += 'VARS haddFinal opts="%s %s"\n' % (final_file, ' '.join(job_dict.values()))
        hadd_str += 'PARENT %s CHILD haddFinal\n' % (' '.join(job_dict.keys()))
    else:
        # Do a layer of intermediate jobs first
        inter_job_dict = {}
        for ind, (jobnames, jobfiles) in enumerate(zip(grouper(job_dict.keys(), group_size),
                                                       grouper(job_dict.values(), group_size))):
            jobnames = filter(lambda x: x, jobnames)
            jobfiles = filter(lambda x: x, jobfiles)
            # create an intermediate filename & jobname
            inter_filename = 'hadd_inter_%d_%s.root' % (ind, rand_str(5))
            inter_jobname = 'hadd_inter_%d' % (ind)
            inter_filename = os.path.join(os.path.dirname(final_file), inter_filename)
            inter_job_dict[inter_jobname] = inter_filename

            hadd_str += 'JOB %s hadd_big.condor\n' % (inter_jobname)
            hadd_str += 'VARS %s opts="%s %s"\n' % (inter_jobname, inter_filename, ' '.join(jobfiles))
            hadd_str += 'PARENT %s CHILD %s\n' % (' '.join(jobnames), inter_jobname)

        # Add in the final hadd job to hadd the results of the intermediate jobs
        hadd_str += 'JOB haddFinal hadd_big.condor\n'
        hadd_str += 'VARS haddFinal opts="%s %s"\n' % (final_file, ' '.join(inter_job_dict.values()))
        hadd_str += 'PARENT %s CHILD haddFinal\n' % (' '.join(inter_job_dict.keys()))

    return hadd_str


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks

    Taken from https://docs.python.org/2/library/itertools.html#recipes
    """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def rand_str(length=3):
    """Generate a random string of user-specified length"""
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase)
                   for _ in range(length))


if __name__ == '__main__':
    submit_matcher_dag()
