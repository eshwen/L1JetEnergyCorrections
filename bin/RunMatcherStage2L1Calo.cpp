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
 * @brief Matching L1 jets from L1UpgradeTree, to reference CaloJets from JetRecoTree.
 *
 * @author Eshwen Bhal, May 2018.
 * Warning: the header file that recognises the leaves for the reco/calo objects (L1TNtuples/interface/L1AnalysisRecoJetDataFormat.h) may not include native support for the calo jet leaves you need.
   Check the header file for references to "caloEt", "caloEta" and "caloPhi".
   If they're not included, add the lines `calo${quantity}.clear();` and `std::vector<float> calo${quantity};` in the relevant places. Then, recompile.
 * You may also have to comment out the if() conditions in the function "findRecoJetIndex" in src/runMatcherUtils.cc
 */
int main(int argc, char* argv[]) {

    cout << "Running Matcher, L1 Jets to CaloJets" << std::endl;

    // deal with user args
    RunMatcherOpts opts(argc, argv);

    ///////////////////////
    // SETUP INPUT FILES //
    ///////////////////////

    // get input TTrees
    // Reference jets - CaloJets
    TString refJetDirectory = opts.refJetDirectory();
    L1GenericTree<L1AnalysisRecoJetDataFormat> refJetTree(opts.inputFilename(),
                                                          refJetDirectory+"/JetRecoTree",
                                                          "Jet");
    L1AnalysisRecoJetDataFormat * refData = refJetTree.getData();

    // L1 jets
    TString l1JetDirectory = opts.l1JetDirectory();
    L1GenericTree<L1AnalysisL1UpgradeDataFormat> l1JetTree(opts.inputFilename(),
                                                           l1JetDirectory+"/L1UpgradeTree",
                                                           "L1Upgrade");
    L1AnalysisL1UpgradeDataFormat * l1Data = l1JetTree.getData();

    // hold Event tree
    L1GenericTree<L1AnalysisEventDataFormat> eventTree(opts.inputFilename(),
                                                         "l1EventTree/L1EventTree",
                                                         "Event");
    L1AnalysisEventDataFormat * eventData = eventTree.getData();

    // hold reco vertex info
    // L1GenericTree<L1AnalysisRecoVertexDataFormat> recoVtxTree(opts.inputFilename(),
    //                                                           "l1RecoTree/RecoTree",
    //                                                            "Vertex");
    // L1AnalysisRecoVertexDataFormat * recoVtxData = recoVtxTree.getData();

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
    int out_ind(-1); // index of this jet in the collection (ordered by descending pT)
    outTree.Branch("pt", &out_pt, "pt/Float_t");
    outTree.Branch("eta", &out_eta, "eta/Float_t");
    outTree.Branch("phi", &out_phi, "phi/Float_t");
    outTree.Branch("nL1", &out_nL1, "nL1/Int_t");
    outTree.Branch("indL1", &out_ind, "indL1/Int_t");
    // Quantities for reference jets (GenJet, etc):
    float out_ptRef(-1.), out_etaRef(99.), out_phiRef(99.);
    int out_nRef(-1), out_indRef;
    outTree.Branch("ptRef", &out_ptRef, "ptRef/Float_t");
    outTree.Branch("etaRef", &out_etaRef, "etaRef/Float_t");
    outTree.Branch("phiRef", &out_phiRef, "phiRef/Float_t");
    outTree.Branch("nRef", &out_nRef, "nRef/Int_t");
    outTree.Branch("inRef", &out_indRef, "indRef/Int_t");
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
    ULong64_t out_event(0);
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
    // use base class smart pointer for ease of swapping in/out different
    //  matchers if so desired
    std::unique_ptr<Matcher> matcher(new DeltaR_Matcher(maxDeltaR, minRefJetPt, maxRefJetPt, minL1JetPt, maxL1JetPt, maxJetEta));
    std::cout << *matcher << std::endl;

    //////////////////////
    // LOOP OVER EVENTS //
    //////////////////////
    // produce matching pairs and store
    Long64_t drawCounter = 0;
    for (Long64_t iEntry = 0; iEntry < nEntries; ++iEntry) {
        if (iEntry % 10000 == 0) {
            cout << "Entry: " << iEntry << " at " << getCurrentTime() << endl;
        }

        if (refJetTree.getEntry(iEntry) < 1 || l1JetTree.getEntry(iEntry) < 1 ||
            eventTree.getEntry(iEntry) < 1)// || recoVtxTree.getEntry(iEntry) < 1)
            break;

        ////////////////////////
        // Generic event info //
        ////////////////////////
        out_event = eventData->event;

        /////////////////////////////
        // Store pileup quantities //
        /////////////////////////////
        // note these get stored once per pair of matched jets NOT once per event
        // out_trueNumInteractions = refData->nMeanPU;
        // out_numPUVertices = refData->nVtx;

        /////////////////////////////////////////////
        // Make vectors of ref & L1 jets from trees //
        /////////////////////////////////////////////
        std::vector<TLorentzVector> refJets = makeTLorentzVectors(refData->caloEt, refData->caloEta, refData->caloPhi);
        std::vector<TLorentzVector> l1Jets = makeTLorentzVectors(l1Data->jetEt, l1Data->jetEta, l1Data->jetPhi);

        out_nL1 = l1Jets.size();
        out_nRef = refJets.size();

        if (out_nL1 == 0 || out_nRef == 0) continue;

        ////////////////
        // Store sums //
        ////////////////
        // L1 sums
        std::vector<TLorentzVector> httL1Jets = getJetsForHTT(l1Jets);
        out_nL1JetsSum = httL1Jets.size();
        out_httL1 = l1Data->sumEt[2];
        out_mhtL1 = l1Data->sumEt[3];
        out_mhtPhiL1 = l1Data->sumPhi[3];
        float httL1_check = scalarSumPt(httL1Jets);

        // Check my calc with stored value
        // Doens't make sense to do this when applying calibrations on the fly
        // if (fabs(out_httL1 - httL1_check) > 0.01 && out_httL1 < 2047.5) {
        //     cout << "HTT L1 not agreeing with calculation: " + lexical_cast<std::string>(out_httL1) + " vs " + lexical_cast<std::string>(httL1_check) << endl;
        //     for (const auto& itr: l1Jets) {
        //         cout << itr.Pt() << " " << itr.Eta() << endl;
        //     }
        // }

        TLorentzVector mhtL1_check = vectorSum(httL1Jets);

        // Override sums with calibrated jets
        out_httL1 = httL1_check;
        out_mhtL1 = mhtL1_check.Pt();
        out_mhtPhiL1 = mhtL1_check.Phi();

        // Ref jet sums
        std::vector<TLorentzVector> httRefJets = getJetsForHTT(refJets);
        out_nRefJetsSum = httRefJets.size();
        out_httRef = scalarSumPt(httRefJets);
        // Pass jets to matcher, do matching
        TLorentzVector mhtVecRef = vectorSum(httRefJets);
        out_mhtRef = mhtVecRef.Pt();
        out_mhtPhiRef = mhtVecRef.Phi();

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
            // std::cout << it << std::endl;
            out_pt = it.l1Jet().Et();
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
            outTree.Fill();
        }

        ///////////////////////////////////////////////////
        // debugging plot - plots eta vs phi map of jets //
        ///////////////////////////////////////////////////
        if (drawCounter < opts.drawNumber()) {
            if (matchResults.size() > 0) {
                TString label = TString::Format(
                    "%.1f < E^{gen}_{T} < %.1f GeV, " \
                    "L1 jet %.1f < E^{L1}_{T} < %.1f GeV, |#eta_{jet}| < %.1f",
                    minRefJetPt, maxRefJetPt, minL1JetPt, maxL1JetPt, maxJetEta);
                // get jets post pT, eta cuts
                JetDrawer drawer(matcher->getRefJets(), matcher->getL1Jets(), matchResults, label);

                TString pdfname = TString::Format("%splots_%s_%s_%s/jets_%lld.pdf",
                    outDir.Data(), inStem.Data(), "gen", "l1", iEntry);
                drawer.drawAndSave(pdfname);

                drawCounter++;
            }
        }
    } // end of loop over entries

    // save tree to new file and cleanup
    outTree.Write("", TObject::kOverwrite);
    outFile->Close();
    return 0;
}


