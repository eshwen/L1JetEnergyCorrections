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
#include "RunMatcherOpts.h"
#include "JetDrawer.h"
#include "SortFilterEmulator.h"

using std::cout;
using std::endl;
namespace fs = boost::filesystem;

// forward declare fns, implementations after main()
TString getSuffixFromDirectory(const TString& dir);
void loadCorrectionFunctions(const TString& filename,
                             std::vector<TF1>& corrFns,
                             const std::vector<float>& etaBins);
void correctJets(std::vector<TLorentzVector>& jets,
                 std::vector<TF1>& corrFns,
                 std::vector<float>& etaBins,
                 float minPt);

/**
 * @brief This program implements an instance of Matcher to produce a ROOT file
 * with matching jet pairs from a L1NTuple file produced by
 * python/l1Ntuple_cfg.py. Can also optionally apply correction functions, and
 * emulate the GCT/Stage 1 by sorting & keeping top 4 cen & fwd jets.
 *
 * @author Robin Aggleton, Nov 2014
 */
int main(int argc, char* argv[]) {

    cout << "Running Matcher" << std::endl;

    // deal with user args
    RunMatcherOpts opts(argc, argv);

    ///////////////////////
    // SETUP INPUT FILES //
    ///////////////////////

    // get input L1Extra TDirectories/TTrees
    // assumes TTree named "L1ExtraTree", but can specify in ctor of L1ExtraTree
    TString refJetDirectory                 = opts.refJetDirectory();
    TString refJetSuffix                    = getSuffixFromDirectory(refJetDirectory);
    std::vector<std::string> refJetBranches = opts.refJetBranchNames();

    TString l1JetDirectory                  = opts.l1JetDirectory();
    TString l1JetSuffix                     = getSuffixFromDirectory(l1JetDirectory);
    std::vector<std::string> l1JetBranches  = opts.l1JetBranchNames();

    // also specify which branches jets are stored in
    // for genJets & gctIntern, it's just cenJet branch,
    // for gctDigis, it's cen/fwd/tau
    L1ExtraTree refJetExtraTree(opts.inputFilename(), refJetDirectory);
    L1ExtraTree l1JetExtraTree(opts.inputFilename(), l1JetDirectory);

    // input filename stem (no .root)
    fs::path inPath(opts.inputFilename());
    TString inStem(inPath.stem().c_str());

    //////////////////////////////////////////////////////////////
    // GET CORRECTION FUNCTIONS, SETUP SORT & FILTER (optional) //
    //////////////////////////////////////////////////////////////
    // N.B do this *before* opening output file below.
    // Otherwise, you'll have to add in a outFile->cd() to save ttree to file.
    bool doCorrections = false;
    std::vector<float> etaBins = {0.0, 0.348, 0.695, 1.044, 1.392, 1.74, 2.172, 3.0, 3.5, 4.0, 4.5, 5.001};
    std::vector<TF1> correctionFunctions;
    unsigned nTop = 4;
    std::unique_ptr<SortFilterEmulator> emu(new SortFilterEmulator(nTop));
    if (opts.correctionFilename() != "") {
        doCorrections = true;
        loadCorrectionFunctions(opts.correctionFilename(), correctionFunctions, etaBins);
    }

    ////////////////////////
    // SETUP OUTPUT FILES //
    ////////////////////////

    // setup output file to store results
    // check that we're not overwriting the input file!
    if (opts.outputFilename() == opts.inputFilename()) {
        throw std::runtime_error("Cannot use input filename as output filename!");
    }
    TFile * outFile = openFile(opts.outputFilename(), "RECREATE");

    // setup output tree to store matched pairs (keep all info)
    // DON'T USE FOR NOW - HARD TO COMPILE- need to fix LinkDef.h
    // TString outTreeName = TString::Format("MatchedPairs_%s_%s",
        // refJetSuffix.Data(), l1JetSuffix.Data());
    // TTree * outTree = new TTree(outTreeName, outTreeName);
    std::vector<MatchedPair> matchResults; // holds results from one event
    // outTree->Branch("MatchedPairs", &matchResults);

    // setup output tree to store raw variable for quick plotting/debugging
    TTree * outTree2 = new TTree("valid", "valid");
    // pt/eta/phi are for l1 jets, ptRef, etc are for ref jets
    float out_pt(-1.), out_eta(99.), out_phi(99.), out_rsp(-1.), out_rsp2(-1.);
    float out_dr(99.), out_deta(99.), out_dphi(99.);
    float out_ptRef(-1.), out_etaRef(99.), out_phiRef(99.);
    float out_ptDiff(99999.), out_resL1(99.), out_resGen(99.);

    outTree2->Branch("pt",     &out_pt,     "pt/Float_t");
    outTree2->Branch("eta",    &out_eta,    "eta/Float_t");
    outTree2->Branch("phi",    &out_phi,    "phi/Float_t");
    outTree2->Branch("rsp",    &out_rsp,    "rsp/Float_t"); // response = refJet pT/ l1 jet pT (inverted definition)
    outTree2->Branch("rsp2",   &out_rsp2,   "rsp2/Float_t"); // response = l1 pT/ ref jet pT
    outTree2->Branch("dr",     &out_dr,     "dr/Float_t");
    outTree2->Branch("deta",   &out_deta,   "deta/Float_t");
    outTree2->Branch("dphi",   &out_dphi,   "dphi/Float_t");
    outTree2->Branch("ptRef",  &out_ptRef, "ptRef/Float_t");
    outTree2->Branch("etaRef", &out_etaRef, "etaRef/Float_t");
    outTree2->Branch("phiRef", &out_phiRef, "phiRef/Float_t");
    outTree2->Branch("ptDiff", &out_ptDiff, "ptDiff/Float_t"); // L1 - Gen
    outTree2->Branch("resL1", &out_resL1, "resL1/Float_t"); // resolution = L1 - Gen / L1
    outTree2->Branch("resGen", &out_resGen, "resGen/Float_t"); // resolution = L1 - Gen / Gen

    // check # events in boths trees is same
    Long64_t nEntriesRef = refJetExtraTree.fChain->GetEntriesFast();
    Long64_t nEntriesL1  = l1JetExtraTree.fChain->GetEntriesFast();
    Long64_t nEntries(0);
    if (nEntriesRef != nEntriesL1) {
        throw range_error("Different number of events in L1 & ref trees");
    } else {
        nEntries = (opts.nEvents() > 0) ? opts.nEvents() : nEntriesL1;
        cout << "Running over " << nEntries << " events." << endl;
    }

    ///////////////////////
    // SETUP JET MATCHER //
    ///////////////////////
    double maxDeltaR(0.7), minRefJetPt(14.), maxRefJetPt(500.);
    double minL1JetPt(0.), maxL1JetPt(500.), maxJetEta(5);
    std::unique_ptr<Matcher> matcher(new DeltaR_Matcher(maxDeltaR, minRefJetPt, maxRefJetPt, minL1JetPt, maxL1JetPt, maxJetEta));
    std::cout << *matcher << std::endl;

    //////////////////////
    // LOOP OVER EVENTS //
    //////////////////////
    // produce matching pairs and store
    for (Long64_t iEntry = 0; iEntry < nEntries; ++iEntry) {

        // jentry is the entry # in the current Tree
        Long64_t jentry = refJetExtraTree.LoadTree(iEntry);
        if (jentry < 0) break;
        if (iEntry % 10000 == 0) {
            cout << "Entry: " << iEntry << endl;
        }
        refJetExtraTree.fChain->GetEntry(iEntry);
        l1JetExtraTree.fChain->GetEntry(iEntry);

        // Get vectors of ref & L1 jets from trees
        std::vector<TLorentzVector> refJets = refJetExtraTree.makeTLorentzVectors(refJetBranches);
        std::vector<TLorentzVector> l1Jets  = l1JetExtraTree.makeTLorentzVectors(l1JetBranches);

        // If doing corrections, split into cen & fwd jets, sort & filter
        // - do it here before matching
        if (doCorrections) {
            correctJets(l1Jets, correctionFunctions, etaBins, opts.correctionMinPt());
            emu->setJets(l1Jets);
            l1Jets = emu->getAllJets();
        }

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
            out_rsp = it.refJet().Et()/it.l1Jet().Et();
            out_rsp2 = it.l1Jet().Et()/it.refJet().Et();
            out_dr = it.refJet().DeltaR(it.l1Jet());
            out_deta = it.refJet().Eta() - it.l1Jet().Eta();
            out_dphi = it.refJet().DeltaPhi(it.l1Jet());
            out_etaRef = it.refJet().Eta();
            out_phiRef = it.refJet().Phi();
            out_ptDiff = it.l1Jet().Et() - it.refJet().Et();
            out_resL1 = out_ptDiff/it.l1Jet().Et();
            out_resGen = out_ptDiff/it.refJet().Et();
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
                inStem.Data(), refJetSuffix.Data(), l1JetSuffix.Data(), iEntry);
            drawer.drawAndSave(pdfname);
        }

        // outTree->Fill();
    }

    // save tree to new file and cleanup
    // outTree->Write("", TObject::kOverwrite);
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
 * @brief Get correction functions from file, and load into vector.
 * @details Note that correction functions have names
 * "fitfcneta_<etaMin>_<etaMax>", where etaMin/Max denote eta bin limits.
 *
 * @param filename  Name of file with correction functions.
 * @param corrFns   Vector of TF1s in which functions are stored.
 */
