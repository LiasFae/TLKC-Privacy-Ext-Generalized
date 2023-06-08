import copy
import os

import numpy as np
import multiprocessing as mp
import operator


class MVS():

    def __init__(self, T, logsimple, sensitive, cont, sensitives, bk_type, dict_safe={}):
        self.T = T
        self.logsimple = logsimple
        self.sensitive = sensitive
        self.cont = cont
        self.sensitives = sensitives
        self.dev = []
        self.bk_type = bk_type
        self.dict_safe = dict_safe

    def mvs(self, L, K, C, multiprocess, mp_technique, t=None):
        i = L
        while i > 0 and i < L + 1:
            i -= 1
            if t is None:
                if self.dict_safe[i][K][C]["v"] != []:
                    w = self.dict_safe[i][K][C]["w"]
                    X1 = self.dict_safe[i][K][C]["x"]
                    violating = self.dict_safe[i][K][C]["v"]
            else:
                if self.dict_safe[i][K][C][t]["v"] != []:
                    w = self.dict_safe[i][K][C][t]["w"]
                    X1 = self.dict_safe[i][K][C][t]["x"]
                    violating = self.dict_safe[i][K][C][t]["v"]
            if 'X1' in locals() and len(X1) > 0:
                count = {tuple(el): 0 for el in X1}
                prob = {tuple(v): {el: [] for el in self.sensitive} for v in X1}
                el_trace = {tuple(el): [] for el in X1}
                i += 1
                w.append([])
                violating.append([])
                prob, count, el_trace = self.prob(X1, count, el_trace, prob, i, type, first=True)
                gen = [q for q in X1 if count[tuple(q)] > 0] #new commented
                w, violating = self.w_violating(gen, count, violating, prob, K, C, w, i)
                # 10: end if
                # 11: end for
                X1.clear()
                # 12: Xi+1 ! Wi ! Wi;
                X1 = self.w_create(w, i, X1, violating, L, multiprocess, mp_technique)
                print("X1: " + str(len(X1)))
                i += 1
                break
            elif 'X1' in locals() and len(X1) == 0:
                i = L + 1
        # 1: X1 <- set of all distinct pairs in T;
        if i == 0:
            flat_list = [item for sublist in self.T for item in sublist]
            X1 = list(set(flat_list))
            if self.bk_type == 'multiset':
                not_valid_multiset = []
                # --- improvement ---
                events_counter = self.aggregate_events(self.logsimple)
                violating_raw_events = self.add_violating_raw_events(events_counter, K)
                # --- improvement end ---
                for el in X1:
                    if el[1] > L:
                        # --- improvement ---
                        if el[0] in violating_raw_events:
                            continue
                        else:
                        # --- improvement end ---
                            not_valid_multiset.append(el)
                for x in not_valid_multiset:
                    X1.remove(x)

            print("X1: " + str(len(X1)))
            # 2: i = 1;
            # count(q)
            # prob(q|s)
            count = {el: 0 for el in X1}
            prob = {v: {el: [] for el in self.sensitive} for v in X1}
            el_trace = {el: [] for el in X1}
            prob, count, el_trace = self.prob(X1, count, el_trace, prob, i, type)
            # 5: for all q  in Xi where |T(q)| > 0 do
            gen = [q for q in X1 if count[tuple(q)] > 0] #new commented
            violating = [[]]
            w = [[]]
            w, violating = self.w_violating(gen, count, violating, prob, K, C, w, i)
            non_violating_events_len_1 = w
            # 10: end if
            # 11: end for
            w[0].sort(key=operator.itemgetter(1))
            X1.clear()
            # 12: Xi+1 ! Wi ! Wi;
            if self.bk_type == 'relative':  # sequence time
                for iterator in range(len(w[0])):
                    candidate = w[0].pop(0)
                    for comb in w[0]:
                        if comb[1] > candidate[1]:
                            X1.append([candidate, comb])
                        elif comb[0] != candidate[0] and comb[1] == candidate[1]:
                            X1.append([candidate, comb])
                        elif comb[1] < candidate[1]:
                            X1.append([comb, candidate])
                    w[0].append(candidate)
                    iterator += 1

            elif self.bk_type == 'sequence':  # sequence
                for iter in range(len(w[0])):
                    candidate = w[0].pop(0)
                    #new
                    X1.append([candidate, candidate])
                    #
                    for comb in w[0]:
                        X1.append([candidate, comb])
                        # if comb[0] != candidate[0]:
                        #     X1.append([candidate, comb])
                        # if comb[1] > candidate[1]:
                        #     X1.append([candidate, comb])
                        # elif comb[1] < candidate[1]:
                        #     X1.append([comb, candidate])
                    w[0].append(candidate)
                    iter += 1
            elif self.bk_type == 'set':  # set
                while len(w[0]) > 1:
                    candidate = w[0].pop(0)
                    for comb in w[0]:
                        if sorted([candidate, comb]) not in X1:
                            X1.append(sorted([candidate, comb]))
            elif self.bk_type == 'multiset':  # multiset
                while len(w[0]) > 1:
                    candidate = w[0].pop(0)
                    for comb in w[0]:
                        if sorted([candidate, comb]) not in X1:
                            if comb[0] != candidate[0] and (comb[1] + candidate[1]) <= L:
                                X1.append(sorted([candidate, comb]))
            i = 1
            print("X1: " + str(len(X1)))
        # 3: while i <= L or Xi not empty do
        while i < L and len(X1) > 0:
            # 4: Scan T to compute |T(q)| and P(s|q), for all q in Xi, for all s in S;
            w.append([])
            violating.append([])
            count = {tuple(el): 0 for el in X1}
            prob = {tuple(v): {el: [] for el in self.sensitive} for v in X1}
            prob, count, el_trace = self.prob(X1, count, el_trace, prob, i, type)
            # 5: for all q  in Xi where |T(q)| > 0 do
            gen = [q for q in X1 if count[tuple(q)] > 0] #new commented
            w, violating = self.w_violating(gen, count, violating, prob, K, C, w, i)
            # 10: end if
            # 11: end for
            i += 1
            if i < L:
                X1.clear()
                # 12: Xi+1 ! Wi ! Wi;
                X1 = self.w_create(w, i - 1, X1, violating, L, multiprocess, mp_technique, non_violating_events = non_violating_events_len_1)
                print("X1: " + str(len(X1)))
                #print(X1)
            # 18: i++;

        # 19: end while
        # 20: return V (T) = V1 ' · · · ' Vi−1;
        if t is None:
            self.dict_safe[i - 1][K][C]["w"] = w.copy()
            self.dict_safe[i - 1][K][C]["x"] = X1.copy()
            self.dict_safe[i - 1][K][C]["v"] = violating.copy()
        else:
            self.dict_safe[i - 1][K][C][t]["w"] = w.copy()
            self.dict_safe[i - 1][K][C][t]["x"] = X1.copy()
            self.dict_safe[i - 1][K][C][t]["v"] = violating.copy()

        violatingConj = [item for sublist in violating for item in sublist]
        return violatingConj, self.dict_safe

    def aggregate_events(self, logsimple):
        events = {}
        for _, trace in logsimple.items():
            tuples = trace['trace']
            for event, count in tuples:
                if event in events:
                    events[event] += count
                else:
                    events[event] = count
        return events
    
    def add_violating_raw_events(self, events_counter, K):
        raw_violating_events = []
        for event, count in events_counter.items():
            if count < K:
                raw_violating_events.append(event)
        return raw_violating_events
    
    def chunk(self, data, parts):
        divided = [None] * parts
        n = len(data) // parts
        for i in range(parts):
            divided[i] = data[i * n:n * (i + 1)]
        if len(data) % 2 != 0:
            divided[-1] += [data[-1]]
        return divided

    def chunkIt(self, data, num):
        avg = len(data) / float(num)
        out = []
        last = 0.0

        while last < len(data):
            out.append(data[int(last):int(last + avg)])
            last += avg

        return out

    def X1_generator_seq(self, data, i, X1, violating, non_violating_events):
        # replace w[i] with data
        # copy X1 to Z1
        Z1 = copy.deepcopy(X1)
        # new way----------------------
        for non_violating in data:
            for event in non_violating_events[0]:
                new_cand = copy.deepcopy(non_violating)
                for index in range(len(non_violating)+1):
                    new_cand[index:index] = [event]
                    Z1.append(new_cand)
                    new_cand = copy.deepcopy(non_violating)
        return Z1

        # new way---------------

        # for iter in range(len(data)):
        #     candidate = data.pop(0)
        #     for comb in data:
        #         add = False
        #         add2 = False
        #         try:
        #             if candidate[0:i] == comb[0:i] and comb[i][0] != candidate[i][0]:
        #                 add = True
        #         except:
        #             print(candidate)
        #             print(comb)
        #             print(i)
        #
        #         if candidate[0:i] == comb[0:i] and comb[i][0] != candidate[i][0]: \
        #             add = True
        #         elif candidate[0:i] == comb[0:i] and comb[i][0] == candidate[i][0] \
        #                 and comb[i][1] > candidate[i][1]:
        #             add = True
        #         elif candidate[0:i] == comb[0:i] and comb[i][0] == candidate[i][0] \
        #                 and comb[i][1] < candidate[i][1]:
        #             add2 = True
        #         if add:
        #             Z1.append([])
        #             Z1[len(Z1) - 1] = candidate[:]
        #             Z1[len(Z1) - 1].append(comb[i])
        #         elif add2:
        #             Z1.append([])
        #             Z1[len(Z1) - 1] = comb[:]
        #             Z1[len(Z1) - 1].append(candidate[i])
        #         if add or add2:
        #             if Z1[len(Z1) - 1] in Z1[0:len(Z1) - 1]:
        #                 del Z1[-1]
        #             else:
        #                 # 13: for %q & Xi+1 do
        #                 # 14: if q is a super sequence of any v & Vi then
        #                 # 15: Remove q from Xi+1;
        #                 if len(Z1) == 0:
        #                     break
        #                 included = False
        #                 for v in violating[i]:
        #                     if all(elem in Z1[len(Z1) - 1] for elem in v):
        #                         for j in range(0, i + 1):
        #                             if j == 0:
        #                                 if v[j] in Z1[len(Z1) - 1]:
        #                                     index = Z1[len(Z1) - 1].index(v[j])
        #                                 else:
        #                                     break
        #                             else:
        #                                 if v[j] in Z1[len(Z1) - 1][index + 1::]:
        #                                     index = Z1[len(Z1) - 1].index(v[j])
        #                                     if j == i:
        #                                         included = True
        #                                         break
        #                                 else:
        #                                     break
        #                     # if all(elem in X1[len(X1) - 1] for elem in v):
        #                     if included:
        #                         del Z1[-1]
        #                         break
        #     data.append(candidate)
        #     iter += 1
        #
        # return Z1

    def X1_generator_relative(self, data, i, X1, violating):
        Z1 = copy.deepcopy(X1)
        for iterator in range(len(data)):
            candidate = data.pop(0)
            for comb in data:
                if candidate[0:i] == comb[0:i] and candidate[i][1] > comb[i][1]:
                    Z1.append([])
                    Z1[len(Z1) - 1] = comb[:]
                    Z1[len(Z1) - 1].append(candidate[i])
                elif candidate[0:i] == comb[0:i] and candidate[i][1] < comb[i][1]:
                    Z1.append([])
                    Z1[len(Z1) - 1] = candidate[:]
                    Z1[len(Z1) - 1].append(comb[i])
                elif candidate[0:i] == comb[0:i] and candidate[i][1] == comb[i][1] and candidate[i][1] != comb[i][1]:
                    Z1.append([])
                    Z1[len(Z1) - 1] = candidate[:]
                    Z1[len(Z1) - 1].append(comb[i])
                else:
                    break
                if Z1[len(Z1) - 1] in Z1[0:len(Z1) - 1]:
                    del Z1[-1]
                else:
                    # 13: for %q & Xi+1 do
                    # 14: if q is a super sequence of any v & Vi then
                    # 15: Remove q from Xi+1;
                    included = False
                    for v in violating[i]:
                        if len(Z1) == 0:
                            break
                        if all(elem in Z1[len(Z1) - 1] for elem in v):
                            for j in range(0, i + 1):
                                if j == 0:
                                    if v[j] in Z1[len(Z1) - 1]:
                                        index = Z1[len(Z1) - 1].index(v[j])
                                    else:
                                        break
                                else:
                                    if v[j] in Z1[len(Z1) - 1][index + 1::]:
                                        index = Z1[len(Z1) - 1].index(v[j])
                                        if j == i:
                                            included = True
                                            break
                                    else:
                                        break
                        # if all(elem in Z1[len(Z1) - 1] for elem in v):
                        if included:
                            del Z1[-1]
                            break
            data.append(candidate)
            iterator += 1

        return Z1

    def X1_generator_multiset(self, data, i, X1, violating, L):
        Z1 = copy.deepcopy(X1)
        while len(data) > 0:
            candidate = data.pop()
            for comb in data:
                if candidate[0:i] == comb[0:i] and comb[i] not in candidate:
                    if comb[i][0] in [el[0] for el in candidate]:
                        continue
                    if comb[i][1] + sum([el[1] for el in candidate]) > L:
                        continue
                    Z1.append([])
                    Z1[len(Z1) - 1] = candidate[:]
                    Z1[len(Z1) - 1].append(comb[i])
                    Z1[len(Z1) - 1] = sorted(Z1[len(Z1) - 1])
                    if Z1[len(Z1) - 1] in Z1[0:len(Z1) - 1]:
                        del Z1[-1]
                    else:
                        # 13: for %q & Xi+1 do
                        # 14: if q is a super sequence of any v & Vi then
                        # 15: Remove q from Xi+1;
                        for v in violating[i]:
                            if len(Z1) == 0:
                                break
                            if all(elem in Z1[len(Z1) - 1] for elem in v):
                                del Z1[-1]
        return Z1

    def X1_generator_set(self, data, i, X1, violating):
        Z1 = copy.deepcopy(X1)
        while len(data) > 0:
            candidate = data.pop()
            for comb in data:
                if candidate[0:i] == comb[0:i] and comb[i] not in candidate:
                    Z1.append([])
                    Z1[len(Z1) - 1] = candidate[:]
                    Z1[len(Z1) - 1].append(comb[i])
                    Z1[len(Z1) - 1] = sorted(Z1[len(Z1) - 1])
                    if Z1[len(Z1) - 1] in Z1[0:len(Z1) - 1]:
                        del Z1[-1]
                    else:
                        # 13: for %q & Xi+1 do
                        # 14: if q is a super sequence of any v & Vi then
                        # 15: Remove q from Xi+1;
                        for v in violating[i]:
                            if len(Z1) == 0:
                                break
                            if all(elem in Z1[len(Z1) - 1] for elem in v):
                                del Z1[-1]
        return Z1

    def foo_relative(self, q, data, i, X1, violating):
        Z1 = self.X1_generator_relative(data, i, X1, violating)
        q.put(Z1)

    def foo_relative_without_q(self, data, i, X1, violating):
        Z1 = self.X1_generator_relative(data, i, X1, violating)
        return Z1

    def foo_seq(self, q, data, i, X1, violating, non_violating_events):
        Z1 = self.X1_generator_seq(data, i, X1, violating, non_violating_events)
        q.put(Z1)

    def foo_seq_without_q(self, data, i, X1, violating, non_violating_events):
        Z1 = self.X1_generator_seq(data, i, X1, violating, non_violating_events)
        return Z1

    def foo_set(self, q, data, i, X1, violating):
        Z1 = self.X1_generator_set(data, i, X1, violating)
        q.put(Z1)

    def foo_set_without_q(self, data, i, X1, violating):
        Z1 = self.X1_generator_set(data, i, X1, violating)
        return Z1

    def foo_multiset(self, q, data, i, X1, violating, L):
        Z1 = self.X1_generator_multiset(data, i, X1, violating, L)
        q.put(Z1)

    def foo_multiset_without_q(self, data, i, X1, violating, L):
        Z1 = self.X1_generator_multiset(data, i, X1, violating, L)
        return Z1

    def foo_sequence_relative_prob_without_q(self,X1,i,prob,count,newel_trace):
        result = self.prob_generator_sequence_relative(X1,i,prob,count,newel_trace)
        return result

    def prob_generator_sequence_relative(self,X1,i,prob,count,newel_trace):
        for q in X1:
            if len(q) == 2:
                try:
                    for key, value in self.logsimple.items():
                        # for value in el_trace[q[0]]:
                        tr = value["trace"]
                        S = value["sensitive"]
                        included = False
                        if self.bk_type == 'sequence':
                            included = self.is_subsequence(q, tr)
                            # if q[i] not in tr[tr.index(q[0]) + 1::]:
                            #     included = False
                        else:
                            if q[i] not in tr:
                                included = False
                        if included:
                            count[tuple(q)] += 1
                            newel_trace[tuple(q)].append(value.copy())
                            for key2, value2 in S.items():
                                if type(prob[tuple(q)][key2]) is list:
                                    prob[tuple(q)][key2].append(value2)
                except:
                    print("Candidate len 1 not in log...!")
            else:
                # if tuple(q[0:i]) not in el_trace.keys():
                #     print(el_trace)
                # else:
                try:
                    for key, value in self.logsimple.items():
                        # for value in el_trace[tuple(q[0:i])]:
                        tr = value["trace"]
                        S = value["sensitive"]
                        included = False
                        if self.bk_type == 'sequence':
                            included = self.is_subsequence(q, tr)
                            # if something went wrong
                            # if q[i - 1] not in tr:
                            #     included = False
                            # elif q[i] not in tr[tr.index(q[i - 1]) + 1::]:
                            #     included = False
                        else:
                            if q[i] not in tr:
                                included = False
                        if included:
                            count[tuple(q)] += 1
                            newel_trace[tuple(q)].append(value.copy())
                            for key2, value2 in S.items():
                                if type(prob[tuple(q)][key2]) is list:
                                    prob[tuple(q)][key2].append(value2)
                except:
                    print("Candidate > len 1 not in log...!")
        result_dict = {'prob':prob, 'newel_trace':newel_trace,'count':count}
        return result_dict


    def prob_generator_set_multiset(self,X1,i,prob,count):
        newel_trace = {tuple(el): [] for el in X1}
        for key, value in self.logsimple.items():
            for q in X1:
                if len(q) == 2:
                    tr = value["trace"]
                    S = value["sensitive"]
                    included = True
                    for j in range(0, len(q)):
                        if q[j][0] not in [ev[0] for ev in tr]:
                            included = False
                            break
                        # new multiset
                        elif self.bk_type == 'multiset':
                            for ev in tr:
                                if q[j][0] == ev[0] and q[j][1] > ev[1]:
                                    included = False
                                    break
                    if included:
                        count[tuple(q)] += 1
                        newel_trace[tuple(q)].append(value.copy())
                        for key2, value2 in S.items():
                            if type(prob[tuple(q)][key2]) is list:
                                prob[tuple(q)][key2].append(value2)
                else:  # len q > 2
                    tr = value["trace"]
                    S = value["sensitive"]
                    included = True
                    for j in range(0, len(q)):
                        # if q[j] not in tr:
                        #     included = False
                        #     break
                        if q[j][0] not in [ev[0] for ev in tr]:
                            included = False
                            break
                            # new multiset
                        elif self.bk_type == 'multiset':
                            for ev in tr:
                                if q[j][0] == ev[0] and q[j][1] > ev[1]:
                                    included = False
                                    break
                    if included:
                        count[tuple(q)] += 1
                        newel_trace[tuple(q)].append(value.copy())
                        for key2, value2 in S.items():
                            if type(prob[tuple(q)][key2]) is list:
                                prob[tuple(q)][key2].append(value2)
        for q in X1:
            prob = self.sens_boxplot(prob, count, q, i)

        return prob,newel_trace,count

    def w_create(self, w, i, X1, violating, L, multiprocess, mp_technique, non_violating_events = []):
        X1_new = []
        if multiprocess:
            if mp_technique == "queue":
                workers_number = os.cpu_count()
                data_chunks = self.chunkIt(w[i], workers_number)
                mp.set_start_method('spawn')
                jobs = []
                if len(data_chunks) < 1:
                    return []

                for worker in range(workers_number):
                    print("In worker X1 creator %d out of %d" % (worker + 1, workers_number))
                    q = mp.Queue()
                    if self.bk_type == 'relative':
                        p = mp.Process(target=self.foo_relative, args=(q, data_chunks[worker], i, X1, violating))
                    elif self.bk_type == 'sequence':
                        p = mp.Process(target=self.foo_seq, args=(q, data_chunks[worker], i, X1, violating, non_violating_events))
                    elif self.bk_type == 'set':
                        p = mp.Process(target=self.foo_set, args=(q, data_chunks[worker], i, X1, violating))
                    elif self.bk_type == 'multiset':
                        p = mp.Process(target=self.foo_multiset, args=(q, data_chunks[worker], i, X1, violating, L))
                    jobs.append(p)
                    p.start()
                    X1_new += q.get()
                for job in jobs:
                    job.join()


            elif mp_technique == "pool":
                pool = mp.Pool()
                workers = []
                workers_number = os.cpu_count()
                data_chunks = self.chunkIt(w[i], workers_number)
                if len(data_chunks) < 1:
                    return []

                for worker in range(workers_number):
                    print("In worker X1 creator %d out of %d" % (worker + 1, workers_number))
                    if self.bk_type == 'relative':
                        workers.append(
                            pool.apply_async(self.foo_relative_without_q, args=(data_chunks[worker], i, X1, violating)))
                    elif self.bk_type == 'sequence':
                        workers.append(
                            pool.apply_async(self.foo_seq_without_q, args=(data_chunks[worker], i, X1, violating, non_violating_events)))
                    elif self.bk_type == 'set':
                        workers.append(
                            pool.apply_async(self.foo_set_without_q, args=(data_chunks[worker], i, X1, violating)))
                    elif self.bk_type == 'multiset':
                        workers.append(
                            pool.apply_async(self.foo_multiset_without_q, args=(data_chunks[worker], i, X1, violating, L)))

                for work in workers:
                    X1_new += work.get()
                pool.close()
                pool.join()

        else:
            if len(w[i]) < 1:
                return []
            if self.bk_type == 'relative':
                X1_new = self.X1_generator_relative(w[i], i, X1, violating)
            elif self.bk_type == 'sequence':
                X1_new = self.X1_generator_seq(w[i], i, X1, violating, non_violating_events)
            elif self.bk_type == 'set':
                X1_new = self.X1_generator_set(w[i], i, X1, violating)
            elif self.bk_type == 'multiset':
                X1_new = self.X1_generator_multiset(w[i], i, X1, violating, L)

        return X1_new


    def w_violating(self, gen, count, violating, prob, K, C, w, i):
        if i == 0:
            for q in gen:
                # 6: if |T(q)|< K or P(s|q) > C then
                if count[q] < K:
                    violating[0].append([q])
                else:
                    highestC = 0
                    for s in self.sensitive:
                        if highestC > C:
                            break
                        if prob[q][s] > highestC:
                            highestC = prob[q][s]
                    # 7: Add q to Vi;
                    if highestC > C:
                        violating[0].append([q])
                    # 8: else
                    # 9: Add q to Wi;
                    else:
                        w[0].append(q)
        else:
            for q in gen:
                # 6: if |T(q)|< K or P(s|q) > C then
                if count[tuple(q)] < K:
                    violating[i].append(q)
                else:
                    highestC = 0
                    for s in self.sensitive:
                        if highestC > C:
                            break
                        if prob[tuple(q)][s] > highestC:
                            highestC = prob[tuple(q)][s]
                    # 7: Add q to Vi;
                    if highestC > C:
                        violating[i].append(q)
                    # 8: else
                    # 9: Add q to Wi;
                    else:
                        w[i].append(q)
        return w, violating


    def prob(self, X1, count, el_trace, prob, i, type, first=False):
        if first:
            for q in X1:
                # creating prob(q|s) and count(q)
                for key, value in self.logsimple.items():
                    tr = value["trace"]
                    S = value["sensitive"]
                    if self.bk_type == 'set':  # or self.bk_type == 'multiset':
                        if all(elem in tr for elem in q):
                            count[tuple(q)] += 1
                            el_trace[tuple(q)].append(value)
                            # listing all values of the different sensitive attributes (key2)
                            for key2, value2 in S.items():
                                prob[tuple(q)][key2].append(value2)
                    # new multiset (real)
                    elif self.bk_type == 'multiset':
                        for elem in q:
                            for ev in tr:
                                if elem[0] == ev[0] and elem[1] <= ev[1]:
                                    count[tuple(q)] += 1
                                    el_trace[tuple(q)].append(value)
                                    # listing all values of the different sensitive attributes (key2)
                                    for key2, value2 in S.items():
                                        prob[tuple(q)][key2].append(value2)
                    else:
                        included = False
                        for j in range(0, len(q)):
                            if j == 0:
                                if q[j] in tr:
                                    index = tr.index(q[j])
                                else:
                                    break
                            else:
                                if q[j] in tr[index + 1::]:
                                    index = tr.index(q[j])
                                    if j == len(q) - 1:
                                        included = True
                                        break
                                else:
                                    break
                            # if all(elem in X1[len(X1) - 1] for elem in v):
                        if included:
                            count[tuple(q)] += 1
                            el_trace[tuple(q)].append(value)
                            # listing all values of the different sensitive attributes (key2)
                            for key2, value2 in S.items():
                                prob[tuple(q)][key2].append(value2)
            # calculating the distribution of s for q
            for q in X1:
                prob = self.sens_boxplot(prob, count, q, i)
        else:  # first is false
            if i == 0:
                for key, value in self.logsimple.items():
                    # creating prob(q|s) and count(q)
                    for q in X1:
                        tr = value["trace"]
                        S = value["sensitive"]
                        if q in tr:
                            count[q] += 1
                            el_trace[q].append(value)
                            # listing all values of the different sensitive attributes (key2)
                            for key2, value2 in S.items():
                                prob[q][key2].append(value2)
                # calculating the distribution of s for q
                for q in X1:
                    prob = self.sens_boxplot(prob, count, q, i)
            else:
                if not (self.bk_type == 'set' or self.bk_type == 'multiset'):
                    newel_trace = {tuple(el): [] for el in X1}

                    results = []
                    pool = mp.Pool()
                    workers = []
                    workers_number = os.cpu_count()
                    data_chunks = self.chunkIt(X1, workers_number)
                    for worker in range(workers_number):
                        print("In worker prob() creator %d out of %d" % (worker + 1, workers_number))
                        workers.append(
                                pool.apply_async(self.foo_sequence_relative_prob_without_q, args=(data_chunks[worker], i, prob, count, newel_trace)))

                    for work in workers:
                        results.append(work.get())
                    pool.close()
                    pool.join()


                    for result in results:
                        for key, value in result.items():
                            if key == 'prob':
                                for prob_key,prob_value in value.items():
                                    for sensitive_key, sensitive_value in prob_value.items():
                                        prob[prob_key][sensitive_key] += sensitive_value
                            elif key == 'newel_trace':
                                for el_trace_key, el_trace_value in value.items():
                                    newel_trace[el_trace_key] += el_trace_value
                            elif key == 'count':
                                for count_key,count_value in value.items():
                                    count[count_key] += count_value

                    # Ohne multiprocessing-------------------
                    # result_dict = self.prob_generator_sequence_relative(X1,i,prob,count,newel_trace)
                    # prob = result_dict['prob']
                    # newel_trace = result_dict['newel_trace']
                    # count = result_dict['count']
                    #----------------------------------------

                    for q in X1:
                        prob = self.sens_boxplot(prob, count, q, i)

                else:  # type is set or multiset
                    prob,newel_trace,count = self.prob_generator_set_multiset(X1,i,prob,count)

                el_trace = newel_trace.copy()
        return prob, count, el_trace

    def is_subsequence(self, x, y):
        """Test whether x is a subsequence of y"""
        x = list(x)
        for letter in y:
            if x and x[0] == letter:
                x.pop(0)
        return not x

    def sens_boxplot(self, prob, count, q, i):
        if i == 0:
            # calculating the distribution of s for q
            for key in self.sensitive:
                highest = 0
                if key in self.cont:
                    freq = {"low": 0, "middle": 0, "high": 0}
                    lower_quartile = np.percentile(prob[q][key], 25)
                    higher_quartile = np.percentile(prob[q][key], 75)
                else:
                    freq = {v: 0 for v in prob[q][key]}
                for item in prob[q][key]:
                    # continious variables are handled with standard deviation
                    if key in self.cont:
                        if item < lower_quartile:
                            freq["low"] += 1
                        elif item > higher_quartile:
                            freq["high"] += 1
                        else:
                            freq["middle"] += 1
                    else:
                        if item in freq:
                            freq[item] += 1
                        else:
                            freq[item] = 1
                # Calculate confidence (C) which is mean of the category confidences,
                # where confidence of each category is 1/(No. values in the category).
                if key in self.cont:
                    if freq["low"] > 0:
                        low = 1 / freq["low"]
                    else:
                        low = 0
                    if freq["middle"] > 0:
                        middle = 1 / freq["middle"]
                    else:
                        middle = 0
                    if freq["high"]:
                        high = 1 / freq["high"]
                    else:
                        high = 0
                    highest = (low + middle + high) / 3
                else:
                    for item in prob[q][key]:
                        newhighest = freq[item] / count[q]
                        if newhighest > highest:
                            highest = newhighest
                prob[q][key] = highest
        else:
            for key in self.sensitive:
                highest = 0
                if prob[tuple(q)][key] == []:
                    prob[tuple(q)][key] = 0
                    continue
                if key in self.cont:
                    freq = {"low": 0, "middle": 0, "high": 0}
                    lower_quartile = np.percentile(prob[tuple(q)][key], 25)
                    higher_quartile = np.percentile(prob[tuple(q)][key], 75)
                else:
                    if type(prob[tuple(q)][key]) is not list:
                        continue
                    freq = {v: 0 for v in prob[tuple(q)][key]}
                for item in prob[tuple(q)][key]:
                    # continious variables are handled with standard deviation
                    if key in self.cont:
                        if item < lower_quartile:
                            freq["low"] += 1
                        elif item > higher_quartile:
                            freq["high"] += 1
                        else:
                            freq["middle"] += 1
                    else:
                        if item in freq:
                            freq[item] += 1
                        else:
                            freq[item] = 1
                # Calculate confidence (C) which is mean of the category confidences,
                # where confidence of each category is 1/(No. values in the category).
                if key in self.cont:
                    if freq["low"] > 0:
                        low = 1 / freq["low"]
                    else:
                        low = 0
                    if freq["middle"] > 0:
                        middle = 1 / freq["middle"]
                    else:
                        middle = 0
                    if freq["high"]:
                        high = 1 / freq["high"]
                    else:
                        high = 0
                    highest = (low + middle + high) / 3
                else:
                    for item in prob[tuple(q)][key]:
                        newhighest = freq[item] / count[tuple(q)]
                        if newhighest > highest:
                            highest = newhighest
                prob[tuple(q)][key] = highest
        return prob
