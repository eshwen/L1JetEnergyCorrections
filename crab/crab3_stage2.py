"""
Stage2-specific CRAB3 setup for running with MC

Run with 'python crab3_stage2.py'
"""


from L1Trigger.L1JetEnergyCorrections.crab3_cfg import config
import L1Trigger.L1JetEnergyCorrections.mc_samples as samples
from CRABAPI.RawCommand import crabCommand
import httplib
import importlib
import os
import sys


# CMSSW CONFIG TO RUN
PY_CONFIG = '../python/l1NtupleMcMaker2018_RAW2DIGI_v1.py'

# Auto-retrieve jet seed threshold in config
# sys.path.append(os.path.dirname(os.path.abspath(PY_CONFIG)))  # nasty hack cos python packaging stoopid
# cmssw_config = importlib.import_module(os.path.splitext(os.path.basename(PY_CONFIG))[0],)
# jst = cmssw_config.process.caloStage2Params.jetSeedThreshold.value()
# print 'Running with JetSeedThreshold', jst

# CHANGE ME - to make a unique indentifier for each set of jobs
job_append = "qcdSpring18_genEmu_07Apr2018_1010v97p22_noJEC_3ae18f212"
# old example (includes tuning of JST):
# job_append = "Stg2_HF_QCDFall15_RAWONLY_11Mar_dasuUpdatesLayer1_noL1JEC_jst%s" % str(jst).replace('.', 'p')


# CHANGE ME - select dataset(s) keys to run over - see python/mc_samples.py
datasets = ["qcdSpring18FlatPU0to70genSimRaw"]
# old examples (they also include datasets with 0 PU):
# datasets = ["qcdSpring16FlatPU20to70genSimRaw"]  # Fall15, RAW
# old examples (they also include datasets with 0 PU):
# datasets = ["QCDFlatFall15PU0to50NzshcalRawRECO", "QCDFlatFall15NoPURECO"]  # Fall15, RAW + RECO (via useParent)
# datasets = ["QCDFlatFall15PU0to50NzshcalRaw", "QCDFlatFall15NoPU"]  # Fall15, RAW


if __name__ == "__main__":
    # We want to put all the CRAB project directories from the tasks we submit
    # here into one common directory. That's why we need to set this parameter.
    config.General.workArea = 'l1ntuple_' + job_append

    config.JobType.psetName = PY_CONFIG

    # Run through datasets once to check all fine
    for dset in datasets:
        if dset not in samples.samples.keys():
            raise KeyError("Wrong dataset key name:", dset)
        # if not samples.check_dataset_exists(samples.samples[dset].inputDataset):
        #     raise RuntimeError("Dataset cannot be found in DAS: %s" % samples.samples[dset].inputDataset)

    for dset in datasets:
        print dset

        dset_opts = samples.samples[dset]

        # requestName used for dir inside workArea & job name on monitoring page
        config.General.requestName = dset + "_" + job_append
        config.Data.inputDataset = dset_opts.inputDataset
        config.Data.useParent = dset_opts.useParent
        config.Data.unitsPerJob = dset_opts.unitsPerJob
        # config.JobType.inputFiles = ['Fall15_25nsV2_MC.db']

        # to restrict total units run over
        # comment it out to run over all
        if dset_opts.totalUnits > 1:
            config.Data.totalUnits = dset_opts.totalUnits
        else:
            if 0 < dset_opts.totalUnits < 1:
                totalUnits = int(samples.get_number_files(dset_opts.inputDataset))
                config.Data.totalUnits = int(totalUnits * dset_opts.totalUnits)
            else:
                config.Data.totalUnits = dset_opts.totalUnits  # make sure we reset

        print config.Data.totalUnits, "total units"

        try:
            crabCommand('submit', config=config)
        except httplib.HTTPException as e:
            print "Cannot submit dataset %s - are you sure it is right?" % dset
            raise
