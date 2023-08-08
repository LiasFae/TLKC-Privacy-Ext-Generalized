from pm4py.algo.discovery.inductive import factory as inductive_miner
from pm4py.evaluation.replay_fitness import factory as replay_factory
from pm4py.evaluation.precision import factory as precision_factory
from pm4py.statistics.traces.log import case_statistics
from pm4py.evaluation.replay_fitness import factory as replay_fitness_factory
from pm4py.algo.conformance.alignments import factory as align_factory


class Results():
    def __init__(self):
        pass

    def results_log(self, log_annon, log):
        net, initial_marking, final_marking = inductive_miner.apply(log_annon)
        fitness = replay_factory.apply(log, net, initial_marking, final_marking)#["log_fitness"]
        precision = precision_factory.apply(log, net, initial_marking, final_marking)
        #alignments = align_factory.apply_log(log, net, initial_marking, final_marking)
        #log_fitness = replay_fitness_factory.evaluate(alignments, variant="alignments")
        #perc_fit_tr = log_fitness["percFitTraces"]
        average_fitness = fitness["averageFitness"]
        var_with_count = case_statistics.get_variant_statistics(log_annon)
        activ1 = {""}
        for el in var_with_count:
            el['variant'] = el['variant'].split(',')
            activ1.update(el['variant'])
        activ1.remove("")
        activ = len(activ1)
        variants = sum([1 for x in var_with_count])
        if (precision + average_fitness != 0):
            f1_score = 2 * precision * average_fitness / (precision + average_fitness)
        else:
            f1_score = 0
        perc_fit_tr = 0
        return fitness, precision, perc_fit_tr, average_fitness, activ, variants, activ1, f1_score
