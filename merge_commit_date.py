#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Objective: used to retrieve the merge commit date,
customized commit date, merge from commit date
"""

import os
import csv

class CommitDate:
    def __init__(self, merge_repo_base, out_base, merge_base):
        self._merge_repos = merge_repo_base
        self._out_base = out_base
        self._merge_base = merge_base
    
    def custom_commit_dates(self, custom_merge, custom_commit, last_commit, custom_name, custom_branch):
        platform_base = './platforms'
        custom_path = os.path.join(platform_base, custom_name)
        commit_times = 0
        cwd = os.getcwd()
        os.chdir(custom_path)
        print(os.getcwd())
        os.popen('git checkout -f ' + custom_branch).read()
        merge_date = os.popen('git show -s --format=%ct ' + custom_merge).read().strip()
        commit_date = os.popen('git show -s --format=%ct ' + custom_commit).read().strip()
        if last_commit:
            commits = os.popen('git log --oneline ' + custom_commit + '..' + last_commit).read()
            commit_times = len(commits.split('\n'))
        between_commits = os.popen('git log --oneline ' + custom_merge + '..' + custom_commit).read()
        between_times = len(between_commits.split('\n'))
        print(custom_path, 'merge date:', merge_date, 'merge commit date:', commit_date, commit_times)
        os.chdir(cwd)
        
        return merge_date, commit_date, commit_times, between_times

    def merge_from_commit_dates(self, merge_from_commit, merge_from_branch, last_commit):
        platform_base = './platforms'
        merge_from_path = os.path.join(platform_base, self._merge_base)
        commit_times = 0
        cwd = os.getcwd()
        os.chdir(merge_from_path)
        print(os.getcwd())
        os.popen('git checkout -f ' + merge_from_branch).read()
        commit_date = os.popen('git show -s --format=%ct ' + merge_from_commit).read().strip()
        print(merge_from_path, 'merge from commit:', commit_date)
        if last_commit:
            commits = os.popen('git log --oneline ' + merge_from_commit + '..' + last_commit).read()
            commit_times = len(commits.split('\n'))
        os.chdir(cwd)

        return commit_date, commit_times

    def commit_date_retrieve(self):
        repos = os.listdir(self._merge_repos)
        for repo in repos:
            repo_path = os.path.join(self._merge_repos, repo)
            csvs = os.listdir(repo_path)
            for cf in csvs:
                if cf.endswith('.csv') and '.android.' not in cf:
                    cf_path = os.path.join(repo_path, cf)
                    outs = []
                    last_commit = ''
                    from_last_commit = ''
                    with open(cf_path) as f:
                        reader = csv.reader(f)
                        for row in reader:
                            print(row)
                            custom_merge = row[0]
                            custom_commit = row[1]
                            custom_name = repo
                            custom_branch = row[4]
                            merge_from_commit = row[2]
                            merge_from_branch = row[5]
                            curr = row
                            merge_date, commit_date, commit_times, between_times = self.custom_commit_dates(custom_merge, custom_commit, last_commit, custom_name, custom_branch)
                            merge_from_commit_date, from_commit_times = self.merge_from_commit_dates(merge_from_commit, merge_from_branch, from_last_commit)
                            curr.append(merge_date)
                            curr.append(commit_date)
                            curr.append(merge_from_commit_date)
                            curr.append(commit_times)
                            curr.append(between_times)
                            curr.append(from_commit_times)
                            outs.append(curr)
                            last_commit = custom_commit
                            from_last_commit = merge_from_commit
                    out_repo_path = os.path.join(self._out_base, repo)
                    if not os.path.exists(out_repo_path):
                        os.mkdir(out_repo_path)
                    out_cf_path = os.path.join(out_repo_path, cf)
                    with open(out_cf_path, 'w') as f:
                        writer = csv.writer(f)
                        writer.writerows(outs)


if __name__ == '__main__':
    # upstream projects name, clone from Githbub
    # official Android will be cloned with name platform_frameworks_base
    merge_base = 'platform_frameworks_base'
    out_base = './android_base/dates'
    merge_repo_base = './android_base/csvs'
    cd = CommitDate(merge_repo_base, out_base, merge_base)
    cd.commit_date_retrieve()
