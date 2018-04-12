#!/usr/bin/env python

"""
Submit matcher jobs on HTCondor.

- add in any directories of NTuples (use absolute path)
- modify settings below (cuts, TDirectories, etc)

Output files will be produced as follows: for ntuples in XXX/DATASET, individual
pairs files will be in XXX/DATASET, whilst the hadded final file will be in
XXX/pairs

Requires the htcondenser package: https://github.com/raggleton/htcondenser

TODO: some fancier way of switching between MC & Data setups?
TODO: remove intermediate files? shouldn't be too hard, just tack extra jobs onto
DAG.
"""


import argparse
import os
import sys
from time import strftime
from distutils.spawn import find_executable
from itertools import izip_longest, chain
import math
import re
import htcondenser as ht
import condorCommon as cc
import logging


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


# List of ntuple directories to run over
NTUPLE_DIRS = [
    # '/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_QCDFlatSpring15BX25HCALFix_26Nov_76X_mcRun2_asymptotic_v5_jetSeed1p5_noJec_v2/QCDFlatSpring15BX25PU10to30HCALFix',
    # '/hdfs/L1JEC/L1JetEnergyCorrections/Stage2_QCDFlatSpring15BX25HCALFix_26Nov_76X_mcRun2_asymptotic_v5_jetSeed1p5_noJec_v2/QCDFlatSpring15BX25PU10to30HCALFix',
    # '/hdfs/user/ra12451/L1JEC/CMSSW_8_0_0_pre5/L1JetEnergyCorrections/Stage2_HF_QCDFlatSpring15BX25HCALFix_10Feb_2dd1043_noJEC_v2/QCDFlatSpring15BX25FlatNoPUHCALFix'
    # '/hdfs/user/ra12451/L1JEC/CMSSW_8_0_0_pre5/L1JetEnergyCorrections/Stage2_HF_QCDFlatSpring15BX25HCALFix_10Feb_2dd1043_noJEC_v2/QCDFlatSpring15BX25PU10to30HCALFix'
    # '/hdfs/user/ra12451/L1JEC/CMSSW_8_0_0_pre5/L1JetEnergyCorrections/Stage2_HF_QCDFlatSpring15BX25HCALFix_16Feb_80X_mcRun2_asymptotic_v1_2779cb0_JEC/QCDFlatSpring15BX25PU10to30HCALFix/',
    # '/hdfs/L1JEC/run260627_SingleMuReReco_HF_L1JEC_2779cb0/SingleMuReReco/'
    # '/hdfs/L1JEC/run260627_SingleMuReReco_HF_noL1JEC_3bf1b93_20Feb_Bristol_v3/SingleMuReReco',
    # '/hdfs/L1JEC/run260627_SingleMuReReco_HF_L1JEC_3bf1b93_20Feb_Bristol_v3/SingleMuReReco',
    # '/hdfs/L1JEC/L1JetEnergyCorrections/Stage2_HF_QCDSpring15_20Feb_3bf1b93_noL1JEC_PFJets_V7PFJEC/QCDFlatSpring15BX25PU10to30HCALFix/'
    # '/hdfs/L1JEC/L1JetEnergyCorrections/Stage2_HF_Fall15_9Mar_integration-v9_NoL1JEC_jst1p5_v2/QCDFlatFall15NoPU',
    # '/hdfs/L1JEC/L1JetEnergyCorrections/Stage2_HF_Fall15_9Mar_integration-v9_L1JEC_jst1p5_v2/QCDFlatFall15NoPU',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst2_RAWONLY/QCDFlatFall15NoPU',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst3_RAWONLY/QCDFlatFall15NoPU',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst4_RAWONLY/QCDFlatFall15NoPU',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst5_RAWONLY_v2/QCDFlatFall15NoPU',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst6_RAWONLY_v2/QCDFlatFall15NoPU',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst2_RAWONLY/QCDFlatFall15PU0to50NzshcalRaw',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst3_RAWONLY/QCDFlatFall15PU0to50NzshcalRaw',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst4_RAWONLY/QCDFlatFall15PU0to50NzshcalRaw',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst5_RAWONLY_v2/QCDFlatFall15PU0to50NzshcalRaw',
    # '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst6_RAWONLY_v2/QCDFlatFall15PU0to50NzshcalRaw',
    # '/hdfs/L1JEC/CMSSW_8_0_7/L1JetEnergyCorrections/QCDFlatFall15PU0to50NzshcalRaw_genEmu_23May_jbntuples/QCDFlatFall15PU0to50NzshcalRaw',
    # '/hdfs/L1JEC/CMSSW_8_0_7/L1JetEnergyCorrections/QCDFlatFall15NoPU_genEmu_23May_jbntuples/QCDFlatFall15NoPU',
    # '/hdfs/L1JEC/CMSSW_8_0_9/QCDFlatFall15PU0to50NzshcalRaw_genEmu_30June2016_809v70_noJEC_893ca/QCDFlatFall15PU0to50NzshcalRaw',
    # '/hdfs/L1JEC/CMSSW_8_0_9/QCDFlatFall15NoPU_genEmu_30June2016_809v70_noJEC_893ca/QCDFlatFall15NoPU',
    # '/hdfs/L1JEC/CMSSW_8_0_9/QCDFlatFall15PU0to50NzshcalRaw_genEmu_15Jul2016_809v70_L1JECinFuncForm0262d_L1JEC4a3a1_v2/QCDFlatFall15PU0to50NzshcalRaw',
    #'/hdfs/L1JEC/CMSSW_9_0_0_pre2/crab_qcdSpring16FlatPU20to70genSimRaw_qcdSpring16_genEmu_21Feb2017_902pre2v91p16_withJEC_6e31c000a39c3/intialNtuples',
    #'/hdfs/L1JEC/CMSSW_9_2_0/crab_qcdSpring17FlatPU0to70genSimRaw_qcdSpring17_genEmu_13Jun2017_920v95p13_withoutJEC_43041fdb/initialNtuples',
    #'/hdfs/L1JEC/CMSSW_9_2_8/crab_qcdSummer17FlatPU28to62genSimRaw_qcdSummer17_genEmu_27Oct2017_928v96p49_noJEC_46c34f99b37a/initialNtuples/',
    '/hdfs/L1JEC/CMSSW_9_2_8/crab_qcdSummer17FlatPU28to62genSimRaw_qcdSummer17_genEmu_03Nov2017_928v96p49_withJEC_79eea6f204/initialNtuples/',
]

