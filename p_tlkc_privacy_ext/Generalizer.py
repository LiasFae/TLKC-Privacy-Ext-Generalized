import json

class Generalizer():

    def __init__(self):
        self=self

    def generalize_attribute(self, trace_attribute, gen_config):
        extracted_attribute = trace_attribute[0]

        new_attribute = ""

        with open(gen_config, "r") as f:
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

    def generalize_traces_with_siblings(self, logsimple, gen_config, generalization_type, generalization_set, sibling_subtrees):
        replacement_list = []
        max_removed = 0
        count = 0
        count2 = 0
        # count < 20 is a safety measure
        while sibling_subtrees and count < 20:
            generalization_set, sibling_subtrees = self.find_lowest_elements_from_subtrees(sibling_subtrees, generalization_set, logsimple)
            count += 1
        found = True
        while found and count2 <20:
            count2 += 1
            found = False
            for key in logsimple.keys():
                list_trace = logsimple[key]['trace']
                generalized_traces, replacement_list = self.generalize(list_trace, gen_config, generalization_type, generalization_set, replacement_list)
                logsimple[key]['trace'] = generalized_traces
            for violating_event in generalization_set:
                for key in logsimple.keys():
                    list_trace2 = logsimple[key]['trace']
                    if violating_event in list_trace2:
                        found = True
                        break
                if found:
                    break    
        return logsimple, max_removed, replacement_list
    

    def generalize_traces_with_suppression(self, logsimple, gen_config, generalization_type, generalization_set):
        replacement_list = []
        max_removed = 0

        for key in logsimple.keys():
            list_trace = logsimple[key]['trace']
            generalized_traces, replacement_list = self.generalize(list_trace, gen_config, generalization_type, generalization_set, replacement_list)
            logsimple[key]['trace'] = generalized_traces
        return logsimple, max_removed, replacement_list
    
    def generalize(self, list_trace, gen_config, generalization_type, violating_list, replacement_list):
        with open(gen_config, "r") as f:
            config = json.load(f)
        top_node = next(iter(config.keys()))
        for i, trace in enumerate(list_trace):
            for violating_event in violating_list:
                if violating_event == trace:
                    generalized_event = self.generalize_attribute(violating_event, gen_config)
                    if generalization_type == "genAndSup" and generalized_event == top_node:
                        generalized_event = "SUPPRESS_EVENT"
                    updated_trace = self.update_trace(trace, violating_event, generalized_event)
                    if ((violating_event[0], updated_trace[0]) not in replacement_list):
                        index = next((i for i, tpl in enumerate(replacement_list) if tpl[1] == violating_event[0]), None)
                        if index is not None:
                            tpl = replacement_list[index]
                            replacement_list[index] = (tpl[0], updated_trace[0])
                        else:
                            replacement_list.append((violating_event[0], updated_trace[0]))
                    list_trace[i] = updated_trace  
        return list_trace, replacement_list

    def update_trace(self, trace, old_event, new_event):
        tuple_from_event = (new_event, old_event[1])
        if trace == old_event:
            return tuple_from_event
        else:
            return trace
        
    def add_siblings(self, suppression_set, gen_config):
        updated_suppression_set = suppression_set
        sibling_subtrees = []


        with open(gen_config, "r") as f:
            config = json.load(f)

        for violating_event in suppression_set:
            #find siblings and if they are not in violating_list already, also generalize them
            def find_sibling_node(attribute, subtree):
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
                        if subtree[key]:
                            sibling_subtrees.append((subtree[key], violating_event[1]))
                            #sibling_subtrees.append(({'Leucocytes': {}}, violating_event[1]))
                        tuple_from_key = (key, violating_event[1])
                        updated_suppression_set.append(tuple_from_key)

        return updated_suppression_set, sibling_subtrees
    
    def find_lowest_elements_from_subtrees(self, sibling_subtrees, generalization_set, logsimple):
        for subtree_dict, occurence in sibling_subtrees:
            def get_lowest_elements(subtree):
                lowest_elements = []
                keys_to_delete = []
                for key, value in subtree.items():
                    if not value:  # this means that the current key is a "leaf" node
                        lowest_elements.append((key, occurence))
                        keys_to_delete.append(key)
                    else:
                        lowest_elements += get_lowest_elements(value)  # recursively call the function on the nested list/dictionary
                for key in keys_to_delete:
                    del subtree[key]
                return lowest_elements

            lowest_elements = get_lowest_elements(subtree_dict)
            for el in lowest_elements:
                if el not in generalization_set:
                    generalization_set.append(el)
        sibling_subtrees = self.remove_empty_subtrees(sibling_subtrees)
        return generalization_set, sibling_subtrees

    def remove_empty_subtrees(self, sibling_subtrees):
        subtrees_to_remove = []
        for i, subtree in enumerate(sibling_subtrees):
            if len(subtree[0]) == 0:
                subtrees_to_remove.append(i)
        for index in sorted(subtrees_to_remove, reverse=True):
            del sibling_subtrees[index]
        return sibling_subtrees