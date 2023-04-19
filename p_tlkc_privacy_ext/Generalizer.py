import json

class Generalizer():

    def __init__(self, log):
        self.log = log

    #TODO: test if this works with more layers in the tree
    def generalize_attribute(self, trace_attribute):
        extracted_attribute = trace_attribute[0]

        with open("generalization_config.json", "r") as f:
            config = json.load(f)

        def search_for_attribute(attribute, subtree):
            """
            Recursive helper function to search for an attribute in a subtree of the configuration file.
            """
            if attribute in subtree:
                return True, subtree
            else:
                for parent, child in subtree.items():
                    found, subsubtree = search_for_attribute(attribute, child)
                    if found:
                        return True, subsubtree

            return False, {}

        #TODO: replace org:group with a generic term
        found, subtree = search_for_attribute(extracted_attribute, config["org:group"])

        if found:
            if extracted_attribute in subtree:
                #TODO: replace org:group with a generic term
                for parent, child in config["org:group"].items():
                    if subtree == child:
                        new_attribute = parent
                        break
            else:
                for parent, child in subtree.items():
                    if extracted_attribute in child:
                        new_attribute = parent
                        break
        else:
            new_attribute = None

        return new_attribute

    def generalize_traces(self, logsimple, suppression_set):
        max_removed = 0

        for key in logsimple.keys():
            list_trace = logsimple[key]['trace']
            generalized_traces = self.generalize(list_trace, suppression_set)
            logsimple[key]['trace'] = generalized_traces
        return logsimple, max_removed
    
    def generalize(self, list_trace, violating_list):
        for i, trace in enumerate(list_trace):
            for violating_event in violating_list:
                if violating_event == trace:
                    generalized_event = self.generalize_attribute(violating_event)
                    updated_trace = self.update_trace(trace, violating_event, generalized_event)
                    list_trace[i] = updated_trace
        return list_trace

    def update_trace(self, trace, old_event, new_event):
        tuple_from_event = (new_event, 0)
        if trace == old_event:
            return tuple_from_event
        else:
            return trace