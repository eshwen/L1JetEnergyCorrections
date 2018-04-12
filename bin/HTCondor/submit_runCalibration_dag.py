#!/usr/bin/env python

"""
Submit runCalibration jobs on HTCondor.

- add in any pairs files you wish to run over (use absolute path)
- modify settings below (PU bins, append, etc)

Output files will be produced as follows: for pairs file, DATASET/pairs/pairs.root,
the output files will be put in DATASET/output/

Requires the htcondenser package: https://github.com/raggleton/htcondenser
"""


import argparse
import os
import sys
sys.path.append(os.path.dirname(os.getcwd()))  # to import binning.py
import binning
from binning import pairwise
from time import strftime
import htcondenser as ht
import condorCommon as cc
import logging
from itertools import chain


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


# List of pairs files to run over (select one)
PAIRS_FILES = [
# '/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_QCDFlatSpring15BX25HCALFix_26Nov_76X_mcRun2_asymptotic_v5_jetSeed1p5_noJec_v2/pairs/pairs_QCDFlatSpring15BX25PU10to30HCALFix_MP_ak4_ref10to5000_l10to5000_dr0p4.root'
# '/hdfs/user/ra12451/L1JEC/CMSSW_8_0_0_pre5/L1JetEnergyCorrections/Stage2_HF_QCDFlatSpring15BX25HCALFix_10Feb_2dd1043_noJEC_v2/pairs/pairs_QCDFlatSpring15BX25FlatNoPUHCALFix_MP_ak4_ref10to5000_l10to5000_dr0p4.root'
# '/hdfs/user/ra12451/L1JEC/CMSSW_8_0_0_pre5/L1JetEnergyCorrections/Stage2_HF_QCDFlatSpring15BX25HCALFix_10Feb_2dd1043_noJEC_v2/pairs/pairs_QCDFlatSpring15BX25FlatNoPUHCALFix_MP_ak4_ref10to5000_l10to5000_dr0p4.root'
# '/hdfs/user/ra12451/L1JEC/CMSSW_8_0_0_pre5/L1JetEnergyCorrections/Stage2_HF_QCDFlatSpring15BX25HCALFix_12Feb_85a0ccf_noJEC_fixedPUS/pairs/pairs_QCDFlatSpring15BX25PU10to30HCALFix_MP_ak4_ref10to5000_l10to5000_dr0p4.root'
# '/hdfs/L1JEC/run260627_SingleMuReReco_HF_noL1JEC_3bf1b93_20Feb_Bristol_v3/pairs/pairs_SingleMuReReco_ak4_ref10to5000_l10to5000_dr0p4_cleanTIGHTLEPVETO.root',
# '/hdfs/L1JEC/L1JetEnergyCorrections/Stage2_HF_QCDSpring15_20Feb_3bf1b93_noL1JEC_PFJets_V7PFJEC/pairs/pairs_QCDFlatSpring15BX25PU10to30HCALFix_MP_ak4_PF10to5000_l10to5000_dr0p4_noCleaning.root'
# '/hdfs/L1JEC/L1JetEnergyCorrections/Stage2_HF_Fall15_9Mar_integration-v9_NoL1JEC_jst1p5_v2/pairs/pairs_QCDFlatFall15NoPU_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/L1JetEnergyCorrections/Stage2_HF_Fall15_9Mar_integration-v9_NoL1JEC_jst1p5_v2/pairs/pairs_ttHTobbFall15PU30_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst2_RAWONLY/pairs/pairs_QCDFlatFall15NoPU_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst3_RAWONLY/pairs/pairs_QCDFlatFall15NoPU_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst4_RAWONLY/pairs/pairs_QCDFlatFall15NoPU_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst5_RAWONLY_v2/pairs/pairs_QCDFlatFall15NoPU_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst6_RAWONLY_v2/pairs/pairs_QCDFlatFall15NoPU_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst2_RAWONLY/pairs/pairs_QCDFlatFall15PU0to50NzshcalRaw_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst3_RAWONLY/pairs/pairs_QCDFlatFall15PU0to50NzshcalRaw_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst4_RAWONLY/pairs/pairs_QCDFlatFall15PU0to50NzshcalRaw_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst6_RAWONLY_v2/pairs/pairs_QCDFlatFall15PU0to50NzshcalRaw_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_2/L1JetEnergyCorrections/Stage2_HF_QCDFall15_16Mar_int-v14_layer1_noL1JEC_jst5_RAWONLY_v2/pairs/pairs_QCDFlatFall15PU0to50NzshcalRaw_MP_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_7/L1JetEnergyCorrections/QCDFlatFall15PU0to50NzshcalRaw_genEmu_23May_jbntuples/pairs/pairs_QCDFlatFall15PU0to50NzshcalRaw_ak4_ref10to5000_l10to5000_dr0p4.root',
# '/hdfs/L1JEC/CMSSW_8_0_7/L1JetEnergyCorrections/QCDFlatFall15PU0to50NzshcalRaw_genEmu_23May_jbntuples/pairs/pairs_QCDFlatFall15PU0to50NzshcalRaw_ak4_ref10to5000_l10to5000_dr0p25.root',
# '/hdfs/L1JEC/CMSSW_8_0_7/L1JetEnergyCorrections/QCDFlatFall15NoPU_genEmu_23May_jbntuples/pairs/pairs_QCDFlatFall15NoPU_ak4_ref10to5000_l10to5000_dr0p25.root',
# '/hdfs/L1JEC/CMSSW_8_0_9/QCDFlatFall15PU0to50NzshcalRaw_genEmu_30June2016_809v70_noJEC_893ca/pairs/pairs_QCDFlatFall15PU0to50NzshcalRaw_ak4_ref10to5000_l10to5000_dr0p25.root',
# '/hdfs/L1JEC/CMSSW_8_0_9/QCDFlatFall15PU0to50NzshcalRaw_genEmu_15Jul2016_809v70_L1JECinFuncForm0262d_L1JEC4a3a1_v2/pairs/pairs_QCDFlatFall15PU0to50NzshcalRaw_ak4_ref10to5000_l10to5000_dr0p25.root',
# '/hdfs/L1JEC/CMSSW_9_0_0_pre2/crab_qcdSpring16FlatPU20to70genSimRaw_qcdSpring16_genEmu_7Feb2017_902pre2v91p7_noJEC_059f1f/pairs/pairs_initialNtuples_ak4_ref10to5000_l10to5000_dr0p25.root',
# '/hdfs/L1JEC/CMSSW_9_0_0_pre2/crab_qcdSpring16FlatPU20to70genSimRaw_qcdSpring16_genEmu_23Mar2017_900pre2v92p7_noJEC_84d3e271977_joeCopyV3/pairs/pairs_initialNtuples_ak4_ref10to5000_l10to5000_dr0p25.root'
#    '/hdfs/L1JEC/CMSSW_9_2_0/crab_qcdSpring17FlatPU0to70genSimRaw_qcdSpring17_genEmu_13Jun2017_920v95p13_withoutJEC_43041fdb/pairs/pairs_initialNtuples_ak4_ref10to5000_l10to5000_dr0p25.root',
#    '/hdfs/L1JEC/CMSSW_9_2_8/crab_qcdSummer17FlatPU28to62genSimRaw_qcdSummer17_genEmu_27Oct2017_928v96p49_noJEC_46c34f99b37a/pairs/pairs_initialNtuples_ak4_ref10to5000_l10to5000_dr0p25.root',
#    '/hdfs/L1JEC/CMSSW_10_0_3/crab_qcdSpring18FlatPU0to70genSimRaw_qcdSpring18_genEmu_09Apr2018_1003v97p22_noJEC_3ae18f212/pairs/pairs_initialNtuples_ak4_ref10to5000_l10to5000_dr0p25.root',
    '/hdfs/L1JEC/CMSSW_10_0_3/crab_qcdSpring18FlatPU0to70genSimRaw_qcdSpring18_genEmu_10Apr2018_1003v97p22_noJEC_ECALZS_3ae18f212/pairs/pairs_initialNtuples_ak4_ref10to5000_l10to5000_dr0p25.root',
]

