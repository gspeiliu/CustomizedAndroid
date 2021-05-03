#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Objective: retrieve every single tags on the repsitory
and check which tag is used to merge in the downstream
"""

import os
import csv
import ast
import json

from collections import defaultdict
from datetime import datetime

class MergeTags:
    def __init__(self, repo_base, branches, merge_base, tag_detail, out_base, commit_tag_path, general_tags, commit_ts):
        self._repo = repo_base
        self._out_base = out_base
        self._branches = branches
        self._merge_base = merge_base
        self._tags = tag_detail
        self._commit_tag = commit_tag_path
        self._general_tags = general_tags
        self._commit_ts = commit_ts

    def commit_tag(self, commit, tag_dict):
        print(commit, len(tag_dict))
        commit_tags = set()
        for tag_commit, tags in tag_dict.items():
            for cmt in tags:
               cmt.startswith(commit) 
               commit_tags.add(tags[0])
        return list(commit_tags)

    def real_commit_retrieve(self, tag_dict):
        outs = defaultdict(list)
        for commit, tags in tag_dict.items():
            cwd = os.getcwd()
            os.chdir(self._repo)
            os.popen('git reset --hard ' + commit).read()
            real_commit = os.popen('git log --pretty="%H" | head -1').read()
            os.chdir(cwd)
            curr = [list(tags)[0]]
            outs[commit].append(list(tags)[0])
            outs[commit].append(real_commit)
        tags_outs = []
        for commit, tags in outs.items():
            tags_outs.append([commit, tags])
        out_path = os.path.join(self._out_base, 'real_tag_commits.csv')
        with open(out_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(tags_outs)
        return outs

    def commit_tags_backup(self):
        tag_dict = self.tag_retrieve()
        real_tag_commits = self.real_commit_retrieve(tag_dict)
        dirs = os.listdir(self._merge_base)
        outs = []
        for d in dirs:
            d_path = os.path.join(self._merge_base, d)
            curr = [d]
            tags = set()
            if os.path.exists(d_path) and os.path.isdir(d_path):
                csvs = os.listdir(d_path)
                for cf in csvs:
                    if cf.endswith('.csv') and '.android.' not in cf:
                        cf_path = os.path.join(d_path, cf)
                        print(cf_path)
                        with open(cf_path) as f:
                            reader = csv.reader(f)
                            for row in reader:
                                commit = row[2]
                                commit_tags = self.commit_tag(commit, real_tag_commits)
                                for tag in commit_tags:
                                    tags.add(tag)
            curr.append(list(tags))
            outs.append(curr)
        out_path = os.path.join(self._out_base, 'merge_tags_details.csv')
        with open(out_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(outs)

    def lineage_branch_require(self):
        lineage_branches = set()
        with open(self._commit_tag) as f:
            lines = [line.strip() for line in f.readlines()]
        for line in lines:
            if '/' in line:
                continue
            lineage_branches.add(line)
        print('length of:', len(lineage_branches))
        dirs = os.listdir(self._merge_base)
        outs = []
        for d in dirs:
            d_path = os.path.join(self._merge_base, d)
            curr = [d]
            tags = set()
            if os.path.exists(d_path) and os.path.isdir(d_path):
                csvs = os.listdir(d_path)
                for cf in csvs:
                    if cf.endswith('.csv') and '.android.' not in cf:
                        cf_path = os.path.join(d_path, cf)
                        with open(cf_path) as f:
                            reader = csv.reader(f)
                            for row in reader:
                                branch_name = row[-1]
                                if branch_name in lineage_branches:
                                    tags.add(branch_name)
            print(len(tags))
            curr.append(list(tags))
            curr.append(len(tags))
            outs.append(curr)
        out_path = os.path.join(self._out_base, 'lineage_merge_branch_details.csv')
        with open(out_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(outs)

    def general_tags_retrieve(self):
        general_tags = set()
        with open(self._general_tags) as f:
            lines = [line.strip() for line in f.readlines()]
        for tag in lines:
            general_tags.add(tag)
        return general_tags

    def commit_ts_retrieve(self):
        commit_ts = dict()
        with open(self._commit_ts) as f:
            reader = csv.reader(f)
            for row in reader:
                commit_ts[row[0]] = row[2]
        return commit_ts

    def commit_tags_require(self):
        commit_tags = self.commit_tag_retrieve()
        general_tags = self.general_tags_retrieve()
        cmt_tss = self.commit_ts_retrieve()
        print('commit tags size:', len(commit_tags))
        dirs = os.listdir(self._merge_base)
        outs = []
        for d in dirs:
            d_path = os.path.join(self._merge_base, d)
            print(d_path)
            curr = [d]
            tags = []
            year_tag = defaultdict(int)
            if os.path.exists(d_path) and os.path.isdir(d_path):
                csvs = os.listdir(d_path)
                for cf in csvs:
                    if cf.endswith('.csv') and '.android.' not in cf:
                        cf_path = os.path.join(d_path, cf)
                        with open(cf_path) as f:
                            reader = csv.reader(f)
                            for row in reader:
                                commit = row[2]
                                cmt_tags = []
                                for cmt, ts in commit_tags.items():
                                    if cmt.startswith(commit):
                                        if ts not in tags:
                                            tags.append(ts)
                                            tags.append(cmt_tss[ts])
                                            dt = datetime.fromtimestamp(int(cmt_tss[ts]))
                                            year_tag[dt.year] += 1

            curr.append(tags)
            curr.append(int(len(tags) / 2))
            tag_num = []
            for year, num in year_tag.items():
                tag_num.append([year, num])
            tag_num.sort(key = lambda x: x[0], reverse = True)
            curr.append(tag_num)
            outs.append(curr)
        out_path = os.path.join(self._out_base, 'merge_tag_details.csv')
        with open(out_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(outs)

    def commit_tag_retrieve(self):
        commit_tags = dict()
        with open(self._commit_tag) as f:
            reader = csv.reader(f)
            for row in reader:
                tag_cmt = ast.literal_eval(row[1])
                commit_tags[row[0]] = tag_cmt[0].strip()
                commit_tags[tag_cmt[1].strip()] = tag_cmt[0].strip()
        return commit_tags

    def tags(self, branch):
        cwd = os.getcwd()
        tag_dict = defaultdict(set)
        os.chdir(self._repo)
        branch_checkout = os.popen('git checkout -f ' + branch).read()
        branch_pull = os.popen('git pull').read()
        tag_lines = os.popen('git show-ref --tags').readlines()
        os.chdir(cwd)
        for tag_line in tag_lines:
            splits = tag_line.split(' ')
            commit_id = splits[0].strip()
            tag_ref = splits[1].strip()
            rslash_pos = tag_ref.rfind('/')
            tag_name = tag_ref[rslash_pos + 1:]
            tag_dict[commit_id].add(tag_name)
        print(branch, len(tag_dict.keys()))
        return tag_dict

    def tag_retrieve(self):
        branches = set()
        tags_dict = defaultdict(set)
        txts = os.listdir(self._branches)
        for t in txts:
            t_name = t[:-4]
            branches.add(t_name)
        for idx, branch in enumerate(branches):
            if idx == 4:
                break
            tag_dict = self.tags(branch)
            for key, val in tag_dict.items():
                for tag in val:
                    tags_dict[key].add(tag)
        return tags_dict

if __name__ == '__main__':
    repo_base = './platforms/platform_frameworks_base'
    branches = './history/android/branches'
    out_base = './outs/android'
    merge_base = './history/android_base/csvs'
    tag_detail = './history/android/tags_details.csv'
    general_tags = './outs/android_code_general.txt'
    commit_tag_path = './outs/android/real_tag_commits.csv'
    commit_ts_path = './outs/android/tag_commit_ts.csv'
#    lineage_branch_all = '/Users/pliu0032/AndroidVersion/history/lineage/branch_all.txt'
    mt = MergeTags(repo_base, branches, merge_base, tag_detail, out_base, commit_tag_path, general_tags, commit_ts_path)
#    mt.tag_retrieve()
#    mt.commit_tags()
    mt.commit_tags_require()
#    mt.lineage_branch_require()
