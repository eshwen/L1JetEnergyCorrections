// STL headers
#include <iostream>
#include <vector>
#include <utility>
#include <stdexcept>
#include <algorithm>

// ROOT headers
#include "TCanvas.h"
#include "TLegend.h"
#include "TChain.h"
#include "TFile.h"
#include "TDirectoryFile.h"
#include "TTree.h"
#include "TROOT.h"
#include "TSystem.h"
#include "TLorentzVector.h"
#include "TRegexp.h"
#include "TString.h"

// BOOST headers
#include <boost/filesystem.hpp>
// #include <boost/algorithm/string.hpp>

// Headers from this package
#include "DeltaR_Matcher.h"
#include "commonRootUtils.h"
#include "L1ExtraTree.h"
#include "PileupInfoTree.h"
#include "RunMatcherOpts.h"
#include "JetDrawer.h"
#include "SortFilterEmulator.h"
#include "L1Ntuple.h"

using std::cout;
using std::endl;
namespace fs = boost::filesystem;

// forward declare fns, implementations after main()
TString getSuffixFromDirectory(const TString& dir);
bool checkTriggerFired(std::vector<TString> hlt, const TString& selection);
std::vector<TLorentzVector> makeTLorentzVectors(std::vector<double> et,
                                                std::vector<double> eta,
                                                std::vector<double> phi);


/**
 * @brief This program implements an instance of Matcher to produce a ROOT file
 * with matching jet pairs from a L1NTuple file produced by
 * python/l1Ntuple_cfg.py. Can also optionally apply correction functions, and
 * emulate the GCT/Stage 1 by sorting & keeping top 4 cen & fwd jets.
 *
 * @author Robin Aggleton, Nov 2014
 */
int main(int argc, char* argv[]) {

    cout << "Running Matcher for data" << std::endl;

    // deal with user args
    RunMatcherOpts opts(argc, argv);

    ///////////////////////
    // SETUP INPUT FILES //
    ///////////////////////
    L1Ntuple ntuple(opts.inputFilename());
    L1Analysis::L1AnalysisEventDataFormat * event = ntuple.event_;
    L1Analysis::L1AnalysisL1ExtraDataFormat * l1JetTree = ntuple.l1extra_;
    L1Analysis::L1AnalysisRecoJetDataFormat * recoJetTree = ntuple.recoJet_;

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

    std::vector<MatchedPair> matchResults; // holds results from one event

    // setup output tree to store raw variable for quick plotting/debugging
    TTree * outTree2 = new TTree("valid", "valid");
    // pt/eta/phi are for l1 jets, ptRef, etc are for ref jets
    float out_pt(-1.), out_eta(99.), out_phi(99.), out_rsp(-1.), out_rsp_inv(-1.);
    float out_dr(99.), out_deta(99.), out_dphi(99.);
    float out_ptRef(-1.), out_etaRef(99.), out_phiRef(99.);
    float out_ptDiff(99999.), out_resL1(99.), out_resRef(99.);
    float out_trueNumInteractions(-1.), out_numPUVertices(-1.);

    outTree2->Branch("pt",     &out_pt,     "pt/Float_t");
    outTree2->Branch("eta",    &out_eta,    "eta/Float_t");
    outTree2->Branch("phi",    &out_phi,    "phi/Float_t");
    outTree2->Branch("rsp",    &out_rsp,    "rsp/Float_t"); // response = l1 pT/ ref jet pT
    outTree2->Branch("rsp_inv",   &out_rsp_inv,   "rsp_inv/Float_t"); // response = ref pT/ l1 jet pT
    outTree2->Branch("dr",     &out_dr,     "dr/Float_t");
    outTree2->Branch("deta",   &out_deta,   "deta/Float_t");
    outTree2->Branch("dphi",   &out_dphi,   "dphi/Float_t");
    outTree2->Branch("ptRef",  &out_ptRef, "ptRef/Float_t");
    outTree2->Branch("etaRef", &out_etaRef, "etaRef/Float_t");
    outTree2->Branch("phiRef", &out_phiRef, "phiRef/Float_t");
    outTree2->Branch("ptDiff", &out_ptDiff, "ptDiff/Float_t"); // L1 - Ref
    outTree2->Branch("resL1", &out_resL1, "resL1/Float_t"); // resolution = L1 - Ref / L1
    outTree2->Branch("resRef", &out_resRef, "resRef/Float_t"); // resolution = L1 - Ref / Ref
    outTree2->Branch("trueNumInteractions", &out_trueNumInteractions, "trueNumInteractions/Float_t");
    outTree2->Branch("numPUVertices", &out_numPUVertices, "numPUVertices/Float_t");

    Long64_t nEntries = ntuple.GetEntries();
    if (opts.nEvents() > 0 && opts.nEvents() <= nEntries) {
        nEntries = opts.nEvents();
    }
    cout << "Running over " << nEntries << " events." << endl;

    ///////////////////////
    // SETUP JET MATCHER //
    ///////////////////////
    double maxDeltaR(0.7), minRefJetPt(14.), maxRefJetPt(1000.);
    double minL1JetPt(0.), maxL1JetPt(500.), maxJetEta(5);
    std::unique_ptr<Matcher> matcher(new DeltaR_Matcher(maxDeltaR, minRefJetPt, maxRefJetPt, minL1JetPt, maxL1JetPt, maxJetEta));
    std::cout << *matcher << std::endl;

    //////////////////////
    // LOOP OVER EVENTS //
    //////////////////////
    // produce matching pairs and store
    for (Long64_t iEntry = 0; iEntry < nEntries; ++iEntry) {

        if (ntuple.GetEntry(iEntry) == 0) {
            break;
        }

        if (iEntry % 10000 == 0) {
            cout << "Entry: " << iEntry << endl;
        }

        // Check HLT bit
        // if (!checkTriggerFired(event->hlt, "HLT_ZeroBias_v1")) {
        //     continue;
        // }

        if (std::find(event->hlt.begin(), event->hlt.end(), "HLT_ZeroBias_v1") == event->hlt.end()) {
            continue;
        }

        // for (unsigned j = 0; j < event->hlt.size(); j++){
        //     cout << event->hlt[j] << endl;
        // }

        // Get vectors of ref & L1 jets from trees
        // etCorr?
        std::vector<TLorentzVector> refJets = makeTLorentzVectors(recoJetTree->et, recoJetTree->eta, recoJetTree->phi);
        std::vector<TLorentzVector> l1Jets  = makeTLorentzVectors(l1JetTree->cenJetEt, l1JetTree->cenJetEta, l1JetTree->cenJetPhi);
        std::vector<TLorentzVector> fwdJets  = makeTLorentzVectors(l1JetTree->fwdJetEt, l1JetTree->fwdJetEta, l1JetTree->fwdJetPhi);
        std::vector<TLorentzVector> tauJets  = makeTLorentzVectors(l1JetTree->tauJetEt, l1JetTree->tauJetEta, l1JetTree->tauJetPhi);
        l1Jets.insert(l1Jets.end(), fwdJets.begin(), fwdJets.end());
        l1Jets.insert(l1Jets.end(), tauJets.begin(), tauJets.end());
        // cout << "# refJets: " << refJets.size() << endl;
        // cout << "# l1Jets: " << l1Jets.size() << endl;

        // Pass jets to matcher, do matching
        matchResults.clear();
        matcher->setRefJets(refJets);
        matcher->setL1Jets(l1Jets);
        matchResults = matcher->getMatchingPairs();
        // matcher->printMatches(); // for debugging

        // store L1 & ref jet variables in tree
        for (const auto &it: matchResults) {
            // std::cout << it << std::endl;
            out_pt = it.l1Jet().Et();
            out_eta = it.l1Jet().Eta();
            out_phi = it.l1Jet().Phi();
            out_rsp = it.l1Jet().Et()/it.refJet().Et();
            out_rsp_inv =  it.refJet().Et()/it.l1Jet().Et();
            out_dr = it.refJet().DeltaR(it.l1Jet());
            out_deta = it.refJet().Eta() - it.l1Jet().Eta();
            out_dphi = it.refJet().DeltaPhi(it.l1Jet());
            out_ptRef = it.refJet().Pt();
            out_etaRef = it.refJet().Eta();
            out_phiRef = it.refJet().Phi();
            out_ptDiff = it.l1Jet().Et() - it.refJet().Et();
            out_resL1 = out_ptDiff/it.l1Jet().Et();
            out_resRef = out_ptDiff/it.refJet().Et();
            outTree2->Fill();
        }


        // debugging plot - plots eta vs phi of jets
        if (iEntry < opts.drawNumber()) {
            TString label = TString::Format(
                "%.1f < E^{gen}_{T} < %.1f GeV, " \
                "L1 jet %.1f < E^{L1}_{T} < %.1f GeV, |#eta_{jet}| < %.1f",
                minRefJetPt, maxRefJetPt, minL1JetPt, maxL1JetPt, maxJetEta);

            // get jets post pT, eta cuts
            JetDrawer drawer(matcher->getRefJets(), matcher->getL1Jets(), matchResults, label);

            TString pdfname = TString::Format("plots_%s_%s_%s/jets_%lld.pdf",
                inStem.Data(), "reco", "l1", iEntry);
            drawer.drawAndSave(pdfname);
        }

    }

    // save tree to new file and cleanup
    outTree2->Write("", TObject::kOverwrite);

    outFile->Close();

}