# Pick one
SAMPLE = 'MC_L1_Gen'
# SAMPLE = 'MC_L1_PF'
# SAMPLE = 'MC_PF_Gen'
# SAMPLE = 'DATA'

# Choose executable to run - must be located using `which <EXE>`
EXE = 'RunMatcherData'
if SAMPLE.startswith("MC"):
    parts = SAMPLE.split('_')
    if len(parts) != 3:
        raise RuntimeError('SAMPLE set incorrectly')
    EXE = 'RunMatcherStage2%s%s' % (parts[1], parts[2])

# DeltaR(L1, RefJet) for matching (typically a value between 0.2<->0.4)
DELTA_R = 0.25

# Minimum pt cut on reference jets
PT_REF_MIN = 10
# PT_REF_MIN = 30.001

# TDirectory name for the L1 jets
L1_DIR = 'l1UpgradeEmuTree'
if SAMPLE.startswith('MC') and '_PF_' in SAMPLE:
        L1_DIR = 'l1JetRecoTree'  # for PF vs Gen

# TDirectory name for the reference jets
REF_DIR = 'l1JetRecoTree'
if SAMPLE.startswith('MC'):
    if SAMPLE.endswith('Gen'):
        REF_DIR = 'l1GeneratorTree'
    elif SAMPLE.endswith('PF'):
        REF_DIR = 'l1JetRecoTree'
    else:
        raise RuntimeError('Cannot get ref jet dir')

# Cleaning cut to apply to Ref Jets
# If none desired, put '' or None
CLEANING_CUT = None  # MC
# CLEANING_CUT = 'TIGHTLEPVETO'  # DATA

# String to append to output ROOT filename
# Note that the things in {} get formatted out later, see below
# Bit of dodgy magic
# APPEND = 'MP_ak4_ref%sto5000_l10to5000_dr%s' % (str(PT_REF_MIN).replace('.', 'p'), str(DELTA_R).replace('.', 'p'))  # MPjets - MC
# APPEND = 'MP_ak4_ref10to5000_l130to5000_dr%s_httL1Jets_allGenJets_MHT' % (str(DELTA_R).replace('.', 'p'))  # MPjets - MC
APPEND = 'ak4_ref%dto5000_l10to5000_dr%s' % (PT_REF_MIN, str(DELTA_R).replace('.', 'p'))  # Demux jets - data
# APPEND = 'ak4_Gen%dto5000_PF0to5000_dr%s_noCleaning' % (PT_REF_MIN, str(DELTA_R).replace('.', 'p'))  # for PFGen exe
# APPEND = 'MP_ak4_PF%dto5000_l10to5000_dr%s_noCleaning' % (PT_REF_MIN, str(DELTA_R).replace('.', 'p'))  # for L1PF exe

