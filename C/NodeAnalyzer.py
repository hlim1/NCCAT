"""
    This file holds functions for analyzing nodes.

    Author: Terrence J. Lim
"""

import os, sys
import json
import copy
import subprocess

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

def qualifier_analyzer(node: dict, ast_0_node: dict):
    """
    """

    assert "quals" in ast_0_node, f"ERROR: {ast_0_node} does not have 'quals' attribute."

    ast_0_node_quals = ast_0_node["quals"]

    quals = None
    assert "quals" in node, f"ERROR: {node} does not have 'quals' attribute"
    if node["quals"] != ast_0_node_quals:
        quals = node["quals"]

    return quals, ast_0_node_quals

def constant_analyzer(node: dict, ast_0_node: dict):
    """
    """

    assert "value" in ast_0_node, f"ERROR: {ast_0_node} does not have 'value' attribute."

    ast_0_node_value = ast_0_node["value"]

    value = None
    assert "value" in node, f"ERROR: {node} does not have 'value' attribute."
    if node["value"] != ast_0_node_value:
        value = node["value"]

    return value, ast_0_node_value

def operator_analyzer(node: dict, ast_0_node: dict):
    """
    """

    assert "op" in ast_0_node, f"ERROR: {ast_0_node} does not have 'operator' attribute."

    ast_0_node_op = ast_0_node["op"]

    op = None
    assert "op" in node, f"ERROR: {node} does not have 'op' attribute."
    if node["op"] != ast_0_node_op:
        op = node["op"]

    return op, ast_0_node_op

def identifier_type_analyzer(node: dict, ast_0_node: dict):
    """
    """

    assert "names" in ast_0_node, f"ERROR: {ast_0_node} does not have 'names' attribute."

    ast_0_node_names = ast_0_node["names"]

    type_name = None
    assert "names" in node, f"ERROR: {node} does not have 'names' attribute."
    if node["names"][0] != ast_0_node_names[0]:
        type_name = node["names"][0]

    return type_name, ast_0_node_names[0]

def goto_analyzer(node: dict, ast_0_node: dict):
    """
    """
    
    assert "name" in ast_0_node, f"ERROR: {ast_0_node} does not have 'name' attribute."

    ast_0_node_label = ast_0_node["name"]

    goto_label = None
    assert "name" in node, f"ERROR: {node} does not have 'name' attribute"
    if goto_label != ast_0_node_node_label:
        goto_label = node["name"]

    return goto_label, ast_0_node_label
