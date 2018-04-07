"""
MC samples to be used in CRAB3 configs

For each sample, we have a simple Dataset namedtuple. Fields are inputDataset,
unitsPerJob, and totalUnits. (see CRAB documentationf or meaning).
We then store all samples in a dict.

Usage:

from mc_samples import samples
dataset = "TTbarFall13PU20bx25"
config.General.requestName = dataset
config.Data.inputDataset = samples[dataset].inputDataset
config.Data.unitsPerJob = samples[dataset].unitsPerJob
config.Data.useParent = samples[dataset].useParent

totalUnits can take the values:
-1: run over all files in the dataset
0 - 1: run over this fraction of the dataset
>1: run over this many files

You can use get_number_files() to ask DAS how many files there are in a dataset.
"""


from collections import namedtuple
import re
import subprocess
import json
import os


# some helper functions
def get_number_files(dataset):
    """Get total number of files in dataset"""
    HOME = os.environ['HOME']
    # cmds = ['das_client.py', '--query', 'summary dataset=%s' % dataset, '--format=json',
    #         '--key=%s/.globus/userkey.pem' % HOME, '--cert=%s/.globus/usercert.pem' % HOME]
    cmds = ['das_client.py', '--query', 'summary dataset=%s' % dataset, '--format=json']
    output = subprocess.check_output(cmds, stderr=subprocess.STDOUT)
    summary_dict = json.loads(output)
    return int(summary_dict['data'][0]['summary'][0]['nfiles'])


def check_dataset_exists(dataset):
    """Check dataset exists in DAS"""
    result = subprocess.call(['das_client.py', '--query', 'dataset dataset=%s' % dataset])
    return result == 0


# handy data structure to store some attributes for each dataset
Dataset = namedtuple("Dataset", "inputDataset unitsPerJob totalUnits useParent")

