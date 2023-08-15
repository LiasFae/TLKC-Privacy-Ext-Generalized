from p_tlkc_privacy_ext.privacyPreserving import privacyPreserving
import os

if __name__ == '__main__':
    event_log = "Sepsis-Cases-Case-attributes.xes" # enter the event log to be anonymized here
    L = [2]
    K = [20]
    C = [0.5]
    alpha = 0.5  # privacy coefficent
    beta = 0.5  # utility coefficent
    event_in_log = 0.5 # frequency in the whole log
    event_in_variant = 0.5 # frequency in traces
    utility_measure = [event_in_log,event_in_variant]
    sensitive_att = ['Diagnose']  # categorical sensitive attributes
    T = ["minutes"]  # original, seconds, minutes, hours, days
    cont = []  # numerical sensitive attributes
    bk_type = "set"  # set, multiset, sequence, relative
    event_attributes = ['concept:name']  # to simplify the event log, containing the attribute to be anonymized
    life_cycle = ['complete', '', 'COMPLETE']  # these life cycles are applied only when all_lif_cycle = False
    all_life_cycle = True  # when life cycle is in trace attributes then all_life_cycle has to be True
    pa_log_dir = "./xes_results" # directory for output results
    pa_log_name = event_log[:-4]
    multiprocess = False  # if you want to you use multiprocessing
    mp_technique = 'pool' # pool, queue
    # --- Generalizer Add-On ---
    generalising = True # True to use generalization, False for suppression
    generalising_max_iterations = 20 # safety measure for aborting generalization
    generalization_type = "sibling" # sibling, genAndSup
    gen_config = "generalization_config_sepsis.json" # load your generalization tree here
    # Generalizer Add-On End ---
    if not os.path.exists(pa_log_dir):
        os.makedirs(pa_log_dir)
    pp = privacyPreserving(event_log)
    privacy_aware_log_dir, max_removed = pp.apply(T, L, K, C, sensitive_att, cont, generalising, generalization_type, generalising_max_iterations, gen_config, bk_type, event_attributes, life_cycle, all_life_cycle,
                                   alpha, beta, pa_log_dir, pa_log_name, False, utility_measure=utility_measure, multiprocess=multiprocess, mp_technique=mp_technique)
    