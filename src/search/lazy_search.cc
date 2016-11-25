#include "lazy_search.h"

#include "g_evaluator.h"
#include "heuristic.h"
#include "successor_generator.h"
#include "sum_evaluator.h"
#include "weighted_evaluator.h"
#include "plugin.h"

#include <algorithm>
#include <limits>
#include <math.h>

static const int DEFAULT_LAZY_BOOST = 1000;

LazySearch::LazySearch(const Options &opts)
    : SearchEngine(opts),
      open_list(opts.get<OpenList<OpenListEntryLazy> *>("open")),
      reopen_closed_nodes(opts.get<bool>("reopen_closed")),
      succ_mode(pref_first),
      current_state(g_initial_state()),
      current_predecessor_id(StateID::no_state),
      current_operator(NULL),
      current_g(0),
      current_real_g(0),
      current_h(0)
{       

    if(opts.getIsAnyTime() == true)
        m_is_anytime = true;
    else 
        m_is_anytime = false;

}

LazySearch::~LazySearch() {
}

void LazySearch::set_pref_operator_heuristics(
    vector<Heuristic *> &heur) {
    preferred_operator_heuristics = heur;
}

void LazySearch::initialize() {
    //TODO children classes should output which kind of search
    cout << "Conducting lazy best first search, (real) bound = " << bound << endl;

    assert(open_list != NULL);
    set<Heuristic *> hset;
    open_list->get_involved_heuristics(hset);

    for (set<Heuristic *>::iterator it = hset.begin(); it != hset.end(); it++) {
        estimate_heuristics.push_back(*it);
        search_progress.add_heuristic(*it);
    }

    // add heuristics that are used for preferred operators (in case they are
    // not also used in the open list)
    hset.insert(preferred_operator_heuristics.begin(),
                preferred_operator_heuristics.end());

    for (set<Heuristic *>::iterator it = hset.begin(); it != hset.end(); it++) {
        heuristics.push_back(*it);
    }
    assert(!heuristics.empty());

    f_incumbent = 0;
    solution_found = false;
    m_is_H_updated = false;
    m_isRpac_lower_bound_satisfied = false;
    m_is_open_based_pac_cond_sutisfied = false;
    m_Initial_H = -1;
    m_infinity_nodes_counter = 0;
    
}

void LazySearch::get_successor_operators(vector<const Operator *> &ops) {
    vector<const Operator *> all_operators;
    vector<const Operator *> preferred_operators;

    g_successor_generator->generate_applicable_ops(
        current_state, all_operators);

    for (int i = 0; i < preferred_operator_heuristics.size(); i++) {
        Heuristic *heur = preferred_operator_heuristics[i];
        if (!heur->is_dead_end())
            heur->get_preferred_operators(preferred_operators);
    }

    if (succ_mode == pref_first) {
        for (int i = 0; i < preferred_operators.size(); i++) {
            if (!preferred_operators[i]->is_marked()) {
                ops.push_back(preferred_operators[i]);
                preferred_operators[i]->mark();
            }
        }

        for (int i = 0; i < all_operators.size(); i++)
            if (!all_operators[i]->is_marked())
                ops.push_back(all_operators[i]);
    } else {
        for (int i = 0; i < preferred_operators.size(); i++)
            if (!preferred_operators[i]->is_marked())
                preferred_operators[i]->mark();
        ops.swap(all_operators);
        if (succ_mode == shuffled)
            random_shuffle(ops.begin(), ops.end());
    }
}

void LazySearch::generate_successors() 
{

    // double error = 1 + m_pac_epsilon;
    // double prob = 0;
    // bool found = false;     

    vector<const Operator *> operators;
    get_successor_operators(operators);
    search_progress.inc_generated(operators.size());
    for (int i = 0; i < operators.size(); i++) 
    {
        int new_g = current_g + get_adjusted_cost(*operators[i]);
        int new_real_g = current_real_g + operators[i]->get_cost();
        bool is_preferred = operators[i]->is_marked();
        if (is_preferred)
        {
            operators[i]->unmark();
        }
        if (new_real_g < bound)
        {
            open_list->evaluate(new_g, is_preferred);
            bool to_insert = false;
            if (m_is_anytime)
            {
                int f_val = open_list->evaluate_for_anytime(new_g, is_preferred); // GAL: check why do evaluate twice?
               // cout << "evaluate_for_anytime: g = " << current_g << " c = " << get_adjusted_cost(*operators[i]) << " f = " << f_val << std::endl;
                if (f_val < f_incumbent || solution_found == false)
                    to_insert = true;

                if(m_is_running_open_based_pac && f_incumbent > 0)
                {

                    if(to_insert)
                    {
                        //calculate m_open_based_P_hat:
                        int current_h = f_val - new_g;

                        if(new_g >= 0 && current_h >= 0) {
                            increase_p_hat(new_g, current_h);
                        }else{
                            cout << " WARN:    generate_successors: g and h may be negative: g[" << current_g << " ] h[" << current_h << "]" << endl;
                        }
                    }

                    // check if oben based pac condition is satisfied
                    // ----------------------------------------------
                    
                    
                    if(is_Ratio_PAC_Condition_Open_Based_satisfied())
                    {
                        cout<< "generate_successors: " ;
                        cout<< "is_Ratio_PAC_Condition_Open_Based_satisfied ! ! !  "  << endl;
                        // cout<< "m_open_based_P_hat = " << m_open_based_P_hat << endl;
                        m_is_open_based_pac_cond_sutisfied = true;

                        return;
                    }
                }
            }
            else
            {
                to_insert = true;
            }
            
            if (to_insert)
            {
                open_list->insert(
                    make_pair(current_state.get_id(), operators[i]));

            }
        }
    } // for(...)


    
}

