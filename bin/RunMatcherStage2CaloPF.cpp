#include <fstream>
#include <map>
#include <algorithm>

// ROOT headers
#include "TChain.h"
#include "TFile.h"
#include "TTree.h"
#include "TROOT.h"
#include "TSystem.h"
#include "TMath.h"

// BOOST headers
#include <boost/filesystem.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/predicate.hpp>
#include <boost/lexical_cast.hpp>

// Headers from L1TNtuples
#include "L1Trigger/L1TNtuples/interface/L1AnalysisEventDataFormat.h"
#include "L1Trigger/L1TNtuples/interface/L1AnalysisL1ExtraDataFormat.h"
#include "L1Trigger/L1TNtuples/interface/L1AnalysisRecoJetDataFormat.h"
#include "L1Trigger/L1TNtuples/interface/L1AnalysisL1UpgradeDataFormat.h"
#include "L1Trigger/L1TNtuples/interface/L1AnalysisRecoVertexDataFormat.h"
#include "L1Trigger/L1TNtuples/interface/L1AnalysisGeneratorDataFormat.h"

// Headers from this package
#include "DeltaR_Matcher.h"
#include "commonRootUtils.h"
#include "L1GenericTree.h"
#include "PileupInfoTree.h"
#include "RunMatcherOpts.h"
#include "JetDrawer.h"
#include "runMatcherUtils.h"

using std::cout;
using std::endl;
using L1Analysis::L1AnalysisEventDataFormat;
using L1Analysis::L1AnalysisRecoJetDataFormat;
using L1Analysis::L1AnalysisL1ExtraDataFormat;
using L1Analysis::L1AnalysisL1UpgradeDataFormat;
using L1Analysis::L1AnalysisRecoVertexDataFormat;
using L1Analysis::L1AnalysisGeneratorDataFormat;
using boost::lexical_cast;

namespace fs = boost::filesystem;

/**
 * @brief Matching PF jets from JetRecoTree, to reference GenJets from the L1ExtraTree.
 *
 * @author Eshwen Bhal, May 2018
 * Warning: the header file that recognises the leaves for the reco/calo objects (L1TNtuples/interface/L1AnalysisRecoJetDataFormat.h) may not include native support for the calo jet leaves you need.
   Check the header file for references to "caloEt", "caloEta" and "caloPhi".
   If they're not included, add the lines `calo${quantity}.clear();` and `std::vector<float> calo${quantity};` in the relevant places. Then, recompile.
 */
