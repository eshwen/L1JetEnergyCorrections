#!/bin/bash -e
#
# Setup CMSSW
VER=CMSSW_9_2_8
echo "Setting up ${VER} ..."
echo "... sourcing CMS default environment from CVMFS"
source /cvmfs/cms.cern.ch/cmsset_default.sh
echo "... creating CMSSW project area"
scramv1 project CMSSW ${VER}
cd ${VER}/src
eval `scramv1 runtime -sh`
echo "${VER} has been set up"
cd ../..