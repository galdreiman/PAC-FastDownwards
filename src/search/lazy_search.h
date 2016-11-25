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
    OpenList<OpenListEntryLazy> *open_list_no_weights;
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
    int current_h;
    int anytime_iteration_counter;
    int f_incumbent;
    bool solution_found;
    std::map<float, float> m_ratio_to_statistics_for_pac;
    std::map<float, float> m_hstar_statistics_for_trivial_pac;
    std::map<float, float> m_inadmissible_statistics_for_pac;
    std::map<std::string, std::map<std::string, float> > m_PAC_statistics;

    double m_pac_epsilon;
    double m_pac_delta;
    double m_pac_ratio_h;
    bool m_is_H_updated;
    bool m_isRpac_lower_bound_satisfied;
    bool m_is_running_trivial_pac;
    bool m_is_running_ratio_based_pac;
    bool m_is_running_RPac_Lower_Bound;
    bool m_is_running_open_based_pac;
    bool m_is_open_based_pac_cond_sutisfied;
    int m_Initial_H;
    int m_max_f_min;
    int m_last_f_val;
    bool m_debug_f_min;
    bool m_is_running_admissible_heuristic;

    double m_open_based_P_hat;
    int m_infinity_nodes_counter;


    virtual void initialize();
    virtual int step();

    void generate_successors();
    int fetch_next_state();

    void reward_progress();

    void get_successor_operators(std::vector<const Operator *> &ops);

    void calculate_p_hat();

    void increase_p_hat(int g, int h);
    void decrease_p_hat(int g, int h);

    int get_min_f();
    int get_h_from_state_id(StateID stateId);
    int get_g_from_state_id(StateID stateId);

	
public:

    LazySearch(const Options &opts);
    virtual ~LazySearch();
    void set_pref_operator_heuristics(std::vector<Heuristic *> &heur);

    virtual void statistics() const;

    void FillPACInfo();

    virtual void InitPacVariables(double epsilon, double delta, int is_lower_bound, int is_rpac_open_based, int is_trivial_pac, int is_ratio_based, std::string is_running_admissible_heuristic);
    virtual bool is_Trivial_PAC_Condition_satisfied();
    virtual bool is_Ratio_PAC_Condition_satisfied();
    virtual bool is_Ratio_PAC_Condition_Lower_Bound_satisfied();
    virtual bool is_Ratio_PAC_Condition_Open_Based_satisfied();
    virtual bool read_stats_file(std::string filename, std::map<float, float> & stats);
    virtual bool read_PAC_statistics_csv(std::string filename, std::map<std::string, std::map<std::string, float> > & stats); // problem -> [parameter-name -> value]



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
