#ifndef LAZY_SEARCH_H
#define LAZY_SEARCH_H

#include <vector>

#include "open_lists/open_list.h"
#include "search_engine.h"
#include "state.h"
#include "scalar_evaluator.h"
#include "search_space.h"
#include "search_progress.h"

#include <iostream>
#include <fstream>
   
class Heuristic;
class Operator;
class Options;

typedef std::pair<StateID, const Operator *> OpenListEntryLazy;

class LazySearch : public SearchEngine {
protected:
    OpenList<OpenListEntryLazy> *open_list_weighted;
    OpenList<OpenListEntryLazy> *open_list;

    // Search Behavior parameters
    bool reopen_closed_nodes; // whether to reopen closed nodes upon finding lower g paths
    enum {original, pref_first, shuffled} succ_mode;

    std::vector<Heuristic *> heuristics;
    std::vector<Heuristic *> preferred_operator_heuristics;
    std::vector<Heuristic *> estimate_heuristics;

    State current_state;
    StateID current_predecessor_id;
    const Operator *current_operator;
    int current_g;
    int current_real_g;
    int anytime_iteration_counter;
    int f_incumbent;
    bool solution_found;
    std::map<float, float> m_ratio_to_statistics_for_pac;

    double m_pac_epsilon;
    double m_pac_ratio_h;
    bool m_is_H_updated;
    int m_Initial_H;

    virtual void initialize();
    virtual int step();

    void generate_successors();
    int fetch_next_state();

    void reward_progress();

    void get_successor_operators(std::vector<const Operator *> &ops);

	
public:

    LazySearch(const Options &opts);
    virtual ~LazySearch();
    void set_pref_operator_heuristics(std::vector<Heuristic *> &heur);

    virtual void statistics() const;

    void FillPACInfo();

    virtual void InitPacVariables(double epsilon, double delta);
    virtual bool is_Ratio_PAC_Condition_satisfied();


};

class Logger
{
    private:
         std::fstream m_file;
    public:
         void trace(std::string s)
        {
            m_file.open ("/home/gal/downward/Logger.txt", std::fstream::app | std::fstream::out);
            m_file << s << "\n";
            m_file.close();
        }
        Logger(){}
        ~Logger(){}

};

#endif
