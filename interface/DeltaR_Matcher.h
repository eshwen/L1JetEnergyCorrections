#ifndef L1Trigger_L1JetEnergyCorrections_DeltaR_Matcher_h
#define L1Trigger_L1JetEnergyCorrections_DeltaR_Matcher_h

// -*- C++ -*-
//
// Package:     L1Trigger/L1JetEnergyCorrections
// Class  :     DeltaR_Matcher
//
/**\class DeltaR_Matcher DeltaR_Matcher.h "L1Trigger/L1JetEnergyCorrections/interface/DeltaR_Matcher.h"

 Description: Implementation of jet matcher using delta R between jets.

 Usage:
    DeltaR_Matcher m;
    m->setRefJets(myRefJets);
    m->setL1Jets(myL1Jets);
    vector<MatchedPair> results = m.getMatchingPairs();
*/
//
// Original Author:  Robin Cameron Aggleton
//         Created:  Wed, 12 Nov 2014 21:21:21 GMT
//
#include "Matcher.h"

#include <iostream>
#include <algorithm>
#include <vector>

#include "TLorentzVector.h"

/**
 * @brief Implementation of jet matcher using delta R between jets.
 * @details DeltaR defined as:
 * (deltaR)^2 = (deltaEta)^2 + (deltaPhi)^2. A L1 jet and ref jet will
 * sucessfully match if deltaR < maxDeltaR, where maxDeltaR must be
 * passed to the object constructor.
 *
 * There is also an optional minimum pT cut on reference and L1 jets, and
 * an optional maximum abs(eta) cuts on jets as well. Defaults for these are found
 * in the constructor. If you want a different cut value, use the relevant constructor or setter.
 */
class DeltaR_Matcher : public Matcher
{

public:

    /**
     * @brief Constructor specifying maximum DeltaR for matching.
     * Set defaults for minRefJetPt, minL1JetPt, maxJetEta such that they have no effect.
     *
     * @param maxDeltaR Maximum deltaR for matching between ref and L1 jet.
     */
    explicit DeltaR_Matcher(const double maxDeltaR);

    /**
     * @brief Constructor, specifying maximum DeltaR for matching, minRefJetPt, minL1JetPt, maxJetEta.
     *
     * @param maxDeltaR Maximum deltaR for matching between ref and L1 jet.
     * @param minRefJetPt Minimum pT a reference jet must have to participate in matching [GeV].
     * @param maxRefJetPt Maximum pT a reference jet must have to participate in matching [GeV].
     * @param minL1JetPt Minimum pT a L1 jet must have to participate in matching [GeV].
     * @param maxL1JetPt Maximum pT a L1 jet must have to participate in matching [GeV].
     * @param maxJetEta Maximum absolute eta of any jet to participate in matching.
     */
    DeltaR_Matcher(const double maxDeltaR,
                   const double minRefJetPt,
                   const double maxRefJetPt,
                   const double minL1JetPt,
                   const double maxL1JetPt,
                   const double maxJetEta);

    virtual ~DeltaR_Matcher();

    /**
     * @brief Set reference jet collection (e.g. GenJets) & sorts by descending pT
     * @details Applies cuts on jets. Only those that pass are saved.
     *
     * @param refJets std::vector of TLorentzVector holding reference jets
     */
    virtual void setRefJets(const std::vector<TLorentzVector>& refJets) override;

    /**
     * @brief Set L1 jet collection (e.g. from GCT) & sorts by descending pT
     * @details Applies cuts on jets. Only those that pass are saved.
     *
     * @param l1Jets std::vector of TLorentzVector holding L1 jets
     */
    virtual void setL1Jets(const std::vector<TLorentzVector>& l1Jets) override;

    /**
     * @brief Set minimum jet pT cut to be applied to reference jets.
     *
     * @param jetPt Minimum pT value.
     */
    void setMinRefJetPt(const double jetPt) { minRefJetPt_ = jetPt; };

