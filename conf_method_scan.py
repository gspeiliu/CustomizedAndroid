#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Objective: used to scan conflicted methods
utilized in real Android apks
"""

import os
import csv
import ast

import subprocess
import pandas as pd

apk_base = '/mnt/fit-Knowledgezoo/yanjie/APPLineage'

def apk_retrieve():
    apks = []
    random_txt = './random1k_complete.txt'
    with open(random_txt) as f:
        lines = [line.strip() for line in f.readlines()]
    for line in lines:
        df = pd.read_csv(line, header = 0)
        line_len = len(df)
        apks.append(df.iloc[line_len - 1]['sha256'] + '.apk')
    return apks

def conflict_method_detect():
    api_path = './conf_methods.txt'
    out_base = './outs/scanout'
    apks = apk_retrieve()
    succ_cnt = 0
    for apk in apks:
        apk_name = apk[:-4]
        apk_path = os.path.join(apk_base, apk)
        out_path = os.path.join(out_base, apk_name + '.txt')
        apk_scan = scan_apk_impl(apk_path, api_path, out_path)
        if apk_scan:
            succ_cnt += 1
    print('succ count:', succ_cnt)

def scan_apk_impl(apk_path, api_path, output_path):
    is_succ = False
    apk_scan_jar_path = './libs/ConfMethodScan.jar'
    platform_path = './android-platforms'
    cmd = ['java', '-jar', apk_scan_jar_path, apk_path, platform_path, api_path]
    proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding = 'utf-8')
    try:
        outs, errs = proc.communicate(timeout = 600)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
    else:
        is_succ = True
        print(output_path)
        print('SUCCESS')
        with open(output_path, 'w') as f:
            f.write(outs)
    return is_succ

if __name__ == '__main__':
    conflict_method_detect()
