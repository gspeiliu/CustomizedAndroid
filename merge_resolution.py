#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Objective: used to check if maintainers ignore
the update from upstream
'''

import os
import csv
import json

import shutil

import pandas as pd

from collections import defaultdict

# platform_frameworks_base
merge_from_platform_name = 'platform_frameworks_base'
merge_from_name = 'android'
out_base_name = 'android_base'
custom_name = 'slimrom'
merge_from_path = './platforms/' + merge_from_platform_name
custom_path = './platforms/' + custom_name
conf_dir = './history/conffiles'
merge_prev_dir = './history/mergeprev'

visited_commits = set()

def java_name_extract(java_path):
    slash_pos = java_path.rfind('/')
    return java_path[slash_pos + 1:]

def conf_line_retrieve(conf):
    confs = []
    if conf.endswith('.java'):
        rslash_pos = conf.rfind('/')
        java_name = conf[rslash_pos + 1:]
        conf_path = os.path.join(conf_dir, java_name)
        with open(conf_path) as f:
            lines = [line.strip() for line in f.readlines()]
        idx = 0
        length = len(lines)
        while idx < length:
            curr_rm = []
            curr_add = []
            if lines[idx].startswith('<<<<<<<'):
                idx += 1
                while not lines[idx].startswith('======='):
                    curr_rm.append(lines[idx])
                    idx += 1
                idx += 1
                while not lines[idx].startswith('>>>>>>>'):
                    curr_add.append(lines[idx])
                    idx += 1
                idx += 1
                confs.append([curr_rm, curr_add])
            else:
                idx += 1
        return origin_file_lines(confs, conf)
    return confs

def origin_file_lines(confs, conf_name):
    rslash_pos = conf_name.rfind('/')
    java_name = conf_name[rslash_pos + 1:]
    line_outs = []
    conf_merge_from_path = os.path.join(merge_from_path, conf_name)
    conf_custom_path = os.path.join(merge_prev_dir, java_name)
    if not os.path.exists(conf_merge_from_path) or not os.path.exists(conf_custom_path):
        return line_outs
    with open(conf_merge_from_path) as f:
        merge_from_lines = [line.strip() for line in f.readlines()]
    with open(conf_custom_path) as f:
        custom_lines = [line.strip() for line in f.readlines()]
    for conf in confs:
        curr = []
        conf_rm = conf[0]
        conf_add = conf[1]
        if conf_rm:
            cstart, cend, clength, clines = origin_file_lines_impl(conf_rm, custom_lines)
            curr.append([cstart, cend, clength, clines])
        else:
            curr.append([0, 0, 0, []])
        if conf_add:
            mstart, mend, mlength, mlines = origin_file_lines_impl(conf_add, merge_from_lines)
            curr.append([mstart, mend, mlength, mlines])
        else:
            curr.append([0, 0, 0, []])
        line_outs.append(curr)
    return line_outs

def origin_file_lines_impl(lines, merge_lines):
    idx = 0
    jdx = 0
    start = 0
    end = 0
    origin_lines = []
    merge_len = len(merge_lines)
    while idx < merge_len:
        if merge_lines[idx] == lines[jdx]:
            start = idx + 1
            inner_idx = idx
            inner_jdx = jdx
            while inner_idx < merge_len and inner_jdx < len(lines):
                if merge_lines[inner_idx] == lines[inner_jdx]:
                    inner_idx += 1
                    inner_jdx += 1
                else:
                    break
            if inner_jdx < len(lines):
                start = 0
                idx += 1
                jdx = 0
            else:
                end = inner_idx
        else:
            idx += 1
        if start != 0:
            break
    return start, end, len(lines), merge_lines[start:end]

def ast_node_cnt(lineNum, ast_nodes):
    node_cnt = 0
    for node in ast_nodes:
        if node.strip():
            start = int(node.split('#')[0].strip())
            end = int(node.split('#')[1].strip())
            if start >= int(lineNum[0]) and end <= int(lineNum[1]):
                node_cnt += 1
    return node_cnt

def add_remove_extract(line):
    add_removes = set()
    at_del = line[2:-2].strip()
    splits = at_del.split(' ')
    add_remove = splits[0].strip()
    if ',' in add_remove:
        inner_splits = add_remove.split(',')
        start = int(inner_splits[0][1:].strip())
        for i in range(start, start + int(inner_splits[1].strip())):
            add_removes.add(i)
    else:
        start = int(add_remove[1:])
        add_removes.add(start)
    return add_removes

def custom_diff_removes(conf, custom_java):
    diff_removes = set()
    if conf.endswith('.java'):
        rslash_pos = conf.rfind('/')
        java_name = conf[rslash_pos + 1:]
        prev_java = os.path.join(merge_prev_dir, java_name)
        lines = os.popen('diff -U 0 ' + prev_java + ' ' + custom_java).readlines()
        idx = 0
        lines_size = len(lines)
        while idx < lines_size:
            if lines[idx].startswith('@@ '):
                diff_removes.update(add_remove_extract(lines[idx]))
                idx += 1
#                while idx < lines_size and not lines[idx].startswith('@@ '):
#                    if lines[idx].startswith('-'):
#                        diff_removes.append(lines[idx][1:].strip())
#                    idx += 1
            else:
                idx += 1
        print(conf, diff_removes, len(diff_removes))
        return diff_removes

def conf_remove_ignore(conf_removes, diff_removes):
    remove_ignore = True
    diff_remove_size = len(diff_removes)
    d_idx = 0
    c_idx = 0
    while d_idx < diff_remove_size:
        if diff_removes[d_idx].strip() == conf_removes[c_idx].strip():
            tmp_idx = d_idx + 1
            while d_idx < diff_remove_size and c_idx < len(conf_removes):
                if diff_removes[d_idx].strip() != conf_removes[c_idx].strip():
                    break
                else:
                    d_idx += 1
                    c_idx += 1
            if c_idx >= len(conf_removes):
                remove_ignore = False
                break
            else:
                c_idx = 0
                d_idx = tmp_idx
        else:
            c_idx = 0
            d_idx += 1
    return remove_ignore

def conflict_lines(conf_line):
    line_numbers = set()
    start = int(conf_line[0])
    end = int(conf_line[1]) + 1
    for i in range(start, end):
        line_numbers.add(i)
    return line_numbers

def up_snippet_exists(up_lines, java_path):
    with open(java_path) as f:
        lines = [line.strip() for line in f.readlines()]
    is_exist = False
    idx = 0
    inner_idx = 0
    while idx < len(lines) and inner_idx < len(up_lines):
        if lines[idx] == up_lines[inner_idx]:
            tmp_idx = idx
            while idx < len(lines) and inner_idx < len(up_lines):
                if lines[idx] == up_lines[inner_idx]:
                    idx += 1
                    inner_idx += 1
                else:
                    break
            if inner_idx >= len(up_lines):
                is_exist = True
                break
            else:
                inner_idx = 0
                idx = tmp_idx + 1
        else:
            idx += 1
    return is_exist

def conf_ignore(custom_commit, custom_branch, conflicts):
    java_jar = './libs/methodparser.jar'
    resolve_dict = defaultdict(int)
    outs = []
    total_ignore = 0
    total_up = 0
    total_other = 0
    total_non_change = 0
    total_non_java = 0
    total_conf = 0
    up_empty = 0
    for conf in conflicts:
        if conf.endswith('.java'):
            curr = [conf]
            curr_ignore = 0
            conf_lines = conf_line_retrieve(conf)
            if not conf_lines:
                continue
            custom_java = os.path.join(custom_path, conf)
            merge_from_java = os.path.join(merge_from_path, conf)
            if not os.path.exists(custom_java) or not os.path.exists(merge_from_java):
                continue
            custom_reset(custom_commit, custom_branch)
            diff_removes = custom_diff_removes(conf, custom_java)
            if diff_removes:
                for conf_line in conf_lines:
                    conf_removes = conf_line[0]
                    conf_line_numbers = conflict_lines(conf_removes)
                    intersect = conf_line_numbers.intersection(diff_removes)
                    if not up_snippet_exists(conf_line[1][3], custom_java) and not intersect:
                        ### ignore
                        total_ignore += 1
                    elif up_snippet_exists(conf_line[1][3], custom_java) and intersect:
                        ### from upstream
                        total_up += 1
                    else:
                        ### others
                        total_other += 1
            else:
                total_non_change += len(conf_lines)
                total_non_java += 1
            total_conf += len(conf_lines)
    return total_ignore, total_up, total_other, total_non_change, total_non_java

def custom_reset(custom_commit, custom_branch):
    '''Reset to the specific commit status'''
    cwd = os.getcwd()
    os.chdir(custom_path)
    branch_checkout = os.popen('git checkout -f ' + custom_branch).read()
    reset_res = os.popen('git reset --hard ' + custom_commit).read()
    os.chdir(cwd)

def merge_from_reset(merge_from_commit, merge_from_branch):
    '''Reset to the specific commit status'''
    cwd = os.getcwd()
    os.chdir(merge_from_path)
    branch_checkout = os.popen('git checkout -f ' + merge_from_branch).read()
    reset_res = os.popen('git reset --hard ' + merge_from_commit).read()
    os.chdir(cwd)

def conf_dir_empty():
    fs = os.listdir(conf_dir)
    for f in fs:
        f_path = os.path.join(conf_dir, f)
        os.remove(f_path)
    pfs = os.listdir(merge_prev_dir)
    for f in pfs:
        f_path = os.path.join(merge_prev_dir, f)
        os.remove(f_path)

def custom_merge_diff(custom_commit, custom_branch, merge_from_commit, merge_from_branch):
    '''Merge android platform and check if there are some conflicts'''
    custom_reset(custom_commit, custom_branch)
    merge_from_reset(merge_from_commit, merge_from_branch)
    has_conflict = False
    cwd = os.getcwd()
    conf_dir_empty()
    os.chdir(custom_path)
    upd_res = os.popen('git remote update').read()
    merge_res = os.popen('git merge ' + merge_from_name + '/' + merge_from_branch).read()
    conflicts = set()
    conf_javas = 0
    merges = merge_res.split('\n')
    total_conf_paths = set()
    for line in merges:
        if line.startswith('CONFLICT (content): Merge conflict in'):
            has_conflict = True
            splits = line.split(' ')
            conflicts.add(splits[-1])
            if splits[-1].endswith('.java'):
                conf_javas += 1
            conf_path = os.path.join(custom_path, splits[-1])
            total_conf_paths.add(conf_path)
            shutil.copy2(conf_path, conf_dir)
    if has_conflict:
        os.popen('git merge --abort').read()
        for conf_path in total_conf_paths:
            if os.path.exists(conf_path):
                shutil.copy2(conf_path, merge_prev_dir)
    os.chdir(cwd)

    return has_conflict, len(conflicts), conflicts, conf_javas

def conf_merges(merge_file_name):
    rslash_pos = merge_file_name.rfind('/')
    merge_branch_name = merge_file_name[rslash_pos + 1:][:-4] + '-merge.csv'
    conf_merge_path = './history/' + out_base_name + '/mergetypes/' + custom_name + '/' + merge_branch_name
    print(conf_merge_path)
    commits = set()
    if os.path.exists(conf_merge_path):
        df = pd.read_csv(conf_merge_path)
        for idx in range(len(df)):
            commits.add(df.iloc[idx]['Merge'])
    return commits

def custom_merge():
    merge_commit_base = './history/' + out_base_name + '/csvs/' + custom_name
    csvs = os.listdir(merge_commit_base)
    conflict_info = []
    for idx, merge_file in enumerate(csvs):
        if merge_file.endswith('.csv') and '.android.' not in merge_file:
            merge_csv = os.path.join(merge_commit_base, merge_file)
            merge_out = os.path.join('./history/' + out_base_name + '/ignore/' + custom_name, merge_file[:-4] + '-merge.csv')
            print(idx, len(csvs), merge_csv)
            conf_commits = conf_merges(merge_csv)
            if conf_commits:
                total_merge, conflict_merge = custom_conf_ignore(merge_csv, merge_out, conf_commits)
                conflict_info.append([merge_file[:-4], total_merge, conflict_merge])
    conflict_info_out = os.path.join('./history/' + out_base_name + '/ignore/' + custom_name, 'conflict_info.csv')
    with open(conflict_info_out, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['branch', 'total', 'conflict'])
        writer.writerows(conflict_info)



def custom_conf_ignore(merge_csv, out_csv, conf_commits):
    total_merge = 0
    conflict_merge = 0
    outs = []
    with open(merge_csv) as f:
        reader = csv.reader(f)
        for row in reader:
            if not row[0] in conf_commits:
                continue
            if not visited_commits or row[0] not in visited_commits:
                visited_commits.add(row[0])
            else:
                continue
            total_merge += 1
            custom_commit = row[1]
            merge_from_commit = row[2]
            custom_brch = row[4]
            merge_from_brch = row[5]
            print(row)
            has_conflict, conf_len, conflicts, conf_java = custom_merge_diff(custom_commit, custom_brch, merge_from_commit, merge_from_brch)
            if has_conflict:
                conflict_merge += 1
                conf_ignore_cnt, total_up_cnt, total_other_cnt, total_non_change, total_non_java = conf_ignore(row[0], custom_brch, conflicts)
                outs.append([row[0], conf_len, conf_java, conf_ignore_cnt, total_up_cnt, total_other_cnt, total_non_change, total_non_java])
    if outs:
        with open(out_csv, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['Merge', 'Conflicts', 'Javas', 'Ignore', 'Up', 'Other', 'Non_change', 'Non_java'])
            writer.writerows(outs)
    print(total_merge, conflict_merge)
    return total_merge, conflict_merge

if __name__ == '__main__':
    custom_merge()