if CLEANING_CUT:
    APPEND += '_clean%s' % CLEANING_CUT

# Directory for logs (should be on /storage)
# Will be created automatically by htcondenser
datestamp = strftime("%d_%b_%y")
LOG_DIR = '/storage/%s/L1JEC/%s/L1JetEnergyCorrections/jobs/pairs/%s' % (os.environ['LOGNAME'], os.environ['CMSSW_VERSION'], datestamp)


def submit_all_matcher_dags(exe, ntuple_dirs, log_dir, append,
                            l1_dir, ref_dir, deltaR, ref_min_pt, cleaning_cut,
                            force_submit):
    """Create and submit DAG checkCalibration jobs for all pairs files.

    Parameters
    ----------
    exe : str
        Name of executable.

    ntuple_dirs : list[str]
        List of directories with L1Ntuples to run over.

    log_dir : str, optional
        Directory for STDOUT/STDERR/LOG files. Should be on /storage.

    append : str, optional
        String to append to filenames to track various settings (e.g. deltaR cut).

    l1_dir : str
        Name of TDirectory in Ntuple that holds L1 jets.

    ref_dir : str
        Name of TDirectory in Ntuple that holds reference jets.

    deltaR : float
        Maximum deltaR(L1, Ref) for a match.

    ref_min_pt : float
        Minimum pT cut on reference jets to be considered for matching.

    cleaning_cut : str
        Cleaning cut to be applied. If '' or None, no cut applied.
        Other options include "TIGHTLEPVETO", "TIGHT", and "LOOSE".
        Also requires events to pass CSC filter & HBHE noise filters.

    force_submit : bool, optional
        If True, forces job submission even if proposed output files
        already exists.
        Oherwise, program quits before submission.
    """
    # Update the matcher script for the worker nodes
    setup_script = 'worker_setup.sh'
    cc.update_setup_script(setup_script, os.environ['CMSSW_VERSION'], os.environ['ROOTSYS'])

    # Update the hadd script for the worker node
    hadd_setup_script = 'cmssw_setup.sh'
    cc.update_hadd_setup_script(hadd_setup_script, os.environ['CMSSW_VERSION'])

    status_files = []

    # Submit a DAG for each pairs file
    for ndir in ntuple_dirs:
        print '>>> Processing', ndir
        sfile = submit_matcher_dag(exe=exe, ntuple_dir=ndir, log_dir=log_dir,
                                   l1_dir=l1_dir, ref_dir=ref_dir,
                                   deltaR=deltaR, ref_min_pt=ref_min_pt,
                                   cleaning_cut=cleaning_cut,
                                   append=append, force_submit=force_submit)
        status_files.append(sfile)

    if status_files:
        print 'All statuses:'
        print 'DAGstatus.py ', ' '.join(status_files)


