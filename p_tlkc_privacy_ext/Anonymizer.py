import os
import sys

from p_tlkc_privacy_ext import MFS, ELReps, MVS


class Anonymizer:

    def __init__(self):
        self = self

    def none_relative_type(self, log, log2, sensitive_att, cont, l, k, c, dict1, spectime, trace_attributes, life_cycle,
                           all_life_cycle, bk_type, alpha, beta, utility_measure, multiprocess, mp_technique):
        repres = ELReps.ELReps(log)
        # log is simplified with the sensitive attribute
        logsimple, traces, sensitives = repres.create_simple_log(bk_type, trace_attributes, life_cycle,
                                                                 all_life_cycle, sensitive_att,
                                                                 time_accuracy='seconds')

        relative_freq = repres.get_relative_freq(traces,utility_measure)
        # analyze what this does
        mvs = MVS.MVS(traces, logsimple, sensitive_att, cont, sensitives, bk_type, dict_safe=dict1)
        violating, dict1 = mvs.mvs(l, k, c, multiprocess, mp_technique)
        violating_length = len(violating.copy())
        # from docu:
        # select event node e that has the highest score to suppress based on some score function
        # delete all MVTs and MFTs containing the event e
        # update the score function for all remaining events in MVT
        # add e to suppression set
        # suppress all e from the event log
        # what is suppression?
        # ---- here something needs to happen before traces get removed (before or after suppression set) ---- 
        # or with violating?
        suppression_set = repres.suppression_new(violating, relative_freq, alpha, beta)
        traces_removed, max_removed = repres.suppress_traces(logsimple.copy(), suppression_set)
        log_count = {t: None for t in spectime}
        d_count = {t: None for t in spectime}
        d_l_count = {t: None for t in spectime}
        for t in spectime:
            traces_removed_copy = traces_removed.copy()
            repres = ELReps.ELReps(log2[t])
            log_count[t], d_count[t], d_l_count[t] = repres.createEventLog(traces_removed_copy, t, trace_attributes,
                                                                           life_cycle,
                                                                           all_life_cycle, bk_type, sensitive_att,
                                                                           time_accuracy='seconds')
        return log_count, violating_length, d_count, d_l_count, dict1, max_removed


    def relative_type(self, log, sensitive_att, cont, t, l, k, c, dict1, trace_attributes, life_cycle, all_life_cycle,
                  bk_type, alpha, beta, utility_measure, multiprocess, mp_technique):
        repres = ELReps.ELReps(log)
        logsimple, traces, sensitives = repres.create_simple_log(bk_type, trace_attributes, life_cycle, all_life_cycle,
                                                                 sensitive_att, time_accuracy=t)

        relative_freq = repres.get_relative_freq(traces, utility_measure)
        mvs = MVS.MVS(traces, logsimple, sensitive_att, cont, sensitives, bk_type, dict_safe=dict1)
        # try:
        violating_time, dict1 = mvs.mvs(l, k, c, multiprocess, mp_technique, t)
        # except Exception as e:
        #     print(e)
        #     if multiprocess:
        #         sys.exit(
        #             "If you are using multiprocessing, the main function needs to be indicated! Use (if __name__ == '__main__':)")

        violating_length_time = len(violating_time.copy())
        # ---- here something needs to happen before traces get removed ---- 
        suppression_set = repres.suppression_new(violating_time, relative_freq, alpha, beta)
        traces_removed, max_removed = repres.suppress_traces(logsimple, suppression_set)
        log_time, d_time, d_l_time = repres.createEventLog(traces_removed, t, trace_attributes, life_cycle, all_life_cycle,
                                                           bk_type, sensitive_att, time_accuracy=t)
        return log_time, violating_length_time, d_time, d_l_time, dict1, max_removed