int LazySearch::fetch_next_state() {
    if (open_list->empty()) {
        if (solution_found)
        {
            cout << "Completely explored state space -- but solution already found!" << endl;
            return SOLVED;
        }
        else
        {
            cout << "Completely explored state space -- no solution!" << endl;
        }
        return FAILED;
    }



    OpenListEntryLazy next = open_list->remove_min();

    current_predecessor_id = next.first;
    current_operator = next.second;
    State current_predecessor = g_state_registry->lookup_state(current_predecessor_id);
    assert(current_operator->is_applicable(current_predecessor));
    current_state = g_state_registry->get_successor_state(current_predecessor, *current_operator);

    SearchNode pred_node = search_space.get_node(current_predecessor);
    current_g = pred_node.get_g() + get_adjusted_cost(*current_operator);
    current_real_g = pred_node.get_real_g() + current_operator->get_cost();
    current_h = heuristics[0]->get_value();
//    cout << "H: " << endl <<
//                     "             current_h = " << current_h << endl <<
//                     "             get_h = " <<  search_space.get_node(current_state).get_h();

//    cout << "DEBUG:" << endl <<
//            "       pred_node.get_g() = " << pred_node.get_g() << endl <<
//            "       pred_node.get_h() = " << pred_node.get_h() << endl;

    //decrease p_hat:
    if(m_is_running_open_based_pac && f_incumbent > 0 && !m_is_open_based_pac_cond_sutisfied)
    {
        // remove last node expanded from sum:
        //------------------------------------
        // cout << "OPEN BASED: remove last node expanded from sum:" << endl;

        int h = pred_node.get_g();
        int g = pred_node.get_h();

        if(h>=0 && g >=0)
        {
            decrease_p_hat(g, h);
        }
        else{
            cout << " WARN:    step (decrease_p_hat): g and h may be negative: g[" << g << " ] h[" << h << "]" << endl;
        }

    }


    return IN_PROGRESS;
}



int LazySearch::step() {
    // Invariants:
    // - current_state is the next state for which we want to compute the heuristic.
    // - current_predecessor is a permanent pointer to the predecessor of that state.
    // - current_operator is the operator which leads to current_state from predecessor.
    // - current_g is the g value of the current state according to the cost_type
    // - current_g is the g value of the current state (using real costs)


    SearchNode node = search_space.get_node(current_state);

//    cout << "DEBUG step():" << endl <<
//            "       current_g = " << current_g << endl <<
//            "       current_h = " << current_h << endl;




    bool reopen = reopen_closed_nodes && (current_g < node.get_g()) && !node.is_dead_end() && !node.is_new();
    if (node.is_new() || reopen) 
    {
        StateID dummy_id = current_predecessor_id;
        // HACK! HACK! we do this because SearchNode has no default/copy constructor
        if (dummy_id == StateID::no_state) 
        {
            dummy_id = g_initial_state().get_id();
        }
        State parent_state = g_state_registry->lookup_state(dummy_id);
        SearchNode parent_node = search_space.get_node(parent_state);

        for (int i = 0; i < heuristics.size(); i++) 
        {
            if (current_operator != NULL) 
            {
                heuristics[i]->reach_state(parent_state, *current_operator, current_state);
            }
            heuristics[i]->evaluate(current_state);
        }
        search_progress.inc_evaluated_states();
        search_progress.inc_evaluations(heuristics.size());
        open_list->evaluate(current_g, false);
        if (!open_list->is_dead_end()) 
        {
            // We use the value of the first heuristic, because SearchSpace only
            // support storing one heuristic value
            int h = heuristics[0]->get_value();
            if(!m_is_H_updated)
            {
                m_Initial_H = h;
                m_is_H_updated = true;
            }

            if(m_is_running_open_based_pac)
            {
                m_last_f_val = h + current_g;

            }
          
            if (reopen) 
            {
                node.reopen(parent_node, current_operator);
                search_progress.inc_reopened();
            } 

            else if (current_predecessor_id == StateID::no_state) 
            {
                node.open_initial(h);
                search_progress.get_initial_h_values();
            } 

            else 
            {
                node.open(h, parent_node, current_operator);
            }
           
            node.close();

            if (check_goal_and_set_plan(current_state))
            {

                cout << "FOUND GOAL WITH g= "<< current_g <<" and h=" << h << endl;

                char* debugEnv;
                debugEnv = getenv ("DEBUG_LEVEL");
                if (debugEnv!=NULL)
                {
                    cout << "------------  Statistics   ------------" << endl;
                    search_progress.print_h_line(current_g);
                    save_plan(get_plan(), 0);
                    statistics();
                    cout << "---------------------------------------" << endl;
                }

                if (!m_is_anytime)
                    return SOLVED;

                else
                {
                    if (!solution_found)
                    {
                        solution_found = true;
                        f_incumbent = current_g;
                         cout << "first new f_incumbent = [" << f_incumbent <<"]" << endl;
                        //calculate p-hat for open based PAC condition:
                        // NOTE: p-hat calculation is performed after every new solution
                        calculate_p_hat(); 
                    }
                    else
                    {
                        if (current_g < f_incumbent)
                        {
                            f_incumbent = current_g;
                            // cout << "improve new f_incumbent = [" << f_incumbent <<"]" << endl;
                            //calculate p-hat for open based PAC condition:
                            // NOTE: p-hat calculation is performed after every new solution
                            calculate_p_hat();
                        }
                    }

                    if(  m_is_running_trivial_pac   )
                    {
                        if( is_Trivial_PAC_Condition_satisfied() )
                        {
                            cout << "*****************" << endl;
                            return SOLVED;
                        }
                    }

                    //check if Ratio Based PAC condition is satisfied
                    if(  m_is_running_ratio_based_pac   )
                    {
                        if( is_Ratio_PAC_Condition_satisfied() )
                        {
                            cout << "*****************" << endl;
                            return SOLVED;
                        }
                    }

                    //ration based + lower bound pac condition:
                    // for every node generation we check for lower bound pac consition
                    // f_val at this point is max(f_min) - because we check f value every step
                    if(m_is_running_RPac_Lower_Bound)
                    {
                        // int f_val = h + current_g;
                        if(is_Ratio_PAC_Condition_Lower_Bound_satisfied())
                        {
                            // if during serch RPAC+LB is satisfied we set the member to true
                            // next time we check the member is when check RPAC in step()
                            m_isRpac_lower_bound_satisfied = true;
                            cout << "INFO: is_Ratio_PAC_Condition_Lower_Bound_satisfied? "<< 1 << std::endl;
                            return SOLVED;
                        }
                    }

                    //check if this run is set to RPAB+LB
                    // if( m_is_running_RPac_Lower_Bound)
                    //     // if it does - check if the condition is met
                    //     if(m_isRpac_lower_bound_satisfied)
                    //         return SOLVED;

                    if(m_is_running_open_based_pac)
                        // cout<< "step = " <<  endl;
                        if(is_Ratio_PAC_Condition_Open_Based_satisfied())
                        {
                            m_is_open_based_pac_cond_sutisfied = true;
                            cout << "m_is_open_based_pac_cond_sutisfied = TRUE ----> solution found!" << endl;
                            return SOLVED;
                        }
                }
            }
            if (search_progress.check_h_progress(current_g)) 
            {
                reward_progress();
            }

            if(!m_is_open_based_pac_cond_sutisfied)
            {
                generate_successors();
                search_progress.inc_expanded();

                int f_val = get_min_f();
                // cout << "fmin =" << f_val << endl;
                if(f_val > m_max_f_min)
                {
                    m_max_f_min = f_val;
                    if(m_is_running_admissible_heuristic)
                    {
                        cout << "update m_max_f_min to " << m_max_f_min << endl;
                        // this is a basic condition that gurenties suboptimality - TODO - make it common
                        // cout << "U/m_max_f_min= " << f_incumbent/m_max_f_min <<  endl;
                        if(f_incumbent > 0 && double(f_incumbent)/double(m_max_f_min) <= 1+m_pac_epsilon)
                        {
                            cout << "$$$ basic condition that gurenties suboptimality is satisfied(!!!): "<<endl 
                                                        <<"$$ U["<< f_incumbent 
                                                           <<"]/m_max_f_min["<<m_max_f_min 
                                                        <<"] = " <<double(f_incumbent)/double(m_max_f_min) 
                                                        <<" <= 1+m_pac_epsilon [" << 1+m_pac_epsilon << "]" 
                                                        << endl;
                            return SOLVED;
                        }
                    }

                    if(m_is_running_RPac_Lower_Bound)
                    {
                        if(is_Ratio_PAC_Condition_Lower_Bound_satisfied())
                        {
                            cout << "m_is_running_RPac_Lower_Bound = TRUE ----> solution found!" << endl;
                            m_isRpac_lower_bound_satisfied = true;
                        }
                    }
                }
            }
            else 
                return SOLVED;

        } 
        else 
        {
            node.mark_as_dead_end();
            search_progress.inc_dead_ends();
        }
    }

    if((m_is_running_RPac_Lower_Bound && m_isRpac_lower_bound_satisfied) || (m_is_running_open_based_pac && m_is_open_based_pac_cond_sutisfied))
    {
        cout << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
        return SOLVED;
    }

    return fetch_next_state();
}

