#!/usr/bin/env python3

#  ----------------------------------------------------------------------------
# Name:         conn.py
# Purpose:      Connection to group of nodes
#
# Author:       Sergey Shafranskiy <sergey.shafranskiy@gmail.com>
#
# Version:      1.1.4
# Build:        167
# Created:      2019-01-11
# ----------------------------------------------------------------------------

from abc import ABC, abstractmethod
from lxml import etree as et
from typing import Callable
from functools import reduce

# In-application tracing messages

CONF_READ_ERR = "Configuration loading error, file: '{}'"

CONN_START = "Connecting to '{}'"
CONN_OK = " OK"
CONN_FAILED = " FAILED"
CONN_CLOSED = "Connection to '{}' was closed"

INFO_SEARCH = "Search for '{0}' in '{1}' with date >= '{2}'"
INFO_EXEC_CMD = "Execute command '{}'"
INFO_OPERATION_COMPLETED = 'Operation completed, {} line(s) found'

TracingFun = Callable[[str], None]


class SortPattern():
    """
    Sorting pattern
    """

    def __init__(self, expr: str, is_active: bool):
        """
        Class constructor

        :param expr: Regex for sorting key extracting
        :param is_active: Is sorting active?
        """
        self.expr = expr
        self.is_active = is_active


class ColumnPattern():
    """
    Column pattern
    """

    def __init__(self, name: str, expr: str, is_main: bool):
        """
        Class constructor

        :param name: Column name
        :param expr: Regex for column value extracting
        :param is_main: Is main column?
        """
        self.name = name
        self.expr = expr
        self.is_main = is_main


# List of column patterns
ColumnPatterns = [ColumnPattern]


class Patterns():
    """
    Patterns (sorting, [columns])
    """
    def __init__(self, sort: SortPattern, msg_columns: ColumnPatterns):
        """
        Class constructor

        :param sort: Sorting pattern
        :param msg_columns: List of column patterns
        """
        self.sort = sort
        self.msg_columns = msg_columns


class OutField():
    """
    Output formatting field
    """

    def __init__(self, name: str, is_xml: bool):
        """
        Class constructor

        :param name: Field name
        :param is_xml: Field contains XML value?
        """
        self.name = name
        self.is_xml = is_xml


# List of output formatting fields
OutFields = [OutField]


class Source():
    """
    Source to which the search is applied
    """

    def __init__(self, name: str, source_name: str, expr: str, fields: OutFields):
        """
        Class constructor

        :param name: Source name (in case file search - the file mask)
        :param expr: Source expression: unix command, sql statement etc.
        :param fields: Output formatting fields
        """
        self.name = name
        self.source_name = source_name
        self.expr = expr
        self.fields = fields


# List of sources
Sources = [Source]


class ConnABC(ABC):
    """
    Low-level connection to source, abstract class
    """

    @abstractmethod
    def connect(self, **conn_args):
        """
        Connecting to source

        :param conn_args: Connection parameters
        """
        return None

    @abstractmethod
    def exec_cmd(self, cmd: str) -> [str]:
        """
        Executing command on open connection

        :param cmd: command string
        :return: stdout list of str
        """
        return None

    @abstractmethod
    def close(self):
        """
        Closing connection
        """
        return None