def submit_matcher_dag(exe, ntuple_dir, log_dir, l1_dir, ref_dir, deltaR, ref_min_pt, cleaning_cut,
                       append, force_submit):
    """Submit one matcher DAG for one directory of ntuples.

    This will run `exe` over all Ntuple files and then hadd the results together.

    Parameters
    ----------
    exe : str
        Name of executable.

    ntuple_dir : str
        Name of directory with L1Ntuples to run over.

    log_dir : str
        Directory for STDOUT/STDERR/LOG files. Should be on /storage.

    append : str
        String to append to filenames to track various settings (e.g. deltaR cut).

    l1_dir : str
        Name of TDirectory in Ntuple that holds L1 jets.

    ref_dir : str
        Name of TDirectory in Ntuple that holds reference jets.

    deltaR : float
        Maximum deltaR(L1, Ref) for a match.

    ref_min_pt : float
        Minimum pT cut on reference jets to be considered for matching.

    force_submit : bool
        If True, forces job submission even if proposed output files
        already exists.
        Oherwise, program quits before submission.
    """
    # DAG for jobs
    stem = 'matcher_%s_%s' % (strftime("%H%M%S"), cc.rand_str(3))
    matcher_dag = ht.DAGMan(filename=os.path.join(log_dir, '%s.dag' % stem),
                            status_file=os.path.join(log_dir, '%s.status' % stem))

    # JobSet for each matching job
    log_stem = 'matcher.$(cluster).$(process)'

    matcher_jobs = ht.JobSet(exe=find_executable(exe),
                             copy_exe=True,
                             filename='submit_matcher.condor',
                             setup_script=None,
                             out_dir=log_dir, out_file=log_stem + '.out',
                             err_dir=log_dir, err_file=log_stem + '.err',
                             log_dir=log_dir, log_file=log_stem + '.log',
                             cpus=1, memory='100MB', disk='100MB',
                             transfer_hdfs_input=False,
                             share_exe_setup=True,
                             hdfs_store=ntuple_dir)

    # For creating filenames later
    fmt_dict = dict()

    # Hold all output filenames
    match_output_files = []

    # Additional files to copy across - JEC, etc
    common_input_files = []

    # Add matcher job for each ntuple file
    for ind, ntuple in enumerate(os.listdir(ntuple_dir)):
        # if ind > 10:
        #     break

        # Skip non-ntuple files
        if not ntuple.endswith('.root') or ntuple.startswith('pairs'):
            continue

        ntuple_abspath = os.path.join(ntuple_dir, ntuple)

        # Construct output name
        ntuple_name = os.path.splitext(ntuple)[0]
        # handle anything up to first underscore (L1Tree, L1Ntuple, ...)
        result = re.match(r'^[a-zA-Z0-9]*_', ntuple_name)
        if result:
            pairs_file = '%s_%s.root' % (ntuple_name.replace(result.group(), 'pairs_'),
                                         append.format(**fmt_dict))
        else:
            pairs_file = 'pairs_%s_%s.root' % (ntuple_name, append.format(**fmt_dict))
        out_file = os.path.join(ntuple_dir, pairs_file)
        match_output_files.append(out_file)

        # Add matching job
        job_args = ['-I', ntuple_abspath, '-O', out_file,
                    '--refDir', ref_dir, '--l1Dir', l1_dir,
                    '--draw 0', '--deltaR', deltaR, '--refMinPt', ref_min_pt]
        if cleaning_cut:
            job_args.extend(['--cleanJets', cleaning_cut])

        input_files = common_input_files + [ntuple_abspath]

        match_job = ht.Job(name='match_%d' % ind,
                           args=job_args,
                           input_files=input_files,
                           output_files=[out_file])

        matcher_jobs.add_job(match_job)
        matcher_dag.add_job(match_job)

    # Construct final filename
    # ---------------------------------------------------------------------
    final_file = 'pairs_%s_%s.root' % (os.path.basename(ntuple_dir.rstrip('/')),
                                       append.format(**fmt_dict))
    final_dir = os.path.join(os.path.dirname(ntuple_dir.rstrip('/')), 'pairs')
    cc.check_create_dir(final_dir, info=True)
    final_file = os.path.join(final_dir, final_file)
    log.info("Final file: %s", final_file)

    # Check if any of the output files already exists - maybe we mucked up?
    # ---------------------------------------------------------------------
    if not force_submit:
        for f in [final_file] + match_output_files:
            if os.path.isfile(f):
                raise RuntimeError('ERROR: output file already exists - not submitting.'
                                   '\nTo bypass, use -f flag. \nFILE: %s' % f)

    # Add in hadding jobs
    # ---------------------------------------------------------------------
    hadd_jobs = add_hadd_jobs(matcher_dag, matcher_jobs.jobs.values(), final_file, log_dir)

    # Add in job to delete individual and intermediate hadd files
    # ---------------------------------------------------------------------
    log_stem = 'matcherRm.$(cluster).$(process)'

    rm_jobs = ht.JobSet(exe='hadoop',
                        copy_exe=False,
                        filename='submit_matcherRm.condor',
                        out_dir=log_dir, out_file=log_stem + '.out',
                        err_dir=log_dir, err_file=log_stem + '.err',
                        log_dir=log_dir, log_file=log_stem + '.log',
                        cpus=1, memory='100MB', disk='10MB',
                        transfer_hdfs_input=False,
                        share_exe_setup=False,
                        hdfs_store=ntuple_dir)

    for i, job in enumerate(chain(matcher_jobs, hadd_jobs[:-1])):
        pairs_file = job.output_files[0]
        rm_job = ht.Job(name='rm%d' % i,
                        args=' fs -rm -skipTrash %s' % pairs_file.replace('/hdfs', ''))
        rm_jobs.add_job(rm_job)
        matcher_dag.add_job(rm_job, requires=hadd_jobs[-1])

    # Submit
    # ---------------------------------------------------------------------
    # matcher_dag.write()
    matcher_dag.submit()
    return matcher_dag.status_file