# ETA bins
ETA_BINS = binning.eta_bins
etaBinsLabel = binning.eta_bins_label

# Select PU bins to run over
# PU_BINS = None  # None if you don't want to cut on PU (ie no pu data)
PU_BINS = binning.pu_bins
# PU_BINS = binning.pu_bins_lower # run260627 lower PU overall

# String to append to output ROOT filename, depending on PU
# Note that the things in {} get formatted out later, see below
# Bit of dodgy magic
APPEND = etaBinsLabel + "_PU{puMin}to{puMax}" if PU_BINS else etaBinsLabel

# Directory for logs (should be on /storage)
# Will be created automatically by htcondenser
datestamp = strftime("%d_%b_%y")
LOG_DIR = '/storage/%s/L1JEC/%s/L1JetEnergyCorrections/jobs/calib/%s' % (os.environ['LOGNAME'], os.environ['CMSSW_VERSION'], datestamp)


def submit_all_runCalib_dags(pairs_files, log_dir, append, pu_bins, eta_bins, force_submit):
    """Create and submit DAG runCalibration jobs for all pairs files.

    Parameters
    ----------
    pairs_files : list[str], optional
        List of pairs files to process. Must be full path.

    log_dir : str, optional
        Directory for STDOUT/STDERR/LOG files. Should be on /storage.

    append : str, optional
        String to append to filenames to track various settings (e.g. PU bin).

    pu_bins : list[list[int, int]], optional
        List of PU bin edges.

    eta_bins : list[float], optional
        List of eta bin edges, including upper edge of last bin.

    force_submit : bool, optional
        If True, forces job submission even if proposed output files already exists.
        Otherwise, program quits before submission.
    """
    # Update the matcher script for the worker nodes
    setup_script = 'worker_setup.sh'
    cc.update_setup_script(setup_script, os.environ['CMSSW_VERSION'], os.environ['ROOTSYS'])

    # Update the hadd script for the worker node
    hadd_setup_script = 'cmssw_setup.sh'
    cc.update_hadd_setup_script(hadd_setup_script, os.environ['CMSSW_VERSION'])

    # Additional files to copy across - other modules. etc
    common_input_files = ['runCalibration.py', 'binning.py', 'common_utils.py']
    common_input_files = [os.path.join(os.path.dirname(os.getcwd()), f) for f in common_input_files]

    status_files = []

    # Submit a DAG for each pairs file
    for pfile in pairs_files:
        print 'Processing', pfile
        sfile = submit_runCalib_dag(pairs_file=pfile, log_dir=log_dir, append=append,
                                    pu_bins=pu_bins, eta_bins=eta_bins,
                                    common_input_files=common_input_files,
                                    force_submit=force_submit)
        status_files.append(sfile)

    if status_files:
        status_files = list(chain.from_iterable(status_files))  # flatten the list
        print 'All statuses:'
        print 'DAGstatus.py ', ' '.join(status_files)