int main(int argc, char* argv[]) {

    cout << "Running Matcher, offline Calo jets to GenJets" << std::endl;

    // deal with user args
    RunMatcherOpts opts(argc, argv);

    ///////////////////////
    // SETUP INPUT FILES //
    ///////////////////////

    // get input TTrees
    // Reference jets - PFJets
    TString refJetDirectory = opts.refJetDirectory();
    L1GenericTree<L1AnalysisRecoJetDataFormat> refJetTree(opts.inputFilename(),
                                                          refJetDirectory+"/JetRecoTree",
                                                          "Jet");
    L1AnalysisRecoJetDataFormat * refData = refJetTree.getData();

    // "L1" jets - CaloJets
    TString l1JetDirectory = opts.l1JetDirectory();
    L1GenericTree<L1AnalysisRecoJetDataFormat> l1JetTree(opts.inputFilename(),
                                                          l1JetDirectory+"/JetRecoTree",
                                                          "Jet");
    L1AnalysisRecoJetDataFormat * l1Data = l1JetTree.getData();

    // TTree that holds PileupInfo
    //    PileupInfoTree puInfoTree(opts.inputFilename());

    // hold Event tree
    L1GenericTree<L1AnalysisEventDataFormat> eventTree(opts.inputFilename(),
                                                         "l1EventTree/L1EventTree",
                                                         "Event");
    L1AnalysisEventDataFormat * eventData = eventTree.getData();

    // hold reco vertex info
    L1GenericTree<L1AnalysisRecoVertexDataFormat> recoVtxTree(opts.inputFilename(),
                                                              "l1RecoTree/RecoTree",
                                                              "Vertex");
    L1AnalysisRecoVertexDataFormat * recoVtxData = recoVtxTree.getData();

    // input filename stem (no .root)
    fs::path inPath(opts.inputFilename());
    TString inStem(inPath.stem().c_str());

    ////////////////////////
    // SETUP OUTPUT FILES //
    ////////////////////////

    // setup output file to store results
    // check that we're not overwriting the input file!
    if (opts.outputFilename() == opts.inputFilename()) {
        throw std::runtime_error("Cannot use input filename as output filename!");
    }
    TFile * outFile = openFile(opts.outputFilename(), "RECREATE");
    fs::path outPath(opts.outputFilename());
    TString outDir(outPath.parent_path().c_str());
    if (outDir != "") {
        outDir += "/";
    }

    // setup output tree to store raw variable for quick plotting/debugging
    TTree outTree("valid", "valid");

    // Quantities for L1 jets:
    float out_pt(-1.), out_eta(99.), out_phi(99.);
    int out_nL1(-1); // number of jets in the event,
    outTree.Branch("pt", &out_pt, "pt/Float_t");
    outTree.Branch("eta", &out_eta, "eta/Float_t");
    outTree.Branch("phi", &out_phi, "phi/Float_t");
    outTree.Branch("nL1", &out_nL1, "nL1/Int_t");

    // Quantities for reference jets (GenJet, etc):
    float out_ptRef(-1.), out_etaRef(99.), out_phiRef(99.);
    int out_nRef(-1);
    outTree.Branch("ptRef", &out_ptRef, "ptRef/Float_t");
    outTree.Branch("etaRef", &out_etaRef, "etaRef/Float_t");
    outTree.Branch("phiRef", &out_phiRef, "phiRef/Float_t");
    outTree.Branch("nRef", &out_nRef, "nRef/Int_t");

    // Cleaning vars
    float out_chef(-1.), out_nhef(-1.), out_pef(-1.), out_eef(-1.), out_mef(-1.), out_hfhef(-1.), out_hfemef(-1.);
    short out_chMult(-1), out_nhMult(-1), out_phMult(-1), out_elMult(-1), out_muMult(-1), out_hfhMult(-1), out_hfemMult(-1);
    outTree.Branch("chef", &out_chef, "chef/F");
    outTree.Branch("nhef", &out_nhef, "nhef/F");
    outTree.Branch("pef", &out_pef, "pef/F");
    outTree.Branch("eef", &out_eef, "eef/F");
    outTree.Branch("mef", &out_mef, "mef/F");
    outTree.Branch("hfhef", &out_hfhef, "hfhef/F");
    outTree.Branch("hfemef", &out_hfemef, "hfemef/F");
    outTree.Branch("chMult", &out_chMult, "chMult/S");
    outTree.Branch("nhMult", &out_nhMult, "nhMult/S");
    outTree.Branch("phMult", &out_phMult, "phMult/S");
    outTree.Branch("elMult", &out_elMult, "elMult/S");
    outTree.Branch("muMult", &out_muMult, "muMult/S");
    outTree.Branch("hfhMult", &out_hfhMult, "hfhMult/S");
    outTree.Branch("hfemMult", &out_hfemMult, "hfemMult/S");

    // Quantities to describe relationship between the two:
    float out_rsp(-1.);
    float out_dr(99.), out_deta(99.), out_dphi(99.);
    float out_ptDiff(99999.), out_resL1(99.), out_resRef(99.);
    int out_nMatches(0);
    outTree.Branch("ptDiff", &out_ptDiff, "ptDiff/Float_t"); // L1 - Ref
    outTree.Branch("rsp", &out_rsp, "rsp/Float_t"); // response = l1 pT/ ref jet pT
    outTree.Branch("dr", &out_dr, "dr/Float_t");
    outTree.Branch("deta", &out_deta, "deta/Float_t");
    outTree.Branch("dphi", &out_dphi, "dphi/Float_t");
    outTree.Branch("resL1", &out_resL1, "resL1/Float_t"); // resolution = L1 - Ref / L1
    outTree.Branch("resRef", &out_resRef, "resRef/Float_t"); // resolution = L1 - Ref / Ref
    outTree.Branch("nMatches", &out_nMatches, "nMatches/Int_t");

    // PU quantities
    float out_trueNumInteractions(-1.), out_numPUVertices(-1.);
    int out_recoNVtx(0);
    outTree.Branch("trueNumInteractions", &out_trueNumInteractions, "trueNumInteractions/Float_t");
    outTree.Branch("numPUVertices", &out_numPUVertices, "numPUVertices/Float_t");
    outTree.Branch("recoNVtx", &out_recoNVtx, "recoNVtx/Int_t");

    // Event number
    int out_event(0);
    outTree.Branch("event", &out_event, "event/Int_t");

    // L1 sums
    int out_nL1JetsSum(0);
    float out_httL1(0.);
    float out_mhtL1(0.), out_mhtPhiL1(0.);
    outTree.Branch("nL1JetsSum", &out_nL1JetsSum);
    outTree.Branch("httL1", &out_httL1);
    outTree.Branch("mhtL1", &out_mhtL1);
    outTree.Branch("mhtPhiL1", &out_mhtPhiL1);

    // Reference jet Sums
    int out_nRefJetsSum(0);
    float out_httRef(0.);
    float out_mhtRef(0.), out_mhtPhiRef(0.);
    outTree.Branch("nRefJetsSum", &out_nRefJetsSum);
    outTree.Branch("httRef", &out_httRef);
    outTree.Branch("mhtRef", &out_mhtRef);
    outTree.Branch("mhtPhiRef", &out_mhtPhiRef);

    // check # events in boths trees is same
    Long64_t nEntriesRef = refJetTree.getEntries();
    Long64_t nEntriesL1  = l1JetTree.getEntries();
    Long64_t nEntries(0);
    if (nEntriesRef != nEntriesL1) {
        throw std::range_error("Different number of events in L1 & ref trees");
    } else {
        nEntries = (opts.nEvents() > 0) ? opts.nEvents() : nEntriesL1;
        cout << "Running over " << nEntries << " events." << endl;
    }

    ///////////////////////
    // SETUP JET MATCHER //
    ///////////////////////
    double maxDeltaR(opts.deltaR()), minRefJetPt(opts.refJetMinPt()), maxRefJetPt(5000.);
    double minL1JetPt(opts.l1JetMinPt()), maxL1JetPt(5000.), maxJetEta(5.);
    std::unique_ptr<Matcher> matcher(new DeltaR_Matcher(maxDeltaR, minRefJetPt, maxRefJetPt, minL1JetPt, maxL1JetPt, maxJetEta));
    std::cout << *matcher << std::endl;

    bool doCleaningCuts = opts.cleanJets() != "";
    if (doCleaningCuts) {
        cout << "Applying " << opts.cleanJets() << " jet cleaning cuts" << endl;
    }

    //////////////////////
    // LOOP OVER EVENTS //
    //////////////////////
    // produce matching pairs and store
    for (Long64_t iEntry = 0; iEntry < nEntries; ++iEntry) {
        if (iEntry % 10000 == 0) {
            cout << "Entry: " << iEntry << " at " << getCurrentTime() << endl;
        }

        if (refJetTree.getEntry(iEntry) < 1 || l1JetTree.getEntry(iEntry) < 1 ||
            eventTree.getEntry(iEntry) < 1 || recoVtxTree.getEntry(iEntry) < 1)
            break;

        ////////////////////////
        // Generic event info //
        ////////////////////////
        out_event = eventData->event;

        /////////////////////////////
        // Store pileup quantities //
        /////////////////////////////
        // note these get stored once per pair of matched jets NOT once per event
	//        puInfoTree.GetEntry(iEntry);
	//        out_trueNumInteractions = puInfoTree.trueNumInteractions();
	//        out_numPUVertices = puInfoTree.numPUVertices();
	//        out_recoNVtx = recoVtxData->nVtx;

        /////////////////////////////////////////////
        // Make vectors of ref & L1 jets from trees //
        /////////////////////////////////////////////
        std::vector<TLorentzVector> refJets = makeTLorentzVectors(refData->et, refData->eta, refData->phi);

        std::vector<TLorentzVector> l1Jets;
        if (doCleaningCuts) {
            l1Jets = makeRecoTLorentzVectorsCleaned(*l1Data, opts.cleanJets()); // with JetID filters
        } else {
	  l1Jets = makeTLorentzVectors(l1Data->caloEt, l1Data->caloEta, l1Data->caloPhi); // etCorr used before but nEntries for it were different to eta and phi
        }

        out_nL1 = l1Jets.size();
        out_nRef = refJets.size();

        if (out_nL1 == 0 || out_nRef == 0) continue;

        ////////////////
        // Store sums //
        ////////////////
        // L1 sums
        std::vector<TLorentzVector> httL1Jets = getJetsForHTT(l1Jets);
        out_nL1JetsSum = httL1Jets.size();
        out_httL1 = scalarSumPt(httL1Jets);
        TLorentzVector mhtVecL1 = vectorSum(httL1Jets);
        out_mhtL1 = mhtVecL1.Pt();
        out_mhtPhiL1 = mhtVecL1.Phi();

        // Ref jet sums
        std::vector<TLorentzVector> httRefJets = getJetsForHTT(refJets);
        out_nRefJetsSum = httRefJets.size();
        out_httRef = scalarSumPt(httRefJets);
        TLorentzVector mhtVecRef = vectorSum(httRefJets);
        out_mhtRef = mhtVecRef.Pt();
        out_mhtPhiRef = mhtVecRef.Phi();

        // if (out_httL1 >= 30 && out_httRef == 0) {
        //     cout << "HTTL1 == " << out_httL1 << ", HTT GEN == 0" << endl;
        //     cout << "L1 jets in HTT:" << endl;
        //     for (const auto& itr: l1Jets) {
        //         if (passHTTCut(itr))
        //             cout << itr.Pt() << " " << itr.Eta() << " " << itr.Phi() << endl;
        //     }
        //     cout << "ref jets:" << endl;
        //     for (const auto& itr: refJets) {
        //         cout << itr.Pt() << " " << itr.Eta() << " " << itr.Phi() << endl;
        //     }
        // }


        ///////////////////////////////////////
        // Pass jets to matcher, do matching //
        ///////////////////////////////////////
        matcher->setRefJets(refJets);
        matcher->setL1Jets(l1Jets);

        std::vector<MatchedPair> matchResults = matcher->getMatchingPairs();
        // matcher->printMatches(); // for debugging

        //////////////////////////////////////////
        // store L1 & ref jet variables in tree //
        //////////////////////////////////////////
        out_nMatches = matchResults.size();
        for (const auto &it: matchResults) {
            out_pt = it.l1Jet().Pt();
            out_eta = it.l1Jet().Eta();
            out_phi = it.l1Jet().Phi();
            out_dr = it.refJet().DeltaR(it.l1Jet());
            out_deta = it.refJet().Eta() - it.l1Jet().Eta();
            out_dphi = it.refJet().DeltaPhi(it.l1Jet());
            out_ptRef = it.refJet().Pt();
            out_etaRef = it.refJet().Eta();
            out_phiRef = it.refJet().Phi();
            out_ptDiff = out_pt - out_ptRef;
            out_rsp = out_pt/out_ptRef;
            out_resL1 = out_ptDiff/out_pt;
            out_resRef = out_ptDiff/out_ptRef;

            int rInd = findRecoJetIndex(out_pt, out_eta, out_phi, *l1Data);
	    cout << "R IND IS " << rInd << endl;
            if (rInd < 0) throw std::range_error("No RecoJet");
            out_chef = l1Data->chef[rInd];
            out_nhef = l1Data->nhef[rInd];
            out_pef = l1Data->pef[rInd];
            out_eef = l1Data->eef[rInd];
            out_mef = l1Data->mef[rInd];
            out_hfhef = l1Data->hfhef[rInd];
            out_hfemef = l1Data->hfemef[rInd];
            out_chMult = l1Data->chMult[rInd];
            out_nhMult = l1Data->nhMult[rInd];
            out_phMult = l1Data->phMult[rInd];
            out_elMult = l1Data->elMult[rInd];
            out_muMult = l1Data->muMult[rInd];
            out_hfhMult = l1Data->hfhMult[rInd];
            out_hfemMult = l1Data->hfemMult[rInd];
            outTree.Fill();
        }

    } // end of loop over entries

    // save tree to new file and cleanup
    outTree.Write("", TObject::kOverwrite);
    outFile->Close();
    return 0;
}