def add_hadd_jobs(dagman, jobs, final_file, log_dir):
    """Add necessary hadd jobs to DAG. All jobs will be hadded together to make
    `final_file`.

    DAGs can only accept a maximum number of arguments, so we have to split
    up hadd-ing into groups. Therefore we need an intermediate layer of hadd
    jobs, and then finally hadd those intermediate output files

    Parameters
    ----------
    dagman : DAGMan
        DAGMan object to add jobs to.

    jobs : list[Job]
        Collection of Jobs to be hadd-ed together.

    final_file : str
        Final hadd-ed filename.

    Returns
    -------
    JobSet
        JobSet for hadd jobs.
    """
    group_size = 200  # max files per hadding job
    # adjust to avoid hadding 1 file by itself
    if len(jobs) % group_size == 0:
        group_size = 199
    # calculate number of intermediate hadd jobs required
    n_inter_jobs = int(math.ceil(len(jobs) * 1. / group_size))

    log_stem = 'matcherHadd.$(cluster).$(process)'

    hadd_jobs = ht.JobSet(exe='hadd',
                          copy_exe=False,
                          filename='haddBig.condor',
                          setup_script=None,
                          out_dir=log_dir, out_file=log_stem + '.out',
                          err_dir=log_dir, err_file=log_stem + '.err',
                          log_dir=log_dir, log_file=log_stem + '.log',
                          cpus=1, memory='100MB', disk='1GB',
                          transfer_hdfs_input=False,
                          share_exe_setup=True,
                          hdfs_store=os.path.dirname(final_file))

    if n_inter_jobs == 1:
        hadd_input = [j.output_files[0] for j in jobs]
        hadd_args = [final_file] + hadd_input
        hadd_job = ht.Job(name='finalHadd',
                          args=hadd_args,
                          input_files=hadd_input,
                          output_files=[final_file])
        hadd_jobs.add_job(hadd_job)
        dagman.add_job(hadd_job, requires=jobs)
    else:
        # Go through groups of Jobs, make intermediate hadd files in same dir
        # as final file
        intermediate_jobs = []
        for i, job_group in enumerate(grouper(jobs, group_size)):
            # Note, job_group is guaranteed to be length group_size, and is
            # padded with None if there arent' that many entries. So need to
            # filter out NoneType
            job_group = filter(None, job_group)
            hadd_input = [j.output_files[0] for j in job_group]
            inter_file = 'hadd_inter_%d_%s.root' % (i, cc.rand_str(5))
            inter_file = os.path.join(os.path.dirname(final_file), inter_file)
            hadd_args = [inter_file] + hadd_input
            hadd_job = ht.Job(name='interHadd%d' % i,
                              args=hadd_args,
                              input_files=hadd_input,
                              output_files=[inter_file])
            hadd_jobs.add_job(hadd_job)
            dagman.add_job(hadd_job, requires=job_group)
            intermediate_jobs.append(hadd_job)

        # Add final hadd job for intermediate files
        hadd_input = [j.output_files[0] for j in intermediate_jobs]
        hadd_args = [final_file] + hadd_input
        hadd_job = ht.Job(name='finalHadd',
                          args=hadd_args,
                          input_files=hadd_input,
                          output_files=[final_file])
        hadd_jobs.add_job(hadd_job)
        dagman.add_job(hadd_job, requires=intermediate_jobs)

    return hadd_jobs


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks.

    If iterable does not divide by n with modulus 0, then the remaining entries
    in the last iterable of grouper() will be padded with fillvalue.

    Taken from https://docs.python.org/2/library/itertools.html#recipes
    e.g.
    >>> grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    """
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', '-f',
                        help='Force submit - will run jobs even if final file '
                             'with same name already exists.',
                        action='store_true')
    args = parser.parse_args()
    sys.exit(submit_all_matcher_dags(exe=EXE, ntuple_dirs=NTUPLE_DIRS, log_dir=LOG_DIR,
                                     l1_dir=L1_DIR, ref_dir=REF_DIR,
                                     deltaR=DELTA_R, ref_min_pt=PT_REF_MIN,
                                     cleaning_cut=CLEANING_CUT,
                                     append=APPEND, force_submit=args.force))
