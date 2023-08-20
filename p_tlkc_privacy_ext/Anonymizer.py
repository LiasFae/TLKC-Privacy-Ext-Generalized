from p_tlkc_privacy_ext import ELReps, MVS, Generalizer


class Anonymizer:

    def __init__(self):
        self = self

    def none_relative_type(self, log, log2, sensitive_att, cont, l, L, k, K, c, C, dict1, spectime, trace_attributes, life_cycle,
                           all_life_cycle, generalising, generalization_type, generalising_max_iterations, gen_config, bk_type, 
                           alpha, beta, utility_measure, multiprocess, mp_technique):
        
        gen_loop = 1
        use_log_count= False

        while True:     
            dict1 = {
                l: {k: {c: {"w": [], "x": [], "v": []} for c in C} for k in K}
                for l in range(0, L[len(L) - 1] + 1)}       
            if use_log_count:
                log_modified = list(log_count.values())[0]
                log2_modified = log_count.copy()
                repres = ELReps.ELReps(log_modified)
            else:
                repres = ELReps.ELReps(log)

            logsimple, traces, sensitives = repres.create_simple_log(bk_type, trace_attributes, life_cycle,
                                                                    all_life_cycle, sensitive_att,
                                                                    time_accuracy='seconds')
            relative_freq = repres.get_relative_freq(traces,utility_measure)
            mvs = MVS.MVS(traces, logsimple, sensitive_att, cont, sensitives, bk_type, dict_safe=dict1)
            violating, dict1 = mvs.mvs(l, k, c, multiprocess, mp_technique)
            violating_length = len(violating.copy())
            suppression_set = repres.suppression_new(violating, relative_freq, alpha, beta, generalising, gen_config)
            if generalising:
                generalize = Generalizer.Generalizer()
                if generalization_type == "sibling":
                    suppression_set_with_siblings, sibling_subtrees = generalize.add_siblings(suppression_set, gen_config)
                    traces_removed, max_removed, replacement_list = generalize.generalize_traces_with_siblings(logsimple.copy(), gen_config, generalization_type, suppression_set_with_siblings, sibling_subtrees)
                elif generalization_type == "genAndSup":
                    traces_removed, max_removed, replacement_list = generalize.generalize_traces_with_suppression(logsimple.copy(), gen_config, generalization_type, suppression_set)
                else:
                    print("Generalization type must be one of the pre-defined values. Will continue with suppression instead.")
                    replacement_list = []
                    traces_removed, max_removed = repres.suppress_traces(logsimple.copy(), suppression_set)
            else:
                # Classic Suppression
                replacement_list = []
                traces_removed, max_removed = repres.suppress_traces(logsimple.copy(), suppression_set)
            log_count = {t: None for t in spectime}
            d_count = {t: None for t in spectime}
            d_l_count = {t: None for t in spectime}
            for t in spectime:
                traces_removed_copy = traces_removed.copy()
                if use_log_count:
                    repres = ELReps.ELReps(log2_modified[t])
                else:
                    repres = ELReps.ELReps(log2[t])
                log_count[t], d_count[t], d_l_count[t] = repres.createEventLog(traces_removed_copy, generalising, replacement_list, t, trace_attributes,
                                                                            life_cycle,
                                                                            all_life_cycle, bk_type, sensitive_att,
                                                                            time_accuracy='seconds')
            gen_loop += 1
            if not generalising or gen_loop > generalising_max_iterations or suppression_set==[]:
                break

            use_log_count = True
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
        suppression_set = repres.suppression_new(violating_time, relative_freq, alpha, beta)
        traces_removed, max_removed = repres.suppress_traces(logsimple, suppression_set)
        log_time, d_time, d_l_time = repres.createEventLog(traces_removed, t, trace_attributes, life_cycle, all_life_cycle,
                                                           bk_type, sensitive_att, time_accuracy=t)
        return log_time, violating_length_time, d_time, d_l_time, dict1, max_removed