/**
 * @brief Get suffix from TDirectory name
 * @details Assumes it starts with "l1ExtraTreeProducer", so
 * e.g. "l1ExtraTreeProducerGctIntern" produces "gctIntern"
 *
 * @param dir Directory name
 * @return Suitable suffix
 */
TString getSuffixFromDirectory(const TString& dir) {
    TString suffix(dir);
    TRegexp re("l1ExtraTreeProducer");
    suffix(re) = "";
    if (suffix == "") suffix = dir;
    return suffix;
}


/**
 * @brief Check if a certain trigger was fired.
 * @details Note, only checks to see if it was fired,
 * not if it was the *only* trigger that was fired.
 *
 * @param hlt Input vector of TStrings of tirgger names fired
 * @param selection Trigger name
 *
 * @return [description]
 */
bool checkTriggerFired(std::vector<TString> hlt, const TString& selection) {
    for (const auto& hltItr: hlt) {
        if (*hltItr == selection)
            return true;
    }
    return false;
}

/**
 * @brief Make a std::vector of TLorentzVectors out of input vectors of et, eta, phi.
 *
 * @param et [description]
 * @param eta [description]
 * @param phi [description]
 * @return [description]
 */
std::vector<TLorentzVector> makeTLorentzVectors(std::vector<double> et,
                                                std::vector<double> eta,
                                                std::vector<double> phi) {
    // check all same size
    if (et.size() != eta.size() || et.size() != phi.size()) {
        throw range_error("Eta/eta/phi vectors different sizes, cannot make TLorentzVectors");
    }
    std::vector<TLorentzVector> vecs;
    for (unsigned i = 0; i < et.size(); i++) {
        TLorentzVector v;
        v.SetPtEtaPhiM(et[i], eta[i], phi[i], 0);
        vecs.push_back(v);
    }
    return vecs;
}
