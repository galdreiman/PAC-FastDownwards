#ifndef OPEN_LISTS_STANDARD_SCALAR_OPEN_LIST_H
#define OPEN_LISTS_STANDARD_SCALAR_OPEN_LIST_H

#include "open_list.h"
#include "../option_parser.h"

#include <deque>
#include <map>
#include <vector>
#include <utility>

class ScalarEvaluator;

template<class Entry>
class StandardScalarOpenList : public OpenList<Entry> {
protected:   
    typedef std::deque<Entry> Bucket;
    std::map<int, Bucket> buckets;
    int size;

    ScalarEvaluator *evaluator;
    int last_evaluated_value;
    int last_preferred;
    bool dead_end;
    bool dead_end_reliable;


    ScalarEvaluator *get_evaluator() {return evaluator; }

public:

    StandardScalarOpenList(const Options &opts);
    StandardScalarOpenList(ScalarEvaluator *eval,
                           bool preferred_only);
    ~StandardScalarOpenList();

    int insert(const Entry &entry);
    Entry remove_min(std::vector<int> *key = 0);
    bool empty() const;
    void clear();

    void evaluate(int g, bool preferred);
    bool is_dead_end() const;
    bool dead_end_is_reliable() const;
    void get_involved_heuristics(std::set<Heuristic *> &hset);
    std::map<int, Bucket> get_buckets(){return buckets;}

    static OpenList<Entry> *_parse(OptionParser &parser);
    
    virtual void getFlattedOpenList(std::vector<Entry> &res);


};


// HACK! Need a better strategy of dealing with templates, also in the Makefile.
template<class Entry>
class StandardScalarOpenListForAnyTime : public StandardScalarOpenList<Entry> {
private:
    ScalarEvaluator *anytime_evaluator;
protected:
    ScalarEvaluator *get_anytime_evaluator() {return anytime_evaluator; }
public:

    StandardScalarOpenListForAnyTime(ScalarEvaluator *eval,
                           ScalarEvaluator *eval_for_anytime, 
                           bool preferred_only);

    int evaluate_for_anytime(int g, bool preferred);

    // int get_anytime_evaluation() {return get_anytime_evaluator()->get_value();}
    // int get_regular_evaluation() {return get_evaluator()->get_value();}




};

#include "standard_scalar_open_list.cc"





#endif
