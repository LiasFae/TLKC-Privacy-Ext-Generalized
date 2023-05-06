import json

class Generalizer():

    def __init__(self, log):
        self.log = log

    def generalize_attribute(self, trace_attribute, bk_type):
        if bk_type !='multiset':
            extracted_attribute = trace_attribute[0]
        else:
            extracted_attribute = trace_attribute

        new_attribute = ""

        with open("generalization_config.json", "r") as f:
            config = json.load(f)

        def search_for_attribute(attribute, subtree, parent):
            """
            Recursive helper function to search for an attribute in a subtree of the configuration file.
            """
            parent_attribute = ""
            if attribute in subtree:
                parent_attribute = parent
                return True, subtree, parent_attribute
            else:
                for parent, child in subtree.items():
                    found, subsubtree, parent_attribute = search_for_attribute(attribute, child, parent)
                    if found:
                        return True, subsubtree, parent_attribute

            return False, {}, parent_attribute

        found, subtree, new_attribute = search_for_attribute(extracted_attribute, config, "")
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
                    generalized_event = self.generalize_attribute(violating_event, bk_type="irrelevant")
                    updated_trace = self.update_trace(trace, violating_event, generalized_event)
                    list_trace[i] = updated_trace  
        return list_trace

    def update_trace(self, trace, old_event, new_event):
        tuple_from_event = (new_event, old_event[1])
        if trace == old_event:
            return tuple_from_event
        else:
            return trace
        
    def add_siblings(self, suppression_set):
        updated_suppression_set = suppression_set

        with open("generalization_config.json", "r") as f:
            config = json.load(f)

        for violating_event in suppression_set:
            #find siblings and if they are not in violating_list already, also generalize them
            def find_sibling_node(attribute, subtree):
                """
                Recursive helper function to search for an attribute in a subtree of the configuration file.
                """
                if attribute in subtree:
                    return True, subtree
                else:
                    for parent, child in subtree.items():
                        found, subsubtree = find_sibling_node(attribute, child)
                        if found:
                            return True, subsubtree

                return False, {}
            extracted_attribute = violating_event[0]
            found, subtree = find_sibling_node(extracted_attribute, config)
            if subtree is None:
                continue
            else:
                for key in subtree.keys():
                    if key == extracted_attribute: #skip original attribute itself
                        continue
                    elif key in [vl[0] for vl in suppression_set]: #skip key if already in suppression set
                        continue
                    else:
                        tuple_from_key = (key, violating_event[1])
                        updated_suppression_set.append(tuple_from_key)

        return updated_suppression_set