class Node(ABC):
    """
    Node (Source instance: server, database etc.)
    """

    def __init__(self, trace_fun: TracingFun, name: str, **conn_args):
        """ Class constructor

        :param name: Node name (shown in GUI)
        :param trace_fun: Callback tracing function
        :param conn_args: Connection parameters
        """
        self.name = name
        self.trace_fun = trace_fun
        self.conn_args = conn_args

        self.conn = self.create_conn()  # Create low-level connection instance
        self.connected: bool = False  # is connected?

    def create_conn(self):
        """
        Create low-level connection
        :return:
        """
        return ConnABC()

    def connect(self) -> bool:
        """
        Establish connection to node

        :return: bool, Connect status
        """
        trace_str = ""
        try:
            trace_str = CONN_START.format(self.conn_args['node_name'])
            self.conn.connect(**self.conn_args)

        except Exception as ex:
            self.connected = False
            trace_str += CONN_FAILED + ", [" + ", ".join([str(arg) for arg in ex.args]) + "]"
        else:
            self.connected = True
            trace_str += CONN_OK

            return self.connected
        finally:
            if self.trace_fun:
                self.trace_fun(trace_str, not self.connected)

    def prepare_in_cmd(self, source, cmd):
        """
        Prepare executing command

        :param source: Source
        :param cmd: Input command
        :return: Output command
        """
        return cmd

    def prepare_out_str(self, out, source: Source) -> [str]:
        """
        Prepare output string (search result)

        :param source: Source
        :param out: Output structure
        :return: Output list of strings
        """
        return out

    def exec_cmd(self, source, cmd: str) -> [str]:
        """
        Execute command on node

        :param source: Source
        :param cmd: Command
        :return: Stdout, list
        """
        res_lst = []
        if self.conn is not None:
            if self.trace_fun:
                self.trace_fun(INFO_EXEC_CMD.format(cmd))
            try:
                cmd_prepared = self.prepare_in_cmd(source, cmd)
                out = self.conn.exec_cmd(cmd_prepared)
                out_list = self.prepare_out_str(out, source)
                res_lst.extend(out_list)
            except Exception as ex:
                res_lst.clear()

        return res_lst

    def prepare_search_cmd(self, source: Source, search_str: str, search_date: str) -> str:
        """
        Prepare search command

        :param source: Source
        :param search_str: Search string
        :param search_date:  Search date in format "YYYY-MM-DD".\
                 - used  for search in files with modification date >= search_date
        :return: Output command
        """
        cmd = source.expr
        repl_params = (r'{{source_name}}', source.source_name), \
                      (r'{{search_str}}', search_str), \
                      (r'{{search_date}}', search_date)
        for r in repl_params:
            cmd = cmd.replace(*r)

        return cmd

    def search(self, source: Source, search_str: str, search_date: str) -> [str]:
        """
        Do search for _search_str_ in file(s) with file name mask _search_file_ with date >= _search_date_

        :param source: Source
        :param search_str: Search string
        :param search_date: Search date in format "YYYY-MM-DD", used if not empty for search with date >= search_date
        :return: Search result, List [str]
        """
        res_lst = []
        if self.conn is not None:
            """              
            if self.trace_fun:
                self.trace_fun(INFO_SEARCH.format(search_str=search_str, source_name=source.source_name, search_date=search_date))
            """
            cmd = self.prepare_search_cmd(source, search_str, search_date)
            out_list = self.exec_cmd(source, cmd)
            res_lst.extend(out_list)

        return res_lst

    def close(self):
        """
        Close SSH connection
        """
        if (self.conn is not None) and self.connected:
            self.conn.close()

            if self.trace_fun:
                self.trace_fun(CONN_CLOSED.format(self.conn_args['node_name']))


# List of nodes
Nodes = [Node]