/*
----
\
 \                h*[   ]       1    [     U                ]
 /   Log(1 - Pr( ---| S | <  ------- |----------  - g_node  | ))  >= Log(1-delta)
/                 h [   ]     h_node [ 1+epsilon            ]
----
*/

/*
1 - init p-hat to 0
2 - go over all nodes in OPEN-LIST and calculate according to the above 
    pac condition 'p-hat'

*/
void LazySearch::calculate_p_hat()
{
    if(!m_is_running_open_based_pac || m_is_open_based_pac_cond_sutisfied)
        return;

    m_open_based_P_hat = 0.0;


    std::vector<OpenListEntryLazy> openListStates;
    open_list->getFlattedOpenList(openListStates);
   
    std::vector<OpenListEntryLazy>::iterator it;
    for(it = openListStates.begin(); it != openListStates.end(); ++it)
    {
        // cout << "stateId = [" << it->first << "]" << endl;

        StateID sId = it->first;
        // const Operator * sOperator = it->second;

        State s = g_state_registry->lookup_state(sId);
        SearchNode sNode = search_space.get_node(s);
        
        int g = sNode.get_g(); 
        int h = sNode.get_h();

        // cout << "calculate_p_hat: g = [" << g << "]" << "h = [" << h << "]" << endl;

        if(g >= 0 && h >= 0) {
            increase_p_hat(g, h);
        }else{
            cout << " WARN:    calculate_p_hat: g and h may be negative: g[" << g << " ] h[" << h << "]" << endl;
        }
         
    }

}

int LazySearch::get_h_from_state_id(StateID stateId)
{
    State s = g_state_registry->lookup_state(stateId);
    return search_space.get_node(s).get_h();
}
int LazySearch::get_g_from_state_id(StateID stateId)
{
    State s = g_state_registry->lookup_state(stateId);
    return search_space.get_node(s).get_g();
}



/*
----
\
 \                h*[   ]       1    [     U                ]
 /   Log(1 - Pr( ---| S | <  ------- |----------  - g_node  | ))  >= Log(1-delta)
/                 h [   ]     h_node [ 1+epsilon            ]
----
*/

void LazySearch::increase_p_hat(int g, int h)
{
    // cout << "increase_p_hat:         g = [" << g << "]" << endl;
    // cout << "increase_p_hat:         h = [" << h << "]" << endl;
    // cout << "increase_p_hat:         f_incumbent = [" << f_incumbent << "]" << endl;
     if(g + h >= f_incumbent || m_is_open_based_pac_cond_sutisfied)
        return;

    double error = 1 + m_pac_epsilon;
    double prob = 0;
    // bool found = false;  
    if(h == 0)
        return;

    double right = (1.0/h) *  ( (double(f_incumbent) / error)  - g );
    std::map<float, float>::const_iterator iter = m_ratio_to_statistics_for_pac.begin();
 
    while(iter != m_ratio_to_statistics_for_pac.end() && iter->first < right)
    {
        ++iter;
    }

    prob = iter->second / 100;


    if(prob == 1)
    {
        cout << "cought prob=1. meaning that added_val=log(1-1)=log(0)=infinity" << endl;
        cout << "right = [" << right <<"]" << endl;
        cout << "right = (1.0/h[" << 1.0/h << "]) *  ( (double(f_incumbent["<<f_incumbent<<"]) / double(error["<<error<< "]))  - g["<<g<<"] )" << endl;
        cout << "increase_p_hat   right = [" << right << "]" << endl;
        m_infinity_nodes_counter += 1;

        cout << "********************************************************************" << endl;
        cout << "m_infinity_nodes_counter" << m_infinity_nodes_counter << endl;
        cout << "********************************************************************" << endl;

        return;
    }
    double added_val = log(1-prob);
//        char str[128];
//        sprintf(str, "increase_p_hat: adding log(1 - prob[%f]) = [%f]   g[%d]  h[%d]\n", prob, added_val,g,h);
//        cout << str;

    m_open_based_P_hat += added_val; //log(1 - prob);
    // cout << " m_open_based_P_hat = [" << m_open_based_P_hat << "]" << endl;
    
    return;
}

/*
----
\
 \                h*[   ]       1    [     U                ]
 /   Log(1 - Pr( ---| S | <  ------- |----------  - g_node  | ))  >= Log(1-delta)
/                 h [   ]     h_node [ 1+epsilon            ]
----
*/