void loadCorrectionFunctions(const TString& filename,
                             std::vector<TF1>& corrFns,
                             const std::vector<float>& etaBins) {

    TFile * corrFile = openFile(filename, "READ");

    // Loop over eta bins
    for (unsigned ind = 0; ind < etaBins.size()-1; ++ind) {
        float etaMin(etaBins[ind]), etaMax(etaBins[ind+1]);
        TString binName = TString::Format("fitfcneta_%g_%g", etaMin, etaMax);
        TF1 * fit = dynamic_cast<TF1*>(corrFile->Get(binName));
        // Make a copy of function and store in vector
        if (fit) {
            TF1 fitFcn(*fit);
            corrFns.push_back(fitFcn);
        } else {
            throw invalid_argument(binName.Prepend("No TF1 with name ").Data());
        }
    }
    corrFile->Close();
}


/**
 * @brief Apply correction function to collection of jets
 * @details [long description]
 *
 * @param corrFn   Vector of TF1 to be applied, corresponding to eta bins
 * @param etaBins  Eta bin limits
 * @param minPt    Minimum jet pT for correction to be applied. If unspecified,
 * it only applies corrections for jets within the fit range of the function.
 */
void correctJets(std::vector<TLorentzVector>& jets,
                 std::vector<TF1>& corrFns,
                 std::vector<float>& etaBins,
                 float minPt) {
    // NB to future self: tried to make corrFns and etaBins const,
    // but lower_bound doesn't like that

    // check corrFn correct size
    if (corrFns.size() != etaBins.size()-1) {
        throw range_error("Corrections functions don't match eta bins");
    }

    // Loop over jets, get correct function for given |eta| & apply if necessary
    for (auto& jetItr: jets) {
        // Get eta bin limits corresponding to jet |eta|
        float absEta = fabs(jetItr.Eta());
        auto maxItr = std::lower_bound(etaBins.begin(), etaBins.end(), absEta);
        if (maxItr == etaBins.begin()) {
            throw range_error("Max eta != first eta bin");
        }
        auto minItr = maxItr - 1;

        // Get correction fn for this bin
        TF1 corrFn = corrFns[minItr-etaBins.begin()];

        // Get fit range
        double fitMin(0.), fitMax(0.);
        corrFn.GetRange(fitMin, fitMax);

        // Now decide if we should apply corrections
        if (((minPt < 0.) && (jetItr.Pt() > fitMin) && (jetItr.Pt() < fitMax))
            || ((minPt >= 0.) && (jetItr.Pt() >= minPt))) {
            // corrFn.Print();
            float newPt = jetItr.Pt() * corrFn.Eval(jetItr.Pt());
            // safeguard against crazy values
            if (newPt < 1000. && newPt > 0.) {
                jetItr.SetPtEtaPhiM(newPt, jetItr.Eta(), jetItr.Phi(), jetItr.M());
            }
        }
    }
}