    /**
     * @brief Set maximum jet pT cut to be applied to reference jets.
     *
     * @param jetPt Maximum pT value.
     */
    void setMaxRefJetPt(const double jetPt) { maxRefJetPt_ = jetPt; };

    /**
     * @brief Set minimum jet pT cut to be applied to L1 jets.
     *
     * @param jetPt Minimum pT value.
     */
    void setMinL1JetPt(const double jetPt) { minL1JetPt_ = jetPt; };

    /**
     * @brief Set maximum jet pT cut to be applied to L1 jets.
     *
     * @param jetPt Maximum pT value.
     */
    void setMaxL1JetPt(const double jetPt) { maxL1JetPt_ = jetPt; };

    /**
     * @brief Set maximum absolute jet eta cut to be applied to both L1 and ref jets.
     *
     * @param jetEta Maximum absolute Eta value
     */
    void setMaxJetEta(const double jetEta) { maxJetEta_ = jetEta; };

    /**
     * @brief Produce pairs of L1 jets matched to reference jets based on deltaR(refJet-l1Jet).
     *
     * @details For each L1 jet, we loop over all reference jets. For each
     * pair, we calculate deltaR between the jets. If deltaR < maxDeltaR_, it
     * counts as a match. If there are > 1 possible matches, the one with the
     * smallest deltaR is used.
     * Note that because the jets are sorted by pT, higher pT L1 jets get priority
     * in matching, since we remove a refJet from potential matches once matched
     * to a L1 jet.
     *
     * @return Returns a vector of of matched jets, held in MatchedPair object.
     */
    virtual std::vector<MatchedPair> getMatchingPairs() override;


private:

    /**
     * @brief Check reference jet passes cuts
     *
     * @param jet Jet to check
     * @return [description]
     */
    bool checkRefJet(const TLorentzVector& jet);

    /**
     * @brief Check L1 jet passes cuts
     *
     * @param jet Jet to check
     * @return [description]
     */
    bool checkL1Jet(const TLorentzVector& jet);

    /**
     * @brief Check if jet pT >= minPt.
     *
     * @param jet Jet under test.
     * @param minPt Minimum pT cut value.
     *
     * @return Whether jet passed test.
     */
    bool checkJetMinPt(const TLorentzVector& jet, const double minPt) const;

    /**
     * @brief Check if jet pT <= maxPt
     *
     * @param jet Jet under test
     * @param maxPt Maximum pT cut value
     *
     * @return Whether jet passed test.
     */
    bool checkJetMaxPt(const TLorentzVector& jet, const double maxPt) const;

    /**
     * @brief Check if abs(eta) of jet <= maxEta.
     *
     * @param jet Jet under test.
     * @param eta Maximum absolute eta allowed.
     *
     * @return Whether jet passed test.
     */
    bool checkJetMaxEta(const TLorentzVector& jet, const double maxEta) const;

    /**
     * @brief Binary predicate to use in std::sort, to allow sorting TLorentzVectors by descending pT
     * @details Since this is a CLASS method, need to make it static for it to work in std::sort. Maybe
     * I should make it a common function outside of the class?
     *
     * @param a One TLorentzVector
     * @param b Other TLorentzVector
     *
     * @return True if a.Pt() > b.Pt()
     */
    static bool sortPtDescending(const TLorentzVector &a, const TLorentzVector &b) { return (a.Pt() > b.Pt()); } ;

    /**
     * @brief Function to print out basic details, used by ostream operator.
     */
    virtual std::ostream&  printName(std::ostream& os) const override;

    const double maxDeltaR_; // Maximum deltaR between reference and L1 jet to count as a 'match'.
    double minRefJetPt_; // Minimum pT for reference jet to take part in matching.
    double maxRefJetPt_; // Maximum pT for reference jet to take part in matching.
    double minL1JetPt_; // Minimum pT for L1 jet to take part in matching.
    double maxL1JetPt_; // Maximum pT for L1 jet to take part in matching.
    double maxJetEta_;  // Maximum absolute eta for any jet to take part in matching.
};

#endif /* L1Trigger_L1JetEnergyCorrections_DeltaR_Matcher_h */