void LazySearch::decrease_p_hat(int g, int h)
{
    double error = 1 + m_pac_epsilon;
    double prob = 0;
    if(h == 0)
        return;

    double right = (1.0/h) *  ( (double(f_incumbent) / error)  - g );
    
    // cout << "decrease_p_hat   right = [" << right << "]" << endl;

    std::map<float, float>::const_iterator iter = m_ratio_to_statistics_for_pac.begin();
 
    while(iter != m_ratio_to_statistics_for_pac.end() && iter->first < right)
    {
         ++iter;
    }
    prob = iter->second /100;
        
    if(prob == 1)
    {
        m_infinity_nodes_counter -= 1;
        cout << "********************************************************************" << endl;
        cout << "m_infinity_nodes_counter" << m_infinity_nodes_counter << endl;
        cout << "********************************************************************" << endl;
        return;
    }

    double added_val = log(1-prob);
//    char str[128];
//    sprintf(str, "decrease_p_hat: adding log(1 - prob[%f]) = [%f]   g[%d]  h[%d]\n", prob, added_val,g,h);
//    cout << str  << endl;

    m_open_based_P_hat -= added_val; //log(1 - prob);
//    cout << "calc P hat: m_open_based_P_hat = [" << m_open_based_P_hat << "]" << endl;
}

int LazySearch::get_min_f()
{
    // int min_f = -1;
    // int indx = 1;
    int g= -1;
    int h= -1;
    int f_val = -1;

    std::vector<OpenListEntryLazy> openListStates;
    open_list->getFlattedOpenList(openListStates);
   
    std::vector<OpenListEntryLazy>::iterator it;
    for(it = openListStates.begin(); it != openListStates.end(); ++it)
    {
        // it = openListStates.begin();
        StateID sId = it->first;

        State s = g_state_registry->lookup_state(sId);
        SearchNode sNode = search_space.get_node(s);
        
        g = sNode.get_g(); 
        h = sNode.get_h();

        // if(m_debug_f_min)
        // {
        //     cout << indx++ <<"-  get_min_f: g=" << g << "  h=" <<h << "   f="<<g+h << endl;
        // }

        if(f_val == -1 || f_val > g+h)
            f_val = g+h;
    }
    return f_val;
}


void LazySearch::reward_progress() {
    // Boost the "preferred operator" open lists somewhat whenever
    open_list->boost_preferred();
}

void LazySearch::statistics() const {
    search_progress.print_statistics();
}

static SearchEngine *_parse(OptionParser &parser) {
    parser.document_synopsis("Lazy best first search", "");
    Plugin<OpenList<OpenListEntryLazy > >::register_open_lists();
    parser.add_option<OpenList<OpenListEntryLazy> *>("open", "open list");
    parser.add_option<bool>("reopen_closed",
                            "reopen closed nodes", "false");
    parser.add_list_option<Heuristic *>(
        "preferred",
        "use preferred operators of these heuristics", "[]");
    SearchEngine::add_options_to_parser(parser);
    Options opts = parser.parse();

    LazySearch *engine = 0;
    if (!parser.dry_run()) {
        engine = new LazySearch(opts);
        vector<Heuristic *> preferred_list =
            opts.get_list<Heuristic *>("preferred");
        engine->set_pref_operator_heuristics(preferred_list);
    }

    return engine;
}


static SearchEngine *_parse_greedy(OptionParser &parser) {
    parser.document_synopsis("Greedy search (lazy)", "");
    parser.document_note(
        "Open lists",
        "In most cases, lazy greedy best first search uses "
        "an alternation open list with one queue for each evaluator. "
        "If preferred operator heuristics are used, it adds an "
        "extra queue for each of these evaluators that includes "
        "only the nodes that are generated with a preferred operator. "
        "If only one evaluator and no preferred operator heuristic is used, "
        "the search does not use an alternation open list "
        "but a standard open list with only one queue.");
    parser.document_note("Equivalent statements using general lazy search",
         "\n```\n--heuristic h2=eval2\n"
         "--search lazy_greedy([eval1, h2], preferred=h2, boost=100)\n```\n"
         "is equivalent to\n"
         "```\n--heuristic h1=eval1 --heuristic h2=eval2\n"
         "--search lazy(alt([single(h1), single(h1, pref_only=true), single(h2),\n"
         "                  single(h2, pref_only=true)], boost=100),\n"
         "              preferred=h2)\n```\n"
         "------------------------------------------------------------\n"
         "```\n--search lazy_greedy([eval1, eval2], boost=100)\n```\n"
         "is equivalent to\n"
         "```\n--search lazy(alt([single(eval1), single(eval2)], boost=100))\n```\n"
         "------------------------------------------------------------\n"
         "```\n--heuristic h1=eval1\n--search lazy_greedy(h1, preferred=h1)\n```\n"
         "is equivalent to\n"
         "```\n--heuristic h1=eval1\n"
         "--search lazy(alt([single(h1), single(h1, pref_only=true)], boost=1000),\n"
         "              preferred=h1)\n```\n"
         "------------------------------------------------------------\n"
         "```\n--search lazy_greedy(eval1)\n```\n"
         "is equivalent to\n"
         "```\n--search lazy(single(eval1))\n```\n",
         true);

    parser.add_list_option<ScalarEvaluator *>("evals", "scalar evaluators");
    parser.add_list_option<Heuristic *>(
        "preferred",
        "use preferred operators of these heuristics", "[]");
    parser.add_option<bool>("reopen_closed",
                            "reopen closed nodes", "false");
    parser.add_option<int>(
        "boost",
        "boost value for alternation queues that are restricted "
        "to preferred operator nodes",
        OptionParser::to_str(DEFAULT_LAZY_BOOST));
    SearchEngine::add_options_to_parser(parser);
    Options opts = parser.parse();

    LazySearch *engine = 0;
    if (!parser.dry_run()) {
        vector<ScalarEvaluator *> evals =
            opts.get_list<ScalarEvaluator *>("evals");
        vector<Heuristic *> preferred_list =
            opts.get_list<Heuristic *>("preferred");
        OpenList<OpenListEntryLazy> *open;
        if ((evals.size() == 1) && preferred_list.empty()) {
            open = new StandardScalarOpenList<OpenListEntryLazy>(evals[0],
                                                                 false);
        } else {
            vector<OpenList<OpenListEntryLazy> *> inner_lists;
            for (int i = 0; i < evals.size(); i++) {
                inner_lists.push_back(
                    new StandardScalarOpenList<OpenListEntryLazy>(evals[i],
                                                                  false));
                if (!preferred_list.empty()) {
                    inner_lists.push_back(
                        new StandardScalarOpenList<OpenListEntryLazy>(evals[i],
                                                                      true));
                }
            }
            open = new AlternationOpenList<OpenListEntryLazy>(
                inner_lists, opts.get<int>("boost"));
        }
        opts.set("open", open);
        engine = new LazySearch(opts);
        engine->set_pref_operator_heuristics(preferred_list);
    }
    return engine;
}