# This dict holds ALL samples
samples = {
    # SPRING 18/100X
    # --------------
    "qcdSpring18FlatPU0to70genSimRaw": Dataset(inputDataset="/QCD_Pt-15to3000_TuneCP5_Flat_13TeV_pythia8/RunIISpring18DRNZSPU0to70_100X_upgrade2018_realistic_v10-v1/GEN-SIM-RAW",
                           useParent=False, unitsPerJob=10, totalUnits=-1),
    # SUMMER 17/92X
    # -------------
    "qcdSummer17FlatPU28to62genSimRaw":	Dataset(inputDataset="/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISummer17DRStdmix-NZSFlatPU28to62_92X_upgrade2017_realistic_v10-v1/GEN-SIM-RAW",
                    useParent=False, unitsPerJob=10, totalUnits=-1), # 9.9M events, 2k evt/file
    # SPRING 17/90X
    # -------------
    "qcdSpring17FlatPU0to70genSimRaw": Dataset(inputDataset="/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/PhaseISpring17DR-FlatPU0to70NZS_90X_upgrade2017_realistic_v20-v1/GEN-SIM-RAW",
                    useParent=False, unitsPerJob=10, totalUnits=-1), # 9.9M events, 2K evt/file
    # SPRING 16/80X
    # -------------
    "qcdSpring16FlatPU20to70genSimRaw": Dataset(inputDataset="/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISpring16DR80-FlatPU20to70HcalNZSRAW_withHLT_80X_mcRun2_asymptotic_v14-v1/GEN-SIM-RAW",
                                              useParent=False, unitsPerJob=10, totalUnits=-1),  # has about 10M events, 1.7K evt/file

    # FALL 15/76X
    # -----------
    # note there are also individual PU bins at PU = [10, 20, 30, 40, 50]
    "SingleNeutrinoFall15PU0to50NzshcalRaw": Dataset(inputDataset='/SingleNeutrino/RunIIFall15DR76-25nsFlat0to50NzshcalRaw_76X_mcRun2_asymptotic_v12-v1/GEN-SIM-RAW',
                                                     useParent=False, unitsPerJob=3, totalUnits=-1),  # 20M events, 5.6K evt/file

    "SingleNeutrinoFall15PU0to50NzshcalRawRECO": Dataset(inputDataset='/SingleNeutrino/RunIIFall15DR76-25nsFlat0to50NzshcalRaw_76X_mcRun2_asymptotic_v12-v1/GEN-SIM-RAW',
                                                         useParent=True, unitsPerJob=1, totalUnits=-1),  # 20M events, 11.2K evt/file

    "ttHTobbFall15PU30": Dataset(inputDataset="/ttHTobb_M125_13TeV_powheg_pythia8/RunIIFall15DR76-25nsPUfixed30NzshcalRaw_76X_mcRun2_asymptotic_v12-v1/GEN-SIM-RAW",
                                 useParent=False, unitsPerJob=10, totalUnits=-1),  # 120K evt, 2K evt/file

    "ttHTobbFall15PU30RECO": Dataset(inputDataset="/ttHTobb_M125_13TeV_powheg_pythia8/RunIIFall15DR76-25nsPUfixed30NzshcalRaw_76X_mcRun2_asymptotic_v12-v1/AODSIM",
                                     useParent=True, unitsPerJob=1, totalUnits=-1),  # 120K evt, 7k evt/file

    "QCDFlatFall15PU0to50NzshcalRaw": Dataset(inputDataset="/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIIFall15DR76-25nsFlat0to50NzshcalRaw_76X_mcRun2_asymptotic_v12-v1/GEN-SIM-RAW",
                                              useParent=False, unitsPerJob=10, totalUnits=-1),  # has about 9M events, 2K evt/file

    "QCDFlatFall15PU0to50NzshcalRawRECO": Dataset(inputDataset="/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIIFall15DR76-25nsFlat0to50NzshcalRaw_76X_mcRun2_asymptotic_v12-v1/AODSIM",
                                                  useParent=True, unitsPerJob=1, totalUnits=-1),  # has about 9M events, 9k evt/file

    "QCDFlatFall15NoPU": Dataset(inputDataset="/QCD_Pt-15to7000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIIFall15DR76-25nsNoPURaw_magnetOn_76X_mcRun2_asymptotic_v12-v1/GEN-SIM-RAW",
                                 useParent=False, unitsPerJob=10, totalUnits=-1),  # has about 9M events, 2K evt/file

    "QCDFlatFall15NoPURECO": Dataset(inputDataset="/QCD_Pt-15to7000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIIFall15DR76-25nsNoPURaw_magnetOn_76X_mcRun2_asymptotic_v12-v1/AODSIM",
                                     useParent=True, unitsPerJob=1, totalUnits=-1),  # has about 9M events, 9K evt/file

    # SPRING 15/74X
    # -------------
    "QCDFlatSpring15BX25PU10to30HCALFix": Dataset(inputDataset='/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISpring15DR74-NhcalZSHFscaleFlat10to30Asympt25ns_MCRUN2_74_V9-v1/GEN-SIM-RAW',
                                                  useParent=False, unitsPerJob=10, totalUnits=-1),

    # RECO
    "QCDFlatSpring15BX25PU10to30HCALFixRECO": Dataset(inputDataset='/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISpring15DR74-NhcalZSHFscaleFlat10to30Asympt25ns_MCRUN2_74_V9-v1/GEN-SIM-RECO',
                                                      useParent=True, unitsPerJob=10, totalUnits=0.3),

    "QCDFlatSpring15BX25FlatNoPUHCALFix": Dataset(inputDataset='/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISpring15DR74-NhcalZSHFscaleNoPUAsympt25ns_MCRUN2_74_V9-v1/GEN-SIM-RAW',
                                                  useParent=False, unitsPerJob=10, totalUnits=-1),

    # RECO
    "QCDFlatSpring15BX25FlatNoPUHCALFixRECO": Dataset(inputDataset='/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISpring15DR74-NhcalZSHFscaleNoPUAsympt25ns_MCRUN2_74_V9-v1/GEN-SIM-RECO',
                                                      useParent=True, unitsPerJob=10, totalUnits=0.3),

    "TTbarSpring15AVE30BX50": Dataset(inputDataset='/TTJets_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/RunIISpring15Digi74-AVE_30_BX_50ns_tsg_MCRUN2_74_V6-v1/GEN-SIM-RAW',
                                      useParent=False, unitsPerJob=25, totalUnits=-1),

    "QCDFlatSpring15BX50": Dataset(inputDataset='/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISpring15Digi74-Flat_10_50_50ns_tsg_MCRUN2_74_V6-v1/GEN-SIM-RAW',
                                   useParent=False, unitsPerJob=50, totalUnits=-1),

    "QCDFlatSpring15BX25": Dataset(inputDataset='/QCD_Pt-15to3000_TuneCUETP8M1_Flat_13TeV_pythia8/RunIISpring15Digi74-Flat_10_50_25ns_tsg_MCRUN2_74_V7-v1/GEN-SIM-RAW',
                                   useParent=False, unitsPerJob=10, totalUnits=-1),

    "SingleNeutrinoSpring15AVE30BX50": Dataset(inputDataset='/SingleNeutrino/RunIISpring15Digi74-AVE_30_BX_50ns_tsg_MCRUN2_74_V6-v1/GEN-SIM-RAW',
                                               useParent=False, unitsPerJob=50, totalUnits=600),

    "SingleNeutrinoSpring15Flat10to50BX50": Dataset(inputDataset='/SingleNeutrino/RunIISpring15Digi74-Flat_10_50_50ns_tsg_MCRUN2_74_V6-v1/GEN-SIM-RAW',
                                                    useParent=False, unitsPerJob=50, totalUnits=600),

    # PHYS 14
    # -------
    "TTbarPhys14AVE30BX50": Dataset(inputDataset='/TT_Tune4C_13TeV-pythia8-tauola/Phys14DR-AVE30BX50_tsg_PHYS14_ST_V1-v1/GEN-SIM-RAW',
                                    useParent=False, unitsPerJob=25, totalUnits=600),

    "QCDFlatPhys14BX50": Dataset(inputDataset='/QCD_Pt-15to3000_Tune4C_Flat_13TeV_pythia8/Phys14DR-Flat20to50BX50_tsg_PHYS14_ST_V1-v2/GEN-SIM-RAW',
                                 useParent=False, unitsPerJob=50, totalUnits=-1),

    "NeutrinoGunPhys14BX50": Dataset(inputDataset='/Neutrino_Pt-2to20_gun/Phys14DR-AVE30BX50_tsg_PHYS14_ST_V1-v1/GEN-SIM-RAW',
                                     useParent=False, unitsPerJob=35, totalUnits=560),

    "QCDFlatSpring14": Dataset(inputDataset='/QCD_Pt-15to3000_Tune4C_Flat_13TeV_pythia8/Spring14dr-Flat20to50_POSTLS170_V5-v1/GEN-SIM-RAW',
                               useParent=False, unitsPerJob=50, totalUnits=-1),

    "TTbarFall13PU20bx25": Dataset(inputDataset='/TT_Tune4C_13TeV-pythia8-tauola/Fall13dr-tsg_PU20bx25_POSTLS162_V2-v1/GEN-SIM-RAW',
                                   useParent=False, unitsPerJob=100, totalUnits=-1),

}

# Add in QCD pt binned samples here easily
ptbins = [15, 30, 50, 80, 120, 170, 300, 470, 600, 800, 1000]
for i, ptmin in enumerate(ptbins[:-1]):
    ptmax = ptbins[i + 1]

    # Spring15 AVEPU20 25ns
    key = "QCD_Pt-%dto%d_Spring15_AVE20BX25" % (ptmin, ptmax)
    ver = "-v1"
    tot = -1
    if ptmin == 80:
        ver = "-v2"
    elif ptmin == 15:
        ver = "_ext1-v1"
        tot = 0.3
    # print key
    samples[key] = Dataset(inputDataset="/QCD_Pt_%dto%d_TuneCUETP8M1_13TeV_pythia8/RunIISpring15Digi74-AVE_20_BX_25ns_tsg_MCRUN2_74_V7%s/GEN-SIM-RAW" % (ptmin, ptmax, ver),
                           useParent=False, unitsPerJob=5, totalUnits=tot)

    # Spring15 AVEPU30 50ns
    key = "QCD_Pt-%dto%d_Spring15_AVE30BX50" % (ptmin, ptmax)
    samples[key] = Dataset(inputDataset="/QCD_Pt_%dto%d_TuneCUETP8M1_13TeV_pythia8/RunIISpring15Digi74-AVE_30_BX_50ns_tsg_MCRUN2_74_V6-v1/GEN-SIM-RAW" % (ptmin, ptmax),
                           useParent=False, unitsPerJob=1, totalUnits=0.1)

    # Phys14 AVEPU20 25ns
    key = "QCD_Pt-%dto%d_Phys14_AVE20BX25" % (ptmin, ptmax)
    ver = "-v1"
    if ptmin in [15, 30]:
        ver = "-v2"
    samples[key] = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Phys14DR-AVE20BX25_tsg_castor_PHYS14_25_V3%s/GEN-SIM-RAW" % (ptmin, ptmax, ver),
                           useParent=False, unitsPerJob=10, totalUnits=0.3)

    # Phys14 AVEPU20 25ns, AODSIM
    key = "QCD_Pt-%dto%d_Phys14_AVE20BX25_AODSIM" % (ptmin, ptmax)
    ver = "-v1"
    if ptmin in [15, 30]:
        ver = "-v2"
    samples[key] = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Phys14DR-AVE20BX25_tsg_castor_PHYS14_25_V3%s/AODSIM" % (ptmin, ptmax, ver),
                           useParent=False, unitsPerJob=3, totalUnits=0.3)

    # Phys14  AVEPU30 50ns
    # manually set totalUnits for smaller jobs
    totUnits = 20 * 50
    key = "QCD_Pt-%dto%d_Phys14_AVE30BX50" % (ptmin, ptmax)
    ver = 1 if ptmin > 49 else 2  # the lowest pt sets are v2 not v1
    samples[key] = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Phys14DR-AVE30BX50_tsg_castor_PHYS14_ST_V1-v%d/GEN-SIM-RAW" % (ptmin, ptmax, ver),
                           useParent=False, unitsPerJob=50, totalUnits=totUnits)

    # Fall13 PU20 25ns
    key = "QCD_Pt-%dto%d_Fall13_PU20bx25" % (ptmin, ptmax)
    samples[key] = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Fall13dr-castor_tsg_PU20bx25_POSTLS162_V2-v1/GEN-SIM-RAW" % (ptmin, ptmax),
                           useParent=False, unitsPerJob=150, totalUnits=-1)

    # Fall13 PU40 25ns
    key = "QCD_Pt-%dto%d_Fall13_PU40bx25" % (ptmin, ptmax)
    samples[key] = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Fall13dr-castor_tsg_PU40bx25_POSTLS162_V2-v1/GEN-SIM-RAW" % (ptmin, ptmax),
                           useParent=False, unitsPerJob=50, totalUnits=-1)

    # Fall13 PU40 50ns
    key = "QCD_Pt-%dto%d_Fall13_PU40bx50" % (ptmin, ptmax)
    samples[key] = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Fall13dr-castor_tsg_PU40bx50_POSTLS162_V2-v1/GEN-SIM-RAW" % (ptmin, ptmax),
                           useParent=False, unitsPerJob=50, totalUnits=-1)

# adhoc mini samples for diff QCD sets
samples_qcd_Spring15_AVE20BX25 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Spring15_AVE20BX25", k))
samples_qcd_Spring15_AVE30BX50 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Spring15_AVE30BX50", k))
samples_qcd_Phys14_AVE20BX25 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Phys14_AVE20BX25$", k))
samples_qcd_Phys14_AVE20BX25_AODSIM = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Phys14_AVE20BX25_AODSIM", k))
samples_qcd_Phys14_AVE30BX50 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Phys14_AVE30BX50", k))
samples_qcd_Fall13_PU20bx25 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Fall13_PU20bx25", k))
samples_qcd_Fall13_PU40bx25 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Fall13_PU40bx25", k))
samples_qcd_Fall13_PU40bx50 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Fall13_PU40bx50", k))