class NodeGroup:
    """
    Group of nodes
    """

    def __init__(self, trace_fun: TracingFun, name: str, ng_type: str, nodes: Nodes, sources: Sources,
                 patterns: Patterns):
        """
        Class constructor

        :param trace_fun: Callback tracing function
        :param name: External name of node group
        :param ng_type: Type of nodegroup ('file', 'database')
        :param nodes: Nodes in node group
        :param sources: Sources
        :param patterns: Regex patterns used to sort and present message data
        """
        self.trace_fun = trace_fun

        self.name = name
        self.type = ng_type
        self.nodes = nodes
        self.sources = sources
        self.patterns = patterns

        self.p_sort = None  # compiled sorting regex
        self.is_sort_active = False  # is sorting active

    def get_node_names(self) -> [str]:
        """
        Get names of all nodes

        :return: Names of nodes
        """
        return [node.name for node in self.nodes]

    def get_node(self, name: str) -> Node:
        """
        Get node by name

        :param name: Node name
        :return: Node
        """
        res = None
        for node in self.nodes:
            if node.name == name:
                res = node
                break
        return res

    def get_source_items(self) -> [[str, str]]:
        """
        Get names of all sources

        :return: Names of sources
        """
        return [[src.name, src.source_name] for src in self.sources]

    def get_source(self, source_name: str) -> str:
        """
        Get source by name

        :param name: Source name
        :return: Source
        """
        src_lst = [src for src in self.sources if src.name == source_name]
        return src_lst[0]

    def sort_fun(self, line: str) -> str:
        """
        Extract sorting key from 'line'

        :param line:
        :return: sorting key
        """
        return line  # by default sorting by whole line

    def exec_cmd(self, source_name: str, cmd: str) -> [str]:
        """
        Execute command

        :param source_name: Source name
        :param cmd: Command
        :return: Command output
        """
        source = self.get_source(source_name)

        res_lst = []
        n_active_nodes = 1
        for node in self.nodes:
            is_connected = node.connect()
            if is_connected:
                n_active_nodes += 1
                res_lst.extend(node.exec_cmd(source, cmd))
                node.close()
        if self.trace_fun:
            self.trace_fun(INFO_OPERATION_COMPLETED.format(len(res_lst)))
        return res_lst

    def search(self, source_name: str, search_str: str, search_date: str) -> [str]:
        """
        Search

        :param source_name: Source name
        :param search_str: Search string
        :param search_date: Search date
        :return: Search output
        """
        if self.trace_fun:
            self.trace_fun(INFO_SEARCH.format(search_str, source_name, search_date))

        source = self.get_source(source_name)

        res_lst = []
        n_active_nodes = 1
        for node in self.nodes:
            is_connected = node.connect()
            if is_connected:
                n_active_nodes += 1
                res_lst.extend(node.search(source, search_str, search_date))
                node.close()

        if self.is_sort_active and (n_active_nodes > 0):
            res_lst = sorted(res_lst, key=self.sort_fun)

        if self.trace_fun:
            self.trace_fun(INFO_OPERATION_COMPLETED.format(len(res_lst)))
        return res_lst


# List of NodeGroups
NodeGroups = [NodeGroup]


class Connection:
    """
    Source connection
    """

    def __init__(self, conf_filename: str, trace_fun: TracingFun = None):
        """
        Class constructor

        :param conf_filename: Configuration file name (*.config.xml)
        :param trace_fun: Callback tracing function
        """
        self.conf_filename = conf_filename
        self.trace_fun = trace_fun

        self.nodegroups: NodeGroups = []

        try:
            # Load xml config file
            tree = et.parse(conf_filename)
            self.parse_xml_config(tree)

        except Exception as ex:
            if self.trace_fun:
                self.trace_fun(CONF_READ_ERR.format(conf_filename) + ", ".join([str(arg) for arg in ex.args]))
            raise ex

    @abstractmethod
    def parse_xml_config(self, tree: et._ElementTree):
        """
        Read configuration

        :param tree: root of xml tree
        :return:
        """
        pass

    def get_nodegroup_names(self) -> [str]:
        """
        Get names of all nodegroups

        :return: Nodegroups names
        """
        return [ng.name for ng in self.nodegroups]

    def get_nodegroup(self, name: str) -> NodeGroup:
        """
        Get nodegroup by name

        :param name: Name of nodegroup
        :return: Nodegroup
        """
        res = None
        for ng in self.nodegroups:
            if ng.name == name:
                res = ng
        return res

    def exec_cmd(self, ng_index: int, source_name: str, cmd: str) -> [str]:
        """
        Execute command

        :param ng_index: Index of active nodegroup
        :param source_name: Source name
        :param cmd: Command
        :return: Command output
        """
        nodegroup = self.nodegroups[ng_index]
        return nodegroup.exec_cmd(source_name, cmd)

    def search(self, ng_index: int, source_name: str, search_str: str, search_date: str) -> [str]:
        """
        Search

        :param ng_index: ng_index: Index of active nodegroup
        :param source_name: Source name
        :param search_str: Search string
        :param search_date: Search date
        :return: Search output
        """
        nodegroup = self.nodegroups[ng_index]
        return nodegroup.search(source_name, search_str, search_date)