static SearchEngine *_parse_weighted_astar(OptionParser &parser) {
    parser.document_synopsis(
        "(Weighted) A* search (lazy)",
        "Weighted A* is a special case of lazy best first search.");
    parser.document_note(
        "Open lists",
        "In the general case, it uses an alternation open list "
        "with one queue for each evaluator h that ranks the nodes "
        "by g + w * h. If preferred operator heuristics are used, "
        "it adds for each of the evaluators another such queue that "
        "only inserts nodes that are generated by preferred operators. "
        "In the special case with only one evaluator and no preferred "
        "operator heuristics, it uses a single queue that "
        "is ranked by g + w * h. ");
    parser.document_note("Equivalent statements using general lazy search",
        "\n```\n--heuristic h1=eval1\n"
        "--search lazy_wastar([h1, eval2], w=2, preferred=h1,\n"
        "                     bound=100, boost=500)\n```\n"
        "is equivalent to\n"
        "```\n--heuristic h1=eval1 --heuristic h2=eval2\n"
        "--search lazy(alt([single(sum([g(), weight(h1, 2)])),\n"
        "                   single(sum([g(), weight(h1, 2)]), pref_only=true),\n"
        "                   single(sum([g(), weight(h2, 2)])),\n"
        "                   single(sum([g(), weight(h2, 2)]), pref_only=true)],\n"
        "                  boost=500),\n"
        "              preferred=h1, reopen_closed=true, bound=100)\n```\n"
        "------------------------------------------------------------\n"
        "```\n--search lazy_wastar([eval1, eval2], w=2, bound=100)\n```\n"
        "is equivalent to\n"
        "```\n--search lazy(alt([single(sum([g(), weight(eval1, 2)])),\n"
        "                   single(sum([g(), weight(eval2, 2)]))],\n"
        "                  boost=1000),\n"
        "              reopen_closed=true, bound=100)\n```\n"
        "------------------------------------------------------------\n"
        "```\n--search lazy_wastar([eval1, eval2], bound=100, boost=0)\n```\n"
        "is equivalent to\n"
        "```\n--search lazy(alt([single(sum([g(), eval1])),\n"
        "                   single(sum([g(), eval2]))])\n"
        "              reopen_closed=true, bound=100)\n```\n"
        "------------------------------------------------------------\n"
        "```\n--search lazy_wastar(eval1, w=2)\n```\n"
        "is equivalent to\n"
        "```\n--search lazy(single(sum([g(), weight(eval1, 2)])), reopen_closed=true)\n```\n",
        true);

    parser.add_list_option<ScalarEvaluator *>("evals", "scalar evaluators");
    parser.add_list_option<Heuristic *>(
        "preferred",
        "use preferred operators of these heuristics", "[]");
    parser.add_option<bool>("reopen_closed", "reopen closed nodes", "true");
    parser.add_option<int>("boost",
                           "boost value for preferred operator open lists",
                           OptionParser::to_str(DEFAULT_LAZY_BOOST));
    parser.add_option<int>("w", "heuristic weight", "1");
    SearchEngine::add_options_to_parser(parser);
    Options opts = parser.parse();

    opts.verify_list_non_empty<ScalarEvaluator *>("evals");

    LazySearch *engine = 0;
    if (!parser.dry_run()) {
        vector<ScalarEvaluator *> evals = opts.get_list<ScalarEvaluator *>("evals");
        vector<Heuristic *> preferred_list =
            opts.get_list<Heuristic *>("preferred");
        vector<OpenList<OpenListEntryLazy> *> inner_lists;
        for (int i = 0; i < evals.size(); i++) {
            GEvaluator *g = new GEvaluator();
            vector<ScalarEvaluator *> sum_evals;
            sum_evals.push_back(g);
            if (opts.get<int>("w") == 1) {
                sum_evals.push_back(evals[i]);
            } else {
                WeightedEvaluator *w = new WeightedEvaluator(
                    evals[i],
                    opts.get<int>("w"));
                sum_evals.push_back(w);
            }
            SumEvaluator *f_eval = new SumEvaluator(sum_evals);

            inner_lists.push_back(
                new StandardScalarOpenList<OpenListEntryLazy>(f_eval, false));

            if (!preferred_list.empty()) {
                inner_lists.push_back(
                    new StandardScalarOpenList<OpenListEntryLazy>(f_eval,
                                                                  true));
            }
        }
        OpenList<OpenListEntryLazy> *open;
        if (inner_lists.size() == 1) {
            open = inner_lists[0];
        } else {
            open = new AlternationOpenList<OpenListEntryLazy>(
                inner_lists, opts.get<int>("boost"));
        }

        opts.set("open", open);

        engine = new LazySearch(opts);
        engine->set_pref_operator_heuristics(preferred_list);
    }
    return engine;
}

