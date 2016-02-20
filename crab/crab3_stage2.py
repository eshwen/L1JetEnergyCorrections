"""
Stage2-specific CRAB3 setup for running with MC

Run with 'python crab3_stage2.py'
"""


from L1Trigger.L1JetEnergyCorrections.crab3_cfg import config
import L1Trigger.L1JetEnergyCorrections.mc_samples as samples
from CRABAPI.RawCommand import crabCommand
import httplib


# CHANGE ME - to make a unique indentifier for each set of jobs, e.g v2
job_append = "Stage2_HF_QCDSpring15_20Feb_3bf1b93_noL1JEC_PFJets_V7PFJEC"

# CHANGE ME - select dataset(s) keys to run over - see mc_samples.py
datasets = ["QCDFlatSpring15BX25PU10to30HCALFix", "QCDFlatSpring15BX25FlatNoPUHCALFix"]

# FIX THIS!!!!
reco_datasets = [
'/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISpring15DR74-NhcalZSHFscaleFlat10to30Asympt25ns_MCRUN2_74_V9-v1/GEN-SIM-RECO',
'/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISpring15DR74-NhcalZSHFscaleNoPUAsympt25ns_MCRUN2_74_V9-v1/GEN-SIM-RECO'
]

if __name__ == "__main__":

    # We want to put all the CRAB project directories from the tasks we submit
    # here into one common directory. That's why we need to set this parameter.
    config.General.workArea = 'l1ntuple_' + job_append

    config.JobType.psetName = '../python/SimL1Emulator_Stage2_HF_MC.py'

    # Run through datasets once to check all fine
    for dset in datasets:
        if dset not in samples.samples.keys():
            raise KeyError("Wrong dataset key name:", dset)
        # if not samples.check_dataset_exists(samples.samples[dset].inputDataset):
        #     raise RuntimeError("Dataset cannot be found in DAS: %s" % samples.samples[dset].inputDataset)

    for dset, reco_dset in zip(datasets, reco_datasets):
        dset_opts = samples.samples[dset]
        print dset
        # requestName will be used for name of folder inside workArea,
        # and the name of the jobs on monitoring page
        print len(dset + "_" + job_append)
        config.General.requestName = dset + "_" + job_append
        config.Data.inputDataset = reco_dset
        config.Data.secondaryInputDataset = dset_opts.inputDataset
        config.Data.unitsPerJob = dset_opts.unitsPerJob

        # to restrict total units run over
        # comment it out to run over all
        if dset_opts.totalUnits > 1:
            config.Data.totalUnits = dset_opts.totalUnits
        elif 0 < dset_opts.totalUnits < 1:
            config.Data.totalUnits = int(samples.get_number_files(dset_opts.inputDataset) * dset_opts.totalUnits)
        else:
            config.Data.totalUnits = 10000000000  # make sure we reset

        print config.Data.totalUnits, "total units"

        try:
            crabCommand('submit', config=config)
        except httplib.HTTPException as e:
            print "Cannot submit dataset %s - are you sure it is right?" % dset
            raise