def submit_runCalib_dag(pairs_file, log_dir, append, pu_bins, eta_bins, common_input_files,
                        force_submit=False):
    """Submit one runCalibration DAG for one pairs file.

    This will run runCalibration over exclusive and inclusive eta bins,
    and then finally hadd the results together.

    Parameters
    ----------
    pairs_files : str, optional
        Pairs file to process. Must be full path.

    log_dir : str, optional
        Directory for STDOUT/STDERR/LOG files. Should be on /storage.

    append : str, optional
        String to append to filenames to track various settings (e.g. PU bin).

    pu_bins : list[list[int, int]], optional
        List of PU bin edges.

    eta_bins : list[float], optional
        List of eta bin edges, including upper edge of last bin.

    force_submit : bool, optional
        If True, forces job submission even if proposed output files
        already exists.
        Oherwise, program quits before submission.

    """
    cc.check_file_exists(pairs_file)

    # Setup output directory for output* files
    # e.g. if pairs file in DATASET/pairs/pairs.root
    # then output goes in DATASET/output/
    out_dir = os.path.dirname(os.path.dirname(pairs_file))
    out_dir = os.path.join(out_dir, 'output')
    cc.check_create_dir(out_dir, info=True)

    # Stem for output filename
    out_stem = os.path.splitext(os.path.basename(pairs_file))[0]
    out_stem = out_stem.replace("pairs_", "output_")

    # Loop over PU bins
    # ---------------------------------------------------------------------
    pu_bins = pu_bins or [[-99, 999]]  # set ridiculous limits if no cut on PU
    status_files = []
    for (pu_min, pu_max) in pu_bins:
        log.info('**** Doing PU bin %g - %g', pu_min, pu_max)

        log_stem = 'runCalib.$(cluster).$(process)'
        runCalib_jobs = ht.JobSet(exe='python',
                                  copy_exe=False,
                                  filename='submit_runCalib.condor',
                                  setup_script='worker_setup.sh',
                                  share_exe_setup=True,
                                  out_dir=log_dir, out_file=log_stem + '.out',
                                  err_dir=log_dir, err_file=log_stem + '.err',
                                  log_dir=log_dir, log_file=log_stem + '.log',
                                  cpus=1, memory='100MB', disk='100MB',
                                  transfer_hdfs_input=False,
                                  common_input_files=common_input_files,
                                  hdfs_store=out_dir)

        # For creating filenames later
        fmt_dict = dict(puMin=pu_min, puMax=pu_max)

        # Hold all output filenames
        calib_output_files = []

        # Add exclusive eta bins to this JobSet
        for ind, (eta_min, eta_max) in enumerate(pairwise(eta_bins)):
            out_file = out_stem + "_%d" % ind + append.format(**fmt_dict) + '.root'
            out_file = os.path.join(out_dir, out_file)
            calib_output_files.append(out_file)

            job_args = ['runCalibration.py', pairs_file, out_file,
                        "--no-genjet-plots", '--stage2',
                        '--no-correction-fit',
                        '--PUmin', pu_min, '--PUmax', pu_max,
                        '--etaInd', ind]

            calib_job = ht.Job(name='calib_%d' % ind,
                               args=job_args,
                               input_files=[pairs_file],
                               output_files=[out_file])

            runCalib_jobs.add_job(calib_job)

        # Add hadd jobs
        # ---------------------------------------------------------------------
        log_stem = 'runCalibHadd.$(cluster).$(process)'

        hadd_jobs = ht.JobSet(exe='hadd',
                              copy_exe=False,
                              share_exe_setup=True,
                              filename='haddSmall.condor',
                              setup_script="cmssw_setup.sh",
                              out_dir=log_dir, out_file=log_stem + '.out',
                              err_dir=log_dir, err_file=log_stem + '.err',
                              log_dir=log_dir, log_file=log_stem + '.log',
                              cpus=1, memory='100MB', disk='20MB',
                              transfer_hdfs_input=False,
                              hdfs_store=out_dir)

        # Construct final hadded file name
        final_file = os.path.join(out_dir, out_stem + append.format(**fmt_dict) + '.root')
        hadd_output = [final_file]
        hadd_args = hadd_output + calib_output_files

        hadder = ht.Job(name='haddRunCalib',
                        args=hadd_args,
                        input_files=calib_output_files,
                        output_files=hadd_output)

        hadd_jobs.add_job(hadder)

        # Add all jobs to DAG, with necessary dependencies
        # ---------------------------------------------------------------------
        stem = 'runCalib_%s_%s' % (strftime("%H%M%S"), cc.rand_str(3))
        calib_dag = ht.DAGMan(filename=os.path.join(log_dir, '%s.dag' % stem),
                              status_file=os.path.join(log_dir, '%s.status' % stem))
        for job in runCalib_jobs:
            calib_dag.add_job(job)

        calib_dag.add_job(hadder, requires=[j for j in runCalib_jobs])

        # Check if any of the output files already exists - maybe we mucked up?
        # ---------------------------------------------------------------------
        if not force_submit:
            for f in [final_file] + calib_output_files:
                if os.path.isfile(f):
                    print 'ERROR: output file already exists - not submitting'
                    print 'FILE:', f
                    return 1

        # calib_dag.write()
        calib_dag.submit()
        status_files.append(calib_dag.status_file)

    print 'For all statuses:'
    print 'DAGstatus.py', ' '.join(status_files)
    return status_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', '-f',
                        help='Force submit - will run jobs even if final file '
                             'with same name already exists.',
                        action='store_true')
    args = parser.parse_args()
    submit_all_runCalib_dags(pairs_files=PAIRS_FILES, log_dir=LOG_DIR, append=APPEND,
                             pu_bins=PU_BINS, eta_bins=ETA_BINS, force_submit=args.force)
