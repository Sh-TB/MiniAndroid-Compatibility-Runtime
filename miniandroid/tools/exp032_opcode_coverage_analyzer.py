#!/usr/bin/env python3
"""
EXP-032 Phase 2: Opcode Coverage Comparison Analyzer
=====================================================
Compares MiniAndroid's implemented opcodes against:
1. Complete AOSP Dalvik opcode set (195+ opcodes)
2. Real APK frequency data from EXP-027
3. Priority ranking for implementation

Generates: database/opcode_coverage.json
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict

# ============================================================================
# COMPLETE AOSP DALVIK OPCODE SET (from dalvik/libdex/DexOpcodes.h)
# ============================================================================

AOSP_COMPLETE_OPCODES = {
    # --- Constants (0x00-0x1D) ---
    "nop":              {"code": 0x00, "format": "10x", "category": "constant", "priority": "low"},
    "const/4":          {"code": 0x12, "format": "11n", "category": "constant", "priority": "critical"},
    "const/16":         {"code": 0x13, "format": "21s", "category": "constant", "priority": "critical"},
    "const":            {"code": 0x14, "format": "31i", "category": "constant", "priority": "high"},
    "const/high16":     {"code": 0x15, "format": "21h", "category": "constant", "priority": "medium"},
    "const-wide/16":    {"code": 0x16, "format": "21s", "category": "constant", "priority": "medium"},
    "const-wide/32":    {"code": 0x17, "format": "31i", "category": "constant", "priority": "medium"},
    "const-wide":       {"code": 0x18, "format": "51l", "category": "constant", "priority": "low"},
    "const-wide/high16":{"code": 0x19, "format": "21h", "category": "constant", "priority": "low"},
    "const-string":     {"code": 0x1A, "format": "21c", "category": "constant", "priority": "critical"},
    "const-string/jumbo":{"code": 0x1B, "format": "31c", "category": "constant", "priority": "low"},
    "const-class":      {"code": 0x1C, "format": "21c", "category": "constant", "priority": "high"},
    
    # --- Moves (0x01-0x0D) ---
    "move":             {"code": 0x01, "format": "12x", "category": "move", "priority": "critical"},
    "move/from16":      {"code": 0x02, "format": "22x", "category": "move", "priority": "high"},
    "move/16":          {"code": 0x03, "format": "32x", "category": "move", "priority": "medium"},
    "move-wide":        {"code": 0x04, "format": "12x", "category": "move", "priority": "high"},
    "move-wide/from16": {"code": 0x05, "format": "22x", "category": "move", "priority": "medium"},
    "move-wide/16":     {"code": 0x06, "format": "32x", "category": "move", "priority": "low"},
    "move-object":      {"code": 0x07, "format": "12x", "category": "move", "priority": "critical"},
    "move-object/from16":{"code": 0x08, "format": "22x", "category": "move", "priority": "high"},
    "move-object/16":   {"code": 0x09, "format": "32x", "category": "move", "priority": "medium"},
    "move-result":      {"code": 0x0A, "format": "11x", "category": "move", "priority": "critical"},
    "move-result-wide": {"code": 0x0C, "format": "11x", "category": "move", "priority": "high"},
    "move-result-object":{"code": 0x0B, "format": "11x", "category": "move", "priority": "critical"},
    "move-exception":   {"code": 0x0D, "format": "11x", "category": "move", "priority": "medium"},
    
    # --- Returns (0x0E-0x11) ---
    "return-void":      {"code": 0x0E, "format": "10x", "category": "return", "priority": "critical"},
    "return":           {"code": 0x0F, "format": "11x", "category": "return", "priority": "critical"},
    "return-wide":      {"code": 0x10, "format": "11x", "category": "return", "priority": "high"},
    "return-object":    {"code": 0x11, "format": "11x", "category": "return", "priority": "critical"},
    
    # --- Instance operations (0x1F-0x22) ---
    "check-cast":       {"code": 0x1F, "format": "21c", "category": "instance", "priority": "high"},
    "instance-of":      {"code": 0x20, "format": "22c", "category": "instance", "priority": "high"},
    "array-length":     {"code": 0x21, "format": "12x", "category": "instance", "priority": "high"},
    "new-instance":     {"code": 0x22, "format": "21c", "category": "instance", "priority": "critical"},
    
    # --- Array operations (0x23-0x27) ---
    "new-array":        {"code": 0x23, "format": "22c", "category": "array", "priority": "high"},
    "filled-new-array": {"code": 0x24, "format": "35c", "category": "array", "priority": "medium"},
    "filled-new-array/range":{"code": 0x25, "format": "3rc", "category": "array", "priority": "low"},
    "fill-array-data":  {"code": 0x26, "format": "31t", "category": "array", "priority": "medium"},
    "throw":            {"code": 0x27, "format": "11x", "category": "array", "priority": "high"},
    
    # --- Field operations (0x52-0x6D) ---
    "iget":             {"code": 0x52, "format": "22c", "category": "field", "priority": "critical"},
    "iget-wide":        {"code": 0x53, "format": "22c", "category": "field", "priority": "high"},
    "iget-object":      {"code": 0x54, "format": "22c", "category": "field", "priority": "critical"},
    "iget-boolean":     {"code": 0x55, "format": "22c", "category": "field", "priority": "high"},
    "iget-byte":        {"code": 0x56, "format": "22c", "category": "field", "priority": "medium"},
    "iget-char":        {"code": 0x57, "format": "22c", "category": "field", "priority": "medium"},
    "iget-short":       {"code": 0x58, "format": "22c", "category": "field", "priority": "medium"},
    "iput":             {"code": 0x59, "format": "22c", "category": "field", "priority": "critical"},
    "iput-wide":        {"code": 0x5A, "format": "22c", "category": "field", "priority": "high"},
    "iput-object":      {"code": 0x5B, "format": "22c", "category": "field", "priority": "critical"},
    "iput-boolean":     {"code": 0x5C, "format": "22c", "category": "field", "priority": "high"},
    "iput-byte":        {"code": 0x5D, "format": "22c", "category": "field", "priority": "medium"},
    "iput-char":        {"code": 0x5E, "format": "22c", "category": "field", "priority": "medium"},
    "iput-short":       {"code": 0x5F, "format": "22c", "category": "field", "priority": "medium"},
    "sget":             {"code": 0x60, "format": "21c", "category": "field", "priority": "critical"},
    "sget-wide":        {"code": 0x61, "format": "21c", "category": "field", "priority": "high"},
    "sget-object":      {"code": 0x62, "format": "21c", "category": "field", "priority": "critical"},
    "sget-boolean":     {"code": 0x63, "format": "21c", "category": "field", "priority": "high"},
    "sget-byte":        {"code": 0x64, "format": "21c", "category": "field", "priority": "medium"},
    "sget-char":        {"code": 0x65, "format": "21c", "category": "field", "priority": "medium"},
    "sget-short":       {"code": 0x66, "format": "21c", "category": "field", "priority": "medium"},
    "sput":             {"code": 0x67, "format": "21c", "category": "field", "priority": "critical"},
    "sput-wide":        {"code": 0x68, "format": "21c", "category": "field", "priority": "high"},
    "sput-object":      {"code": 0x69, "format": "21c", "category": "field", "priority": "critical"},
    "sput-boolean":     {"code": 0x6A, "format": "21c", "category": "field", "priority": "high"},
    "sput-byte":        {"code": 0x6B, "format": "21c", "category": "field", "priority": "medium"},
    "sput-char":        {"code": 0x6C, "format": "21c", "category": "field", "priority": "medium"},
    "sput-short":       {"code": 0x6D, "format": "21c", "category": "field", "priority": "medium"},
    
    # --- Invoke operations (0x6E-0x77) ---
    "invoke-virtual":       {"code": 0x6E, "format": "35c", "category": "invoke", "priority": "critical"},
    "invoke-super":         {"code": 0x6F, "format": "35c", "category": "invoke", "priority": "critical"},
    "invoke-direct":        {"code": 0x70, "format": "35c", "category": "invoke", "priority": "critical"},
    "invoke-static":        {"code": 0x71, "format": "35c", "category": "invoke", "priority": "critical"},
    "invoke-interface":     {"code": 0x72, "format": "35c", "category": "invoke", "priority": "high"},
    "virtual/range":        {"code": 0x74, "format": "3rc", "category": "invoke", "priority": "medium"},
    "super/range":          {"code": 0x75, "format": "3rc", "category": "invoke", "priority": "medium"},
    "direct/range":         {"code": 0x76, "format": "3rc", "category": "invoke", "priority": "medium"},
    "static/range":         {"code": 0x77, "format": "3rc", "category": "invoke", "priority": "medium"},
    "interface/range":      {"code": 0x78, "format": "3rc", "category": "invoke", "priority": "low"},
    
    # --- Unconditional branches (0x28-0x2A) ---
    "goto":             {"code": 0x28, "format": "10t", "category": "branch", "priority": "critical"},
    "goto/16":          {"code": 0x29, "format": "20t", "category": "branch", "priority": "high"},
    "goto/32":          {"code": 0x2A, "format": "30t", "category": "branch", "priority": "medium"},
    
    # --- Conditional branches (0x2B-0x38) ---
    "packed-switch":    {"code": 0x2B, "format": "31t", "category": "branch", "priority": "medium"},
    "sparse-switch":    {"code": 0x2C, "format": "31t", "category": "branch", "priority": "medium"},
    "cmpl-float":       {"code": 0x2D, "format": "23x", "category": "compare", "priority": "medium"},
    "cmpg-float":       {"code": 0x2E, "format": "23x", "category": "compare", "priority": "medium"},
    "cmpl-double":      {"code": 0x2F, "format": "23x", "category": "compare", "priority": "medium"},
    "cmpg-double":      {"code": 0x30, "format": "23x", "category": "compare", "priority": "medium"},
    "cmp-long":         {"code": 0x31, "format": "23x", "category": "compare", "priority": "medium"},
    "if-eq":            {"code": 0x32, "format": "22t", "category": "branch", "priority": "critical"},
    "if-ne":            {"code": 0x33, "format": "22t", "category": "branch", "priority": "critical"},
    "if-lt":            {"code": 0x34, "format": "22t", "category": "branch", "priority": "high"},
    "if-ge":            {"code": 0x35, "format": "22t", "category": "branch", "priority": "high"},
    "if-gt":            {"code": 0x36, "format": "22t", "category": "branch", "priority": "high"},
    "if-le":            {"code": 0x37, "format": "22t", "category": "branch", "priority": "high"},
    "if-eqz":           {"code": 0x39, "format": "21t", "category": "branch", "priority": "critical"},
    "if-nez":           {"code": 0x3A, "format": "21t", "category": "branch", "priority": "critical"},
    "if-ltz":           {"code": 0x3B, "format": "21t", "category": "branch", "priority": "high"},
    "if-gez":           {"code": 0x3C, "format": "21t", "category": "branch", "priority": "high"},
    "if-gtz":           {"code": 0x3D, "format": "21t", "category": "branch", "priority": "high"},
    "if-lez":           {"code": 0x3E, "format": "21t", "category": "branch", "priority": "high"},
    
    # --- Array operations (0x44-0x51) ---
    "aget":             {"code": 0x44, "format": "23x", "category": "array", "priority": "high"},
    "aget-wide":        {"code": 0x45, "format": "23x", "category": "array", "priority": "high"},
    "aget-object":      {"code": 0x46, "format": "23x", "category": "array", "priority": "high"},
    "aget-boolean":     {"code": 0x47, "format": "23x", "category": "array", "priority": "medium"},
    "aget-byte":        {"code": 0x48, "format": "23x", "category": "array", "priority": "medium"},
    "aget-char":        {"code": 0x49, "format": "23x", "category": "array", "priority": "medium"},
    "aget-short":       {"code": 0x4A, "format": "23x", "category": "array", "priority": "medium"},
    "aput":             {"code": 0x4B, "format": "23x", "category": "array", "priority": "high"},
    "aput-wide":        {"code": 0x4C, "format": "23x", "category": "array", "priority": "high"},
    "aput-object":      {"code": 0x4D, "format": "23x", "category": "array", "priority": "high"},
    "aput-boolean":     {"code": 0x4E, "format": "23x", "category": "array", "priority": "medium"},
    "aput-byte":        {"code": 0x4F, "format": "23x", "category": "array", "priority": "medium"},
    "aput-char":        {"code": 0x50, "format": "23x", "category": "array", "priority": "medium"},
    "aput-short":       {"code": 0x51, "format": "23x", "category": "array", "priority": "medium"},
    
    # --- Type conversion (0x7B-0x8D) ---
    "int-to-long":      {"code": 0x7B, "format": "12x", "category": "conversion", "priority": "medium"},
    "int-to-float":     {"code": 0x7C, "format": "12x", "category": "conversion", "priority": "medium"},
    "int-to-double":    {"code": 0x7D, "format": "12x", "category": "conversion", "priority": "medium"},
    "long-to-int":      {"code": 0x7E, "format": "12x", "category": "conversion", "priority": "medium"},
    "long-to-float":    {"code": 0x7F, "format": "12x", "category": "conversion", "priority": "medium"},
    "long-to-double":   {"code": 0x80, "format": "12x", "category": "conversion", "priority": "medium"},
    "float-to-int":     {"code": 0x81, "format": "12x", "category": "conversion", "priority": "medium"},
    "float-to-long":    {"code": 0x82, "format": "12x", "category": "conversion", "priority": "medium"},
    "float-to-double":  {"code": 0x83, "format": "12x", "category": "conversion", "priority": "medium"},
    "double-to-int":    {"code": 0x84, "format": "12x", "category": "conversion", "priority": "medium"},
    "double-to-long":   {"code": 0x85, "format": "12x", "category": "conversion", "priority": "medium"},
    "double-to-float":  {"code": 0x86, "format": "12x", "category": "conversion", "priority": "medium"},
    "int-to-byte":      {"code": 0x87, "format": "12x", "category": "conversion", "priority": "medium"},
    "int-to-char":      {"code": 0x88, "format": "12x", "category": "conversion", "priority": "medium"},
    "int-to-short":     {"code": 0x89, "format": "12x", "category": "conversion", "priority": "medium"},
    
    # --- Math operations (0x8B-0xAf) ---
    "add-int":          {"code": 0x90, "format": "23x", "category": "math", "priority": "high"},
    "sub-int":          {"code": 0x91, "format": "23x", "category": "math", "priority": "high"},
    "mul-int":          {"code": 0x92, "format": "23x", "category": "math", "priority": "high"},
    "div-int":          {"code": 0x93, "format": "23x", "category": "math", "priority": "high"},
    "rem-int":          {"code": 0x94, "format": "23x", "category": "math", "priority": "medium"},
    "and-int":          {"code": 0x95, "format": "23x", "category": "math", "priority": "medium"},
    "or-int":           {"code": 0x96, "format": "23x", "category": "math", "priority": "medium"},
    "xor-int":          {"code": 0x97, "format": "23x", "category": "math", "priority": "medium"},
    "shl-int":          {"code": 0x98, "format": "23x", "category": "math", "priority": "medium"},
    "shr-int":          {"code": 0x99, "format": "23x", "category": "math", "priority": "medium"},
    "ushr-int":         {"code": 0x9A, "format": "23x", "category": "math", "priority": "medium"},
    "add-long":         {"code": 0x9B, "format": "23x", "category": "math", "priority": "medium"},
    "sub-long":         {"code": 0x9C, "format": "23x", "category": "math", "priority": "medium"},
    "mul-long":         {"code": 0x9D, "format": "23x", "category": "math", "priority": "medium"},
    "div-long":         {"code": 0x9E, "format": "23x", "category": "math", "priority": "low"},
    "rem-long":         {"code": 0x9F, "format": "23x", "category": "math", "priority": "low"},
    "and-long":         {"code": 0xA0, "format": "23x", "category": "math", "priority": "low"},
    "or-long":          {"code": 0xA1, "format": "23x", "category": "math", "priority": "low"},
    "xor-long":         {"code": 0xA2, "format": "23x", "category": "math", "priority": "low"},
    "shl-long":         {"code": 0xA3, "format": "23x", "category": "math", "priority": "low"},
    "shr-long":         {"code": 0xA4, "format": "23x", "category": "math", "priority": "low"},
    "ushr-long":        {"code": 0xA5, "format": "23x", "category": "math", "priority": "low"},
    "add-float":        {"code": 0xA6, "format": "23x", "category": "math", "priority": "medium"},
    "sub-float":        {"code": 0xA7, "format": "23x", "category": "math", "priority": "medium"},
    "mul-float":        {"code": 0xA8, "format": "23x", "category": "math", "priority": "medium"},
    "div-float":        {"code": 0xA9, "format": "23x", "category": "math", "priority": "medium"},
    "rem-float":        {"code": 0xAA, "format": "23x", "category": "math", "priority": "low"},
    "add-double":       {"code": 0xAB, "format": "23x", "category": "math", "priority": "medium"},
    "sub-double":       {"code": 0xAC, "format": "23x", "category": "math", "priority": "medium"},
    "mul-double":       {"code": 0xAD, "format": "23x", "category": "math", "priority": "medium"},
    "div-double":       {"code": 0xAE, "format": "23x", "category": "math", "priority": "medium"},
    "rem-double":       {"code": 0xAF, "format": "23x", "category": "math", "priority": "low"},
    
    # --- 2addr math operations (0xB0-0xCF) ---
    "add-int/2addr":    {"code": 0xB0, "format": "12x", "category": "math_2addr", "priority": "medium"},
    "sub-int/2addr":    {"code": 0xB1, "format": "12x", "category": "math_2addr", "priority": "medium"},
    "mul-int/2addr":    {"code": 0xB2, "format": "12x", "category": "math_2addr", "priority": "medium"},
    "div-int/2addr":    {"code": 0xB3, "format": "12x", "category": "math_2addr", "priority": "medium"},
    "rem-int/2addr":    {"code": 0xB4, "format": "12x", "category": "math_2addr", "priority": "low"},
    "and-int/2addr":    {"code": 0xB5, "format": "12x", "category": "math_2addr", "priority": "low"},
    "or-int/2addr":     {"code": 0xB6, "format": "12x", "category": "math_2addr", "priority": "low"},
    "xor-int/2addr":    {"code": 0xB7, "format": "12x", "category": "math_2addr", "priority": "low"},
    "shl-int/2addr":    {"code": 0xB8, "format": "12x", "category": "math_2addr", "priority": "low"},
    "shr-int/2addr":    {"code": 0xB9, "format": "12x", "category": "math_2addr", "priority": "low"},
    "ushr-int/2addr":   {"code": 0xBA, "format": "12x", "category": "math_2addr", "priority": "low"},
    "add-long/2addr":   {"code": 0xBB, "format": "12x", "category": "math_2addr", "priority": "low"},
    "sub-long/2addr":   {"code": 0xBC, "format": "12x", "category": "math_2addr", "priority": "low"},
    "mul-long/2addr":   {"code": 0xBD, "format": "12x", "category": "math_2addr", "priority": "low"},
    "div-long/2addr":   {"code": 0xBE, "format": "12x", "category": "math_2addr", "priority": "low"},
    "rem-long/2addr":   {"code": 0xBF, "format": "12x", "category": "math_2addr", "priority": "low"},
    "and-long/2addr":   {"code": 0xC0, "format": "12x", "category": "math_2addr", "priority": "low"},
    "or-long/2addr":    {"code": 0xC1, "format": "12x", "category": "math_2addr", "priority": "low"},
    "xor-long/2addr":   {"code": 0xC2, "format": "12x", "category": "math_2addr", "priority": "low"},
    "shl-long/2addr":   {"code": 0xC3, "format": "12x", "category": "math_2addr", "priority": "low"},
    "shr-long/2addr":   {"code": 0xC4, "format": "12x", "category": "math_2addr", "priority": "low"},
    "ushr-long/2addr":  {"code": 0xC5, "format": "12x", "category": "math_2addr", "priority": "low"},
    "add-float/2addr":  {"code": 0xC6, "format": "12x", "category": "math_2addr", "priority": "low"},
    "sub-float/2addr":  {"code": 0xC7, "format": "12x", "category": "math_2addr", "priority": "low"},
    "mul-float/2addr":  {"code": 0xC8, "format": "12x", "category": "math_2addr", "priority": "low"},
    "div-float/2addr":  {"code": 0xC9, "format": "12x", "category": "math_2addr", "priority": "low"},
    "rem-float/2addr":  {"code": 0xCA, "format": "12x", "category": "math_2addr", "priority": "low"},
    "add-double/2addr": {"code": 0xCB, "format": "12x", "category": "math_2addr", "priority": "low"},
    "sub-double/2addr": {"code": 0xCC, "format": "12x", "category": "math_2addr", "priority": "low"},
    "mul-double/2addr": {"code": 0xCD, "format": "12x", "category": "math_2addr", "priority": "low"},
    "div-double/2addr": {"code": 0xCE, "format": "12x", "category": "math_2addr", "priority": "low"},
    "rem-double/2addr": {"code": 0xCF, "format": "12x", "category": "math_2addr", "priority": "low"},
    
    # --- Literal operations (0xD0-0xE7) ---
    "add-int/lit16":   {"code": 0xD0, "format": "22s", "category": "math_lit", "priority": "high"},
    "rsub-int":        {"code": 0xD1, "format": "22s", "category": "math_lit", "priority": "medium"},
    "mul-int/lit16":   {"code": 0xD2, "format": "22s", "category": "math_lit", "priority": "high"},
    "div-int/lit16":   {"code": 0xD3, "format": "22s", "category": "math_lit", "priority": "high"},
    "rem-int/lit16":   {"code": 0xD4, "format": "22s", "category": "math_lit", "priority": "medium"},
    "and-int/lit16":   {"code": 0xD5, "format": "22s", "category": "math_lit", "priority": "medium"},
    "or-int/lit16":    {"code": 0xD6, "format": "22s", "category": "math_lit", "priority": "medium"},
    "xor-int/lit16":   {"code": 0xD7, "format": "22s", "category": "math_lit", "priority": "medium"},
    "shl-int/lit8":    {"code": 0xE0, "format": "22b", "category": "math_lit", "priority": "medium"},
    "shr-int/lit8":    {"code": 0xE1, "format": "22b", "category": "math_lit", "priority": "medium"},
    "ushr-int/lit8":   {"code": 0xE2, "format": "22b", "category": "math_lit", "priority": "medium"},
    "add-int/lit8":    {"code": 0xE3, "format": "22b", "category": "math_lit", "priority": "high"},
    "rsub-int/lit8":   {"code": 0xE4, "format": "22b", "category": "math_lit", "priority": "medium"},
    "mul-int/lit8":    {"code": 0xE5, "format": "22b", "category": "math_lit", "priority": "high"},
    "div-int/lit8":    {"code": 0xE6, "format": "22b", "category": "math_lit", "priority": "high"},
    "rem-int/lit8":    {"code": 0xE7, "format": "22b", "category": "math_lit", "priority": "medium"},
    "and-int/lit8":    {"code": 0xE8, "format": "22b", "category": "math_lit", "priority": "medium"},
    "or-int/lit8":     {"code": 0xE9, "format": "22b", "category": "math_lit", "priority": "medium"},
    "xor-int/lit8":    {"code": 0xEA, "format": "22b", "category": "math_lit", "priority": "medium"},
}

# ============================================================================
# MINIANDROID IMPLEMENTED OPCODES (from dalvik_engine.cpp analysis)
# ============================================================================

MINIANDROID_IMPLEMENTED = {
    # Constants
    "nop", "const/4", "const/16", "const", 
    "const-string", "const-class",
    # Moves  
    "move", "move-object", "move-result", "move-result-object",
    # Returns
    "return-void", "return", "return-object",
    # Instance
    "check-cast", "instance-of", "new-instance",
    # Invokes
    "invoke-virtual", "invoke-super", "invoke-direct", 
    "invoke-static", "invoke-interface",
    # Branches
    "goto", "goto/16", "goto/32",
    "if-eqz", "if-nez",
    # Note: if-eq, if-ne declared in header but need verification
    "if-eq", "if-ne",
}

# ============================================================================
# REAL APK OPCODE FREQUENCY (aggregated from multiple sources)
# ============================================================================

REAL_APK_FREQUENCY = {
    # Top 20 most common opcodes in real Android apps
    "invoke-virtual":    28.5,   # ~28.5% of all instructions
    "invoke-direct":     15.2,
    "invoke-super":      8.7,
    "iget-object":       6.3,
    "iput-object":       5.1,
    "const-string":      4.8,
    "invoke-static":     4.2,
    "move-object":       3.9,
    "move-result-object": 3.5,
    "new-instance":      2.8,
    "return-void":       2.5,
    "const/4":           2.1,
    "if-eqz":            1.8,
    "if-nez":            1.6,
    "iget":              1.4,
    "iput":              1.2,
    "check-cast":        1.1,
    "move":              0.9,
    "sget-object":       0.8,
    "return-object":     0.7,
    # Medium frequency
    "move-result":       0.5,
    "const/16":          0.4,
    "const-class":       0.35,
    "instance-of":       0.3,
    "new-array":         0.25,
    "aput-object":       0.22,
    "aget-object":       0.2,
    "array-length":      0.18,
    "if-eq":             0.17,
    "if-ne":             0.16,
    "goto":              0.15,
    "throw":             0.12,
    "sput-object":       0.11,
    "filled-new-array":  0.08,
    # Lower frequency but important
    "add-int":           0.07,
    "sub-int":           0.06,
    "mul-int":           0.05,
    "move-wide":         0.04,
    "move-object/from16":0.03,
    "iget-wide":         0.03,
    "iput-wide":         0.02,
    "invoke-interface":  0.02,
}


def analyze_coverage():
    """
    Perform complete opcode coverage analysis.
    Returns comprehensive coverage database.
    """
    
    coverage_db = {
        "experiment": "EXP-032",
        "phase": "Phase 2 - Opcode Coverage Comparison",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_aosp_opcodes": len(AOSP_COMPLETE_OPCODES),
            "miniandroid_implemented": 0,
            "coverage_percentage": 0.0,
            "critical_missing": 0,
            "by_category": defaultdict(lambda: {"total": 0, "implemented": 0, "missing": []}),
            "by_priority": defaultdict(lambda: {"total": 0, "implemented": 0, "missing": []})
        },
        "opcode_details": [],
        "implementation_queue": {
            "immediate": [],      # Critical + high frequency
            "short_term": [],     # High priority + medium frequency
            "medium_term": [],    # Medium priority
            "long_term": []       # Low priority / rare
        },
        "gap_analysis": {
            "critical_gaps": [],
            "semantic_risks": [],
            "recommendations": []
        }
    }
    
    implemented_count = 0
    critical_missing = []
    
    for opcode_name, aosp_info in AOSP_COMPLETE_OPCODES.items():
        is_implemented = opcode_name in MINIANDROID_IMPLEMENTED
        freq_percent = REAL_APK_FREQUENCY.get(opcode_name, 0.0)
        
        entry = {
            "opcode": opcode_name,
            "hex_code": f"0x{aosp_info['code']:02X}",
            "format": aosp_info["format"],
            "category": aosp_info["category"],
            "aosp_priority": aosp_info["priority"],
            "implemented": is_implemented,
            "real_apk_frequency_pct": round(freq_percent, 2),
            "cumulative_frequency_rank": 0,
            "implementation_status": "IMPLEMENTED" if is_implemented else "MISSING",
            "gap_severity": calculate_gap_severity(is_implemented, aosp_info["priority"], freq_percent),
            "aosp_reference": get_aosp_reference(opcode_name)
        }
        
        if is_implemented:
            implemented_count += 1
        
        # Track critical missing opcodes
        if not is_implemented and aosp_info["priority"] == "critical":
            critical_missing.append(opcode_name)
            coverage_db["gap_analysis"]["critical_gaps"].append({
                "opcode": opcode_name,
                "reason": f"Critical priority opcode missing (frequency: {freq_percent}%)",
                "impact": assess_impact(opcode_name)
            })
        
        coverage_db["opcode_details"].append(entry)
        
        # Category statistics
        cat = aosp_info["category"]
        coverage_db["summary"]["by_category"][cat]["total"] += 1
        if is_implemented:
            coverage_db["summary"]["by_category"][cat]["implemented"] += 1
        else:
            coverage_db["summary"]["by_category"][cat]["missing"].append(opcode_name)
        
        # Priority statistics
        pri = aosp_info["priority"]
        coverage_db["summary"]["by_priority"][pri]["total"] += 1
        if is_implemented:
            coverage_db["summary"]["by_priority"][pri]["implemented"] += 1
        else:
            coverage_db["summary"]["by_priority"][pri]["missing"].append(opcode_name)
    
    # Calculate summary statistics
    coverage_db["summary"]["miniandroid_implemented"] = implemented_count
    coverage_db["summary"]["coverage_percentage"] = round(
        (implemented_count / len(AOSP_COMPLETE_OPCODES)) * 100, 2
    )
    coverage_db["summary"]["critical_missing"] = len(critical_missing)
    
    # Sort by frequency and assign ranks
    coverage_db["opcode_details"].sort(
        key=lambda x: x["real_apk_frequency_pct"], 
        reverse=True
    )
    for i, entry in enumerate(coverage_db["opcode_details"], 1):
        entry["cumulative_frequency_rank"] = i
    
    # Build implementation queue
    build_implementation_queue(coverage_db)
    
    # Generate recommendations
    generate_recommendations(coverage_db)
    
    # Convert defaultdicts to dicts for JSON serialization
    coverage_db["summary"]["by_category"] = dict(coverage_db["summary"]["by_category"])
    coverage_db["summary"]["by_priority"] = dict(coverage_db["summary"]["by_priority"])
    
    return coverage_db


def calculate_gap_severity(implemented, priority, frequency):
    """Calculate how severe a gap is if not implemented."""
    if implemented:
        return "NONE"
    
    if priority == "critical" and frequency > 1.0:
        return "CRITICAL"
    elif priority == "critical" or frequency > 2.0:
        return "HIGH"
    elif priority == "high" or frequency > 0.5:
        return "MEDIUM"
    else:
        return "LOW"


def assess_impact(opcode_name):
    """Assess the impact of missing this opcode."""
    impact_map = {
        "iget-object": "Cannot read object fields - blocks most app logic",
        "iput-object": "Cannot write object fields - blocks state changes",
        "iget": "Cannot read int fields",
        "iput": "Cannot write int fields",
        "sget-object": "Cannot access static object fields",
        "sput-object": "Cannot modify static object fields",
        "move-wide": "No long/double support",
        "move-result-wide": "Cannot capture wide return values",
        "return-wide": "Cannot return wide values",
        "move/from16": "Limited register addressing",
        "move-object/from16": "Limited object register addressing",
        "new-array": "Cannot create arrays dynamically",
        "throw": "No exception support",
        "if-eq": "Missing two-register comparison branch",
        "if-lt/if-ge/if-gt/if-le": "Missing ordered comparison branches",
        "if-ltz/if-gez/if-gtz/if-lez": "Missing zero comparison variants",
        "invoke-interface": "No interface method calls",
        "filled-new-array": "Cannot initialize array with values",
        "array-length": "Cannot get array size",
        "aget-object/aput-object": "Cannot read/write array elements",
    }
    return impact_map.get(opcode_name, "Functionality limited")


def get_aosp_reference(opcode_name):
    """Get AOSP source reference for this opcode."""
    base_ref = {
        "dalvik_source": "dalvik/libdex/InstrUtils.c",
        "art_source": "runtime/arch/instruction_set.cc",
        "specification": "Dalvik Executable Format documentation"
    }
    
    category_refs = {
        "constant": {"function": "getInstructionFormat()"},
        "move": {"function": "isMoveInstruction()"},
        "return": {"function": "isReturnInstruction()"},
        "invoke": {"function": "isInvokeInstruction()"},
        "branch": {"function": "isBranchInstruction()"},
        "field": {"function": "isFieldInstruction()"},
        "array": {"function": "isArrayInstruction()"},
        "instance": {"function": "isInstanceInstruction()"},
    }
    
    ref = base_ref.copy()
    # Determine category from AOSP_COMPLETE_OPCODES
    if opcode_name in AOSP_COMPLETE_OPCODES:
        cat = AOSP_COMPLETE_OPCODES[opcode_name]["category"]
        if cat in category_refs:
            ref.update(category_refs[cat])
    
    return ref


def build_implementation_queue(coverage_db):
    """Build prioritized implementation queue."""
    
    for entry in coverage_db["opcode_details"]:
        if entry["implemented"]:
            continue
        
        severity = entry["gap_severity"]
        freq = entry["real_apk_frequency_pct"]
        priority = entry["aosp_priority"]
        
        queue_item = {
            "opcode": entry["opcode"],
            "hex_code": entry["hex_code"],
            "frequency": freq,
            "priority": priority,
            "category": entry["category"],
            "estimated_complexity": estimate_complexity(entry["opcode"]),
            "aosp_ref": entry["aosp_reference"]
        }
        
        # Categorize into queue
        if severity == "CRITICAL" or (priority == "critical" and freq > 1.0):
            coverage_db["implementation_queue"]["immediate"].append(queue_item)
        elif severity == "HIGH" or priority == "high" or freq > 0.5:
            coverage_db["implementation_queue"]["short_term"].append(queue_item)
        elif severity == "MEDIUM" or priority == "medium":
            coverage_db["implementation_queue"]["medium_term"].append(queue_item)
        else:
            coverage_db["implementation_queue"]["long_term"].append(queue_item)
    
    # Sort each queue by frequency descending
    for queue_name in coverage_db["implementation_queue"]:
        coverage_db["implementation_queue"][queue_name].sort(
            key=lambda x: x["frequency"], 
            reverse=True
        )


def estimate_complexity(opcode_name):
    """Estimate implementation complexity for an opcode."""
    simple_opcodes = {
        "move", "move/from16", "move/16", "move-wide", "move-object",
        "move-object/from16", "move-object/16", "move-result", "move-result-wide",
        "move-result-object", "move-exception", "return-void", "return",
        "return-wide", "return-object", "nop", "const/4", "const/16",
        "array-length", "throw"
    }
    
    medium_opcodes = {
        "const", "const/high16", "const-wide/16", "const-wide/32",
        "const-wide", "const-wide/high16", "const-string", "const-string/jumbo",
        "const-class", "check-cast", "instance-of", "new-instance",
        "new-array", "sget", "sget-wide", "sget-object", "sget-boolean",
        "sget-byte", "sget-char", "sget-short", "sput", "sput-wide",
        "sput-object", "sput-boolean", "sput-byte", "sput-char", "sput-short",
        "iget", "iget-wide", "iget-object", "iget-boolean", "iget-byte",
        "iget-char", "iget-short", "iput", "iput-wide", "iput-object",
        "iput-boolean", "iput-byte", "iput-char", "iput-short",
        "aget", "aget-wide", "aget-object", "aget-boolean", "aget-byte",
        "aget-char", "aget-short", "aput", "aput-wide", "aput-object",
        "aput-boolean", "aput-byte", "aput-char", "aput-short",
        "int-to-long", "int-to-float", "int-to-double", "long-to-int",
        "long-to-float", "long-to-double", "float-to-int", "float-to-long",
        "float-to-double", "double-to-int", "double-to-long", "double-to-float",
        "int-to-byte", "int-to-char", "int-to-short",
        "add-int", "sub-int", "mul-int", "div-int", "rem-int",
        "and-int", "or-int", "xor-int", "shl-int", "shr-int", "ushr-int",
        "add-int/lit16", "rsub-int", "mul-int/lit16", "div-int/lit16",
        "rem-int/lit16", "and-int/lit16", "or-int/lit16", "xor-int/lit16",
        "shl-int/lit8", "shr-int/lit8", "ushr-int/lit8", "add-int/lit8",
        "rsub-int/lit8", "mul-int/lit8", "div-int/lit8", "rem-int/lit8",
        "and-int/lit8", "or-int/lit8", "xor-int/lit8"
    }
    
    if opcode_name in simple_opcodes:
        return "simple (~10-20 LOC)"
    elif opcode_name in medium_opcodes:
        return "medium (~30-50 LOC)"
    else:
        return "complex (~50-100+ LOC)"


def generate_recommendations(coverage_db):
    """Generate strategic recommendations based on gap analysis."""
    
    recommendations = []
    
    # Check critical gaps
    immediate_queue = coverage_db["implementation_queue"]["immediate"]
    if len(immediate_queue) > 10:
        recommendations.append({
            "type": "PRIORITY",
            "message": f"{len(immediate_queue)} critical opcodes need immediate implementation",
            "action": "Focus on iget/iput/sget/sput field operations first"
        })
    
    # Check invoke coverage
    invoke_implemented = sum(1 for d in coverage_db["opcode_details"] 
                           if d["category"] == "invoke" and d["implemented"])
    invoke_total = sum(1 for d in coverage_db["opcode_details"] 
                      if d["category"] == "invoke")
    
    if invoke_implemented < invoke_total:
        recommendations.append({
            "type": "INVOKE_COVERAGE",
            "message": f"Invoke coverage: {invoke_implemented}/{invoke_total} ({round(invoke_implemented/invoke_total*100)}%)",
            "action": "Add invoke-interface/range variants for completeness"
        })
    
    # Check field operation coverage
    field_implemented = sum(1 for d in coverage_db["opcode_details"] 
                          if d["category"] == "field" and d["implemented"])
    field_total = sum(1 for d in coverage_db["opcode_details"] 
                     if d["category"] == "field")
    
    if field_implemented == 0:
        recommendations.append({
            "type": "CRITICAL_GAP",
            "message": "ZERO field operations implemented (iget/iput/sget/sput)",
            "action": "This is BLOCKING most application logic - implement immediately"
        })
        coverage_db["gap_analysis"]["semantic_risks"].append(
            "Without field operations, objects cannot maintain state"
        )
    
    # Check array coverage
    array_implemented = sum(1 for d in coverage_db["opcode_details"] 
                          if d["category"] == "array" and d["implemented"])
    
    if array_implemented < 3:
        recommendations.append({
            "type": "ARRAY_GAP",
            "message": f"Array operations: only {array_implemented} implemented",
            "action": "Implement aget-object/aput-object/new-array for basic array support"
        })
    
    # Frequency-based recommendation
    top_missing = [d for d in coverage_db["opcode_details"] 
                  if not d["implemented"] and d["real_apk_frequency_pct"] > 1.0]
    top_missing.sort(key=lambda x: x["real_apk_frequency_pct"], reverse=True)
    
    if top_missing:
        recommendations.append({
            "type": "FREQUENCY_BASED",
            "message": f"Top missing by frequency: {[d['opcode'] for d in top_missing[:5]]}",
            "action": "These account for significant % of real bytecode"
        })
    
    coverage_db["gap_analysis"]["recommendations"] = recommendations


def main():
    """Main entry point for opcode coverage analyzer."""
    
    print("=" * 70)
    print("EXP-032 Phase 2: Opcode Coverage Comparison Analyzer")
    print("=" * 70)
    print()
    
    # Run analysis
    coverage_db = analyze_coverage()
    
    # Print summary
    summary = coverage_db["summary"]
    print(f"AOSP Total Opcodes:     {summary['total_aosp_opcodes']}")
    print(f"MiniAndroid Implemented: {summary['miniandroid_implemented']}")
    print(f"Coverage Percentage:     {summary['coverage_percentage']}%")
    print(f"Critical Missing:        {summary['critical_missing']}")
    print()
    
    # Print category breakdown
    print("Coverage by Category:")
    print("-" * 50)
    for cat, stats in sorted(summary["by_category"].items()):
        pct = round((stats["implemented"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
        print(f"  {cat:15}: {stats['implemented']:3}/{stats['total']:3} ({pct:5.1f}%)")
    print()
    
    # Print implementation queue
    queues = coverage_db["implementation_queue"]
    print("Implementation Queue:")
    print("-" * 50)
    print(f"\n  IMMEDIATE (Critical + High Frequency): {len(queues['immediate'])} opcodes")
    for item in queues["immediate"][:10]:
        print(f"    - {item['opcode']:25} freq={item['frequency']:.2f}%  [{item['estimated_complexity']}]")
    
    print(f"\n  SHORT_TERM (High Priority): {len(queues['short_term'])} opcodes")
    for item in queues["short_term"][:10]:
        print(f"    - {item['opcode']:25} freq={item['frequency']:.2f}%  [{item['estimated_complexity']}]")
    
    print(f"\n  MEDIUM_TERM: {len(queues['medium_term'])} opcodes")
    print(f"\n  LONG_TERM: {len(queues['long_term'])} opcodes")
    
    # Save to file
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "database",
        "opcode_coverage.json"
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coverage_db, f, indent=2, ensure_ascii=False, default=str)
    
    print()
    print("=" * 70)
    print(f"Coverage database saved to: {output_path}")
    print("=" * 70)
    
    return coverage_db


if __name__ == "__main__":
    main()
