#!/bin/bash

# Submit checkCalibration jobs on HTCondor using the DAGman feature.
# All you need to do is add in the relevant pairs file(s) you wish to run over.
# Use absolute path!
#
# For each pairs file, creates a dag file. This does all the eta bins in
# separate jobs, and then hadds them all after.

declare -a pairsFiles=(
# /hdfs/user/ra12451/L1JEC/CMSSW_7_4_2/src/L1Trigger/L1JetEnergyCorrections/QCDSpring15_Stage1_AVE20BX25_newRCTv2/pairs_QCD_Pt-15to1000_Spring15_AVE20BX25_Stage1_QCDSpring15_newRCTv2_preGt_ak4_ref14to1000_l10to500.root
# /hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_QCDFlatSpring15BX25HCALFix_26Nov_76X_mcRun2_asymptotic_v5_jetSeed1p5_jec22Nov/pairs/pairs_QCDFlatSpring15BX25PU10to30HCALFix_MP_ak4_ref10to5000_l10to5000_dr0p4.root
# /hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_Run260627/pairs/pairs_ntuples_data_ref10to5000_l10to5000_dr0p4.root
# /hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_QCDFlatSpring15BX25HCALFix_26Nov_76X_mcRun2_asymptotic_v5_jetSeed1p5_noJec_v2/pairs/pairs_QCDFlatSpring15BX25PU10to30HCALFix_MP_ak4_ref10to5000_l10to5000_dr0p4.root
# /hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_Run260627_JEC/pairs/pairs_ntuples_data_ref10to5000_l10to5000_dr0p4.root
# /hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_Run260627/pairs/pairs_Express_data_ref10to5000_l10to5000_dr0p4_noCleaning.root
# /hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_Run260627_JEC/pairs/pairs_Express_data_ref10to5000_l10to5000_dr0p4_noCleaning.root
/hdfs/user/ra12451/L1JEC/CMSSW_7_6_0_pre7/L1JetEnergyCorrections/Stage2_Run260627/pairs/pairs_Express_data_ref10to5000_l10to5000_dr0p4_tightLepVeto.root
)

declare -a etaBins=(
0
0.348
0.695
1.044
1.392
1.74
2.172
3.0
# 3.5
# 4.0
# 4.5
# 5
)

# update the setup scripts for worker nodes
sed -i "s/VER=CMSSW_.*/VER=$CMSSW_VERSION/" condor_worker.sh
sed -i "s@RDIR=/.*@RDIR=$ROOTSYS@" condor_worker.sh
sed -i "s/VER=CMSSW_.*/VER=$CMSSW_VERSION/" hadd.sh

# make a copy of the condor script for these jobs. Can use the same one for
# all of them, just pass in different arguments
outfile="submit_checkCalib.condor"
cp submit_template.condor "$outfile"
echo 'arguments = $(opts)' >> "$outfile"
echo "queue" >> "$outfile"

# Replace correct parts
datestamp=$(date "+%d_%b_%Y")
logDir="jobs/checkCalib/${datestamp}"
if [ ! -d "$logD" ]; then
    mkdir -p $logDir
fi
sed -i "s@SEDNAME@${logDir}/checkCalib@g" $outfile # for log files
sed -i 's/SEDEXE/condor_worker.sh/g' $outfile # thing to execute on worker node
cdir=${PWD%HTCondor}
echo $cdir
sed -i "s@SEDINPUTFILES@$cdir/checkCalibration.py, $cdir/binning.py, $cdir/correction_LUT_plot.py, $cdir/common_utils.py@" $outfile

declare -a statusFileNames=()