static SearchEngine *_parse_anytime_weighted_astar(OptionParser &parser) {
    parser.document_synopsis(
        "(Weighted) A* search (lazy)",
        "Weighted A* is a special case of lazy best first search.");
    parser.document_note(
        "Open lists",
        "In the general case, it uses an alternation open list "
        "with one queue for each evaluator h that ranks the nodes "
        "by g + w * h. If preferred operator heuristics are used, "
        "it adds for each of the evaluators another such queue that "
        "only inserts nodes that are generated by preferred operators. "
        "In the special case with only one evaluator and no preferred "
        "operator heuristics, it uses a single queue that "
        "is ranked by g + w * h. ");
    parser.document_note("Equivalent statements using general lazy search",
        "\n```\n--heuristic h1=eval1\n"
        "--search lazy_wastar([h1, eval2], w=2, preferred=h1,\n"
        "                     bound=100, boost=500)\n```\n"
        "is equivalent to\n"
        "```\n--heuristic h1=eval1 --heuristic h2=eval2\n"
        "--search lazy(alt([single(sum([g(), weight(h1, 2)])),\n"
        "                   single(sum([g(), weight(h1, 2)]), pref_only=true),\n"
        "                   single(sum([g(), weight(h2, 2)])),\n"
        "                   single(sum([g(), weight(h2, 2)]), pref_only=true)],\n"
        "                  boost=500),\n"
        "              preferred=h1, reopen_closed=true, bound=100)\n```\n"
        "------------------------------------------------------------\n"
        "```\n--search lazy_wastar([eval1, eval2], w=2, bound=100)\n```\n"
        "is equivalent to\n"
        "```\n--search lazy(alt([single(sum([g(), weight(eval1, 2)])),\n"
        "                   single(sum([g(), weight(eval2, 2)]))],\n"
        "                  boost=1000),\n"
        "              reopen_closed=true, bound=100)\n```\n"
        "------------------------------------------------------------\n"
        "```\n--search lazy_wastar([eval1, eval2], bound=100, boost=0)\n```\n"
        "is equivalent to\n"
        "```\n--search lazy(alt([single(sum([g(), eval1])),\n"
        "                   single(sum([g(), eval2]))])\n"
        "              reopen_closed=true, bound=100)\n```\n"
        "------------------------------------------------------------\n"
        "```\n--search lazy_wastar(eval1, w=2)\n```\n"
        "is equivalent to\n"
        "```\n--search lazy(single(sum([g(), weight(eval1, 2)])), reopen_closed=true)\n```\n",
        true);

    parser.add_list_option<ScalarEvaluator *>("evals", "scalar evaluators");
    parser.add_list_option<Heuristic *>(
        "preferred",
        "use preferred operators of these heuristics", "[]");
    parser.add_option<bool>("reopen_closed", "reopen closed nodes", "true");
    parser.add_option<int>("boost",
                           "boost value for preferred operator open lists",
                           OptionParser::to_str(DEFAULT_LAZY_BOOST));
    parser.add_option<int>("w", "heuristic weight", "1");
    parser.add_option<double>("delta", "PAC delta", "0");
    parser.add_option<double>("epsilon", "PAC epsilon", "0");
    parser.add_option<int>("trivial_pac", "Trivial PAC Condition", "0");
    parser.add_option<int>("ratio_based", "Ratio Based PAC Condition", "0");
    parser.add_option<int>("rpac_lower_bound", "Ratio Based PAC Condition + LowerBound", "0");
    parser.add_option<int>("rpac_open_based", "Open Based PAC Condition", "0");
    parser.add_option<string>("heuristic_func", "The name of the heuristic function in use", "0");
    SearchEngine::add_options_to_parser(parser);
    Options opts = parser.parse();

    opts.verify_list_non_empty<ScalarEvaluator *>("evals");

    LazySearch *engine = 0;


    if (!parser.dry_run()) {
        vector<ScalarEvaluator *> evals = opts.get_list<ScalarEvaluator *>("evals");
        vector<ScalarEvaluator *> evals_for_anytime = opts.get_list<ScalarEvaluator *>("evals");
        
        vector<Heuristic *> preferred_list =
            opts.get_list<Heuristic *>("preferred");

        vector<OpenList<OpenListEntryLazy> *> inner_lists;

        for (int i = 0; i < evals.size(); i++) {
            GEvaluator *g = new GEvaluator();
            GEvaluator *g_for_anytime = new GEvaluator();
            vector<ScalarEvaluator *> sum_evals;
            vector<ScalarEvaluator *> sum_evals_for_anytime;
            sum_evals.push_back(g);

            if (opts.get<int>("w") == 1) {
                sum_evals.push_back(evals[i]);
            } else {
                WeightedEvaluator *w = new WeightedEvaluator(
                    evals[i],
                    opts.get<int>("w"));
                sum_evals.push_back(w);
            }
            SumEvaluator *f_eval = new SumEvaluator(sum_evals);
            sum_evals_for_anytime.push_back(g_for_anytime);
            sum_evals_for_anytime.push_back(evals[i]);
            SumEvaluator *f_eval_for_anytime = new SumEvaluator(sum_evals_for_anytime);

            inner_lists.push_back(
                new StandardScalarOpenListForAnyTime<OpenListEntryLazy>(f_eval, f_eval_for_anytime, false));

            if (!preferred_list.empty()) {
                inner_lists.push_back(
                    new StandardScalarOpenListForAnyTime<OpenListEntryLazy>(f_eval, f_eval_for_anytime, true));
            }

        }


        OpenList<OpenListEntryLazy> *open;
       
        if (inner_lists.size() == 1) {
            open = inner_lists[0];
        } else {
            open = new AlternationOpenList<OpenListEntryLazy>(
                inner_lists, opts.get<int>("boost"));
        }

        
        opts.set("open", open);
        opts.setIsAnyTime(true); //TODO coding convention - add "is_any_time" as a description to the function

        engine = new LazySearch(opts);
        engine->set_pref_operator_heuristics(preferred_list);

        //read the PAC data
        engine->FillPACInfo();

        double      pac_delta = opts.get<double>("delta");
        double      pac_epsilon = opts.get<double>("epsilon");
        int         is_trivial_pac = opts.get<int>("trivial_pac");
        int         is_ratio_based = opts.get<int>("ratio_based");
        int         is_lower_bound = opts.get<int>("rpac_lower_bound");
        int         is_rpac_open_based = opts.get<int>("rpac_open_based");
        std::string is_running_admissible_heuristic = opts.get<std::string>("heuristic_func");

        engine->InitPacVariables(pac_epsilon, pac_delta, is_lower_bound, is_rpac_open_based,is_trivial_pac,is_ratio_based,is_running_admissible_heuristic);
        
    }
    return engine;
}