# Queue up jobs
for pairs in "${pairsFiles[@]}"
do
    # check file actually exists
    if [ ! -e "$pairs" ]; then
        echo "$Pairs does not exist!"
        exit 1
    fi

    # Puts the output in relevant directory,
    # e.g. if pairs in Stage1/pairs/xxx/pairs.root
    # output goes to Stage1/check/xxx/check.root
    fdir=`dirname $pairs`
    fdir=${fdir/pairs/check}
    if [ ! -d "$fdir" ]; then
        mkdir -p $fdir
        echo "Making output dir $fdir"
    fi
    fname=`basename $pairs`

    echo "Using pairs file $pairs"
    echo "Writing output to directory: $fdir"

    # Make DAG file for this pairs file
    # To make sure we don't overlap with another, we give it a timestamp + random string
    timestamp=$(date "+%H%M%S")
    rand=$(cat /dev/urandom | tr -dc 'a-zA-Z' | fold -w 3 | head -n 1)
    dagfile="checkCalib_${timestamp}_${rand}.dag"
    echo "# dag file for $pairs" >> $dagfile
    echo "# output will be $fdir" >> $dagfile

    # Store all jobs names and output fileNames for later
    declare -a jobNames=()
    declare -a outFileNames=()

    # Maximum pT for L1 jets
    maxPt=1022

    # PU cuts
    puMin=-30
    puMax=40

    # Special appendix, if desired (e.g. if changing a param)
    append=""
    # append="${append}_PU${puMin}to${puMax}_maxPt${maxPt}"
    append="${append}_maxPt${maxPt}"

    outname=${fname/pairs_/check_}
    outname=${outname%.root}

    # Write jobs to DAG file
    # Do individual eta bins first
    len=${#etaBins[@]}
    len=$(( len - 1 ))
    for ((i=0;i<$len;++i));
    do
        j=$(( i + 1 ))
        etamin=${etaBins[i]}
        etamax=${etaBins[j]}

        jobname="checkCalib_${etamin}to${etamax}"
        jobname="checkCalib_${i}"
        jobNames+=($jobname)

        outRootName="${fdir}/${outname}_${i}${append}.root"
        outFileNames+=($outRootName)

        echo "JOB $jobname $outfile" >> "$dagfile"
        echo "VARS $jobname opts=\"${pairs} ${outRootName} python checkCalibration.py ${pairs} ${outRootName} --excl --maxPt ${maxPt} --PUmin ${puMin} --PUmax ${puMax} --etaInd ${i}\"" >> "$dagfile"
    done

    # Now do inclusive bins (central, forward, all)
    jobname="checkCalib_central"
    jobNames+=($jobname)
    outRootName="${fdir}/${outname}_central${append}.root"
    outFileNames+=($outRootName)
    echo "JOB $jobname $outfile" >> "$dagfile"
    echo "VARS $jobname opts=\"${pairs} ${outRootName} python checkCalibration.py ${pairs} ${outRootName} --incl --central --maxPt ${maxPt} --PUmin ${puMin} --PUmax ${puMax}\"" >> "$dagfile"

    # jobname="checkCalib_forward"
    # jobNames+=($jobname)
    # outRootName="${fdir}/${outname}_forward${append}.root"
    # outFileNames+=($outRootName)
    # echo "JOB $jobname $outfile" >> "$dagfile"
    # echo "VARS $jobname opts=\"${pairs} ${outRootName} python checkCalibration.py ${pairs} ${outRootName} --incl --forward --maxPt ${maxPt} --PUmin ${puMin} --PUmax ${puMax}\"" >> "$dagfile"

    # jobname="checkCalib_all"
    # jobNames+=($jobname)
    # outRootName="${fdir}/${outname}_all${append}.root"
    # outFileNames+=($outRootName)
    # echo "JOB $jobname $outfile" >> "$dagfile"
    # echo "VARS $jobname opts=\"${pairs} ${outRootName} python checkCalibration.py ${pairs} ${outRootName} --incl --maxPt ${maxPt} --PUmin ${puMin} --PUmax ${puMax}\"" >> "$dagfile"

    # Now add job for hadding
    finalRootName="${fdir}/${outname}${append}.root"
    haddJobName="haddCheckCalib"
    echo "JOB $haddJobName hadd_small.condor" >> "$dagfile"
    echo "VARS $haddJobName opts=\"$finalRootName ${outFileNames[@]}\"" >> "$dagfile"
    echo "Output file: $finalRootName"

    # Add in parent-child relationships & status file
    echo "PARENT ${jobNames[@]} CHILD $haddJobName" >> "$dagfile"
    statusfile="checkCalib_${timestamp}_${rand}.status"
    echo "NODE_STATUS_FILE $statusfile 30" >> "$dagfile"
    statusFileNames+=($statusfile)

    # Submit jobs
    autoSub=true
    for f in "${outFileNames[@]}"; do
        if [ -e $f ]; then
            echo "One of the output files already exists, please check your setup."
            autoSub=false
            break
        fi
    done
    echo ""
    echo "Condor DAG script made"
    echo "Submit with:"
    echo "condor_submit_dag $dagfile"
    if [ $autoSub = true ]; then
        echo "Submitting..."
        condor_submit_dag "$dagfile"
    else
        echo "***** WARNING: Not auto submitting. *****"
    fi
    echo ""
    echo "Check status with:"
    echo "./DAGstatus.py $statusfile"
    echo ""
    echo "(may take a little time to appear)"
done

if [ ${#statusFileNames[@]} -gt "1" ]; then
    echo "To check all statuses:"
    echo "./DAGstatus.py ${statusFileNames[@]}"
fi