void LazySearch::InitPacVariables(double epsilon, double delta, int is_lower_bound,int is_rpac_open_based, int is_trivial_pac, int is_ratio_based, std::string is_running_admissible_heuristic)
{
    
    cout << "INFO: InitPacVariables" << std::endl;

     cout << "is_rpac_open_based = [" << is_rpac_open_based << "]" << endl;
     cout << "is_lower_bound = [" << is_lower_bound << "]" << endl;
     m_is_running_trivial_pac           = is_trivial_pac != 0;
     m_is_running_ratio_based_pac       = is_ratio_based != 0;
     m_is_running_RPac_Lower_Bound      = is_lower_bound != 0;
     m_is_running_open_based_pac        = is_rpac_open_based != 0;
     m_max_f_min                        = 0;
     m_pac_epsilon                      = epsilon;
     // delta                           = 100 - (int)(delta * 100); // old version
     m_pac_delta                        = delta  ;
     m_open_based_P_hat                 = 0.0; //init P accumulator
     m_last_f_val                       = 0;
     m_debug_f_min                      = true;
     m_is_running_admissible_heuristic  = is_running_admissible_heuristic != "ff"; // GAL: TEMP - suppose to come from the initiate script

     cout << "m_is_running_trivial_pac = [" << m_is_running_trivial_pac << "]" << endl;
     cout << "m_is_running_ratio_based_pac = [" << m_is_running_ratio_based_pac << "]" << endl;
     cout << "m_is_running_open_based_pac = [" << m_is_running_open_based_pac << "]" << endl;
     cout << "m_is_running_RPac_Lower_Bound = [" << m_is_running_RPac_Lower_Bound << "]" << endl;
     cout << "delta = [" << delta << "]" << endl;
     cout << "1- delta = [" << 1 - delta << "]" << endl;
     cout << "log(1- delta) = [" << log(1 - delta) << "]" << endl;

     bool found = false;
     std::map<float, float>::const_iterator iter = m_ratio_to_statistics_for_pac.begin();
     for (; iter != m_ratio_to_statistics_for_pac.end();++iter)
     {
        if (iter->second > m_pac_delta * 100)
        {
            found = true;
            break;
        }
     }
     if (found)
        m_pac_ratio_h = (--iter)->first;
     else
        m_pac_ratio_h = 1000;

     cout << "PAC Variables:" << std::endl;
     cout << "pac_epsilon: " << m_pac_epsilon << std::endl;
     cout << "pac_ratio_h: " << m_pac_ratio_h <<  std::endl;
     cout << "pac_probability: " << m_pac_delta << std::endl;

}

/*

Pr(  (U / (1+epsilon)) <= h*(S) ) >= 1 - delta
after manipulation:
Pr(  (U / (1+epsilon)) > h*(S) ) < 1 - delta
*/
bool LazySearch::is_Trivial_PAC_Condition_satisfied()
{
    if(current_g >= f_incumbent)
    {
        return false;
    }

    cout << "INFO: is_Trivial_PAC_Condition_satisfied"<< std::endl;

    double prob = 0;
    double U = f_incumbent;
    double error = 1 + m_pac_epsilon;
    double right = U / error;

    cout << "******  is_Trivial_PAC_Condition_satisfied    ******" << endl;
    // find the probability
    std::map<float, float>::const_iterator iter = m_hstar_statistics_for_trivial_pac.begin();
 
    // cout<< "(iter->first)=" <<(iter->first) << endl;
    while(iter != m_hstar_statistics_for_trivial_pac.end() && iter->first < right)
    {
         ++iter;
         // cout<< "(iter->first)=" <<(iter->first) << endl;
    }
    if(iter == m_hstar_statistics_for_trivial_pac.end())
    { // in case of the solution is bigger than the max cost in the statistics (from preprocess) 
        prob = 1;
    }
    else
    {
        prob = iter->second /100;
    }

    cout<<
        "   rihgt = "        << right << endl <<
        "   prob = "         << prob << endl <<
        "   U = "            << U << endl <<
        "   m_Initial_H = "  << m_Initial_H << endl <<
        "   error = "        << error << endl <<
        "   delta = "        << (m_pac_delta) << endl <<
    endl;

    bool ret = prob < m_pac_delta;
    cout << "INFO: is_Trivial_PAC_Condition_satisfied? "<< ret << std::endl;

    return ret;

}



/*
the ratio based pac condition is:
Pr(h*\h(S) >= U/(h(s)*(1+epsilon)) ) >= 1 - delta
*/
bool LazySearch::is_Ratio_PAC_Condition_satisfied()
{
    if(current_g >= f_incumbent)
    {
        return false;
    }

    cout << "INFO: is_Ratio_PAC_Condition_satisfied"<< std::endl;

    double prob = 0;
    double U = f_incumbent;
    double error = 1 + m_pac_epsilon;
    double right = U / (m_Initial_H * error);

    cout << "******  is_Ratio_PAC_Condition_satisfied    ******" << endl;
    // find the probability
    std::map<float, float>::const_iterator iter = m_ratio_to_statistics_for_pac.begin();
    cout<< "(iter->first)=" <<(iter->first) << endl;
    while(iter != m_ratio_to_statistics_for_pac.end() && iter->first < right)
    {
         ++iter;
         // cout<< "(iter->first)=" <<(iter->first) << endl;
    }

    if(iter == m_ratio_to_statistics_for_pac.end())
    { // in case of the solution is bigger than the max cost in the statistics (from preprocess) 
        prob = 1;
    }
    else
    {
        prob = iter->second /100;
    }

    cout<<
        "   rihgt = "        << right << endl <<
        "   prob = "         << prob << endl <<
        "   U = "            << U << endl <<
        "   m_Initial_H = "  << m_Initial_H << endl <<
        "   error = "        << error << endl <<
        "   1- delta = "     << (1-m_pac_delta) << endl <<
    endl;

    bool ret = prob < m_pac_delta;
    cout << "INFO: is_Ratio_PAC_Condition_satisfied? "<< ret << std::endl;

    return ret;

}

/*
  | max F_min       h_star(s)          U            |
Pr| ---------   <=  --------   <   ---------------- |
  |   h(s)            h(s)          h(s)(1+epsilon) |
*/
bool LazySearch::is_Ratio_PAC_Condition_Lower_Bound_satisfied()
{
    if(current_g >= f_incumbent)
    {
        return false;
    }

    // if f_val is lower than max(f_min) it cannot be max(f_min)
    // therfore - return false - RPAC+LB is not satisfied 

    if(f_incumbent <=0 || f_incumbent < m_max_f_min)
        return false;

    double prob = 0;
    double U = f_incumbent;
    double error = 1 + m_pac_epsilon;
    double right = U / (m_Initial_H * error);

    // cout << "U / (m_Initial_H * error) = " << U << "/(" << m_Initial_H << " * " << error << ") = "<< right << endl;
    // cout << "m_max_f_min / m_Initial_H = " << f_min << "/" << m_Initial_H <<" = " << left << endl;

//    cout << "-----------   U=" << U <<
//            ", h_s= " << m_Initial_H <<
//            ", m_max_f_min=" << m_max_f_min <<
//            ", current_g=" << current_g <<
//            ", U/m_max_f_min=" << U/m_max_f_min <<
//            ", U / (m_Initial_H * error)=" << U / (m_Initial_H * error) <<
//            ", 1 + epsilon=" << m_pac_epsilon +1 << endl;


    std::map<float, float>::const_iterator iter = m_ratio_to_statistics_for_pac.begin();
 
    while(iter != m_ratio_to_statistics_for_pac.end() && (iter->first) < right)
    {
         ++iter;
    }

    if(iter != m_ratio_to_statistics_for_pac.begin())
    {
        prob = (--iter)->second /100;
    }
    else
    {
        prob = iter->second /100;
    }


    bool ret = prob < m_pac_delta;
    cout << "-----prob[" << prob << "] <? pac_delta[" << m_pac_delta <<"] = " << ret << endl;
    return ret;
}


/*
----
\
 \                h*[   ]       1    [     U                ]
 /   Log(1 - Pr( ---| S | <  ------- |----------  - g_node  | ))  >= Log(1-delta)
/                 h [   ]     h_node [ 1+epsilon            ]
----
*/

bool LazySearch::is_Ratio_PAC_Condition_Open_Based_satisfied()
{
    if(current_g >= f_incumbent)
    {
        return false;
    }

    double log_delta = log(1 - m_pac_delta );
    bool flag = (m_open_based_P_hat >= log_delta) && (m_infinity_nodes_counter == 0);

    if(flag) {
        cout<<
                "   U = "            << f_incumbent << endl <<
                "   log(1- delta) = "     << log_delta << endl <<
                "   flag = "     << flag << endl <<
                "   m_open_based_P_hat = "     << m_open_based_P_hat << endl <<
                "   m_infinity_nodes_counter = "     << m_infinity_nodes_counter << endl << endl;
    }

    return flag;

}

void LazySearch::FillPACInfo()
{
    if (!m_is_anytime)
        return;

    // read commulative h-star (no ratio related) - only for trivial PAC condition
    if (!read_stats_file("PAC_Commulative_hstar.csv", m_hstar_statistics_for_trivial_pac)) {
        std::cout << " ERROR: failed to read " << "PAC_Commulative_h-ff_to_h-star.csv" << std::endl;
    }

    if(!read_PAC_statistics_csv("PAC_Statistics.csv", m_PAC_statistics))
    {
        std::cout << " ERROR: failed to read " << "PAC_Statistics.csv" << std::endl;
    }


    if(m_is_running_admissible_heuristic) {
        // in casee of using FF heuristic
        std::string filename = "PAC_Commulative_h-ff_to_h-star.csv";
        std::cout << filename.c_str() << std::endl;
        if (!read_stats_file(filename, m_ratio_to_statistics_for_pac)) {
            std::cout << " ERROR: failed to read " << filename.c_str() << std::endl;
        }
    } else{
        // in case of using lm-cat
        std::string filename = "PAC_Commulative_ratio.csv" ;
        if (!read_stats_file(filename, m_ratio_to_statistics_for_pac)) {
            std::cout << " ERROR: faile dto read " << filename.c_str() << std::endl;
        }
    }

    std::cout << "************************************************************************************" << std::endl << "inadmissible_statistics_for_pac" <<std::endl;
    for (std::map<float, float>::const_iterator iter = m_inadmissible_statistics_for_pac.begin(); iter != m_inadmissible_statistics_for_pac.end();iter++) {
        std::cout << "map[" << iter->first << "] = " << iter->second << std::endl;
    }

    std::cout << "************************************************************************************" << std::endl << "Ratio" << std::endl;
    for (std::map<float, float>::const_iterator iter = m_ratio_to_statistics_for_pac.begin(); iter != m_ratio_to_statistics_for_pac.end();iter++) {
        std::cout << "map[" << iter->first << "] = " << iter->second << std::endl;
    }

    std::cout << "************************************************************************************" << std::endl << "PAC_statistics" << std::endl;
    for (std::map<std::string, std::map<std::string, float> >::const_iterator iter = m_PAC_statistics.begin(); iter != m_PAC_statistics.end();iter++)
    {
        std::cout << iter->first << ":" << iter->second.at("optSol");
//        for (std::map<std::string, float>::const_iterator inner_iter = iter->second.begin(); inner_iter != iter->second.end();inner_iter++)
//        {
//            std::cout << " map[" << inner_iter->first << "] = " << inner_iter->second << ",";
//        }
        std::cout << std::endl;
    }
    std::cout << "************************************************************************************" << std::endl;
}

bool LazySearch::read_stats_file(std::string filename, std::map<float, float> & stats)
{
    ifstream file_hstar ( filename.c_str() );
    string hstar;
    string presentage;
    while ( file_hstar.good() )
    {
        getline ( file_hstar, hstar, ',' );
        getline ( file_hstar, presentage, '\n' );
        if (atof(hstar.c_str()) != 0)
            stats[atof(hstar.c_str())] = atof(presentage.c_str());

    }

    return true;
}

bool LazySearch::read_PAC_statistics_csv(std::string filename, std::map<std::string, std::map<std::string, float> > & stats) // problem -> [parameter-name -> value]
{
    ifstream file_hstar ( filename.c_str() );
    string prob;
    string isSolved;
    string optSol;
    string h_ff;
    string h;
    string h_star_to_h;
    while ( file_hstar.good() )
    {
        getline ( file_hstar, prob, ',' );
        getline ( file_hstar, isSolved, ',' );
        getline ( file_hstar, optSol, ',' );
        getline ( file_hstar, h_ff, ',' );
        getline ( file_hstar, h, ',' );
        getline ( file_hstar, h_star_to_h, '\n' );

        std::map<std::string, float> valuesMap;
        valuesMap["isSolved"] = atof(isSolved.c_str());
        valuesMap["optSol"] = atof(optSol.c_str());
        valuesMap["h_ff"] = atof(h_ff.c_str());
        valuesMap["h"] = atof(h.c_str());
        valuesMap["h_star_to_h"] = atof(h_star_to_h.c_str());

        stats[prob] = valuesMap;


    }

    return true;
}

static Plugin<SearchEngine> _plugin("lazy", _parse);
static Plugin<SearchEngine> _plugin_greedy("lazy_greedy", _parse_greedy);
static Plugin<SearchEngine> _plugin_weighted_astar("lazy_wastar", _parse_weighted_astar);
static Plugin<SearchEngine> _plugin_anytime_weighted_astar("lazy_anytime_wastar", _parse_anytime_weighted_astar);
