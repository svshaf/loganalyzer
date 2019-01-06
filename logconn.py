#!/usr/bin/env python3

#  ----------------------------------------------------------------------------
# Name:         logconn.py
# Purpose:      Connection to sources (ssh connect. to nodes, connect. to databases)
#
# Author:       Sergey Shafranskiy <sergey.shafranskiy@gmail.com>
#
# Version:      1.1.3
# Build:        164
# Created:      2018-12-16
# ----------------------------------------------------------------------------

import re
import paramiko
from yattag import indent
from lxml import etree as et
import cx_Oracle

import conn

# In-application tracing strings

INFO_GET_LOG_PART = "Get lines from {} to {} from file'{}'"
INFO_SEARCH_EXT = "Extended search for '{}' in files '{}' with date >= '{}'"

CONF_ERR_MISSING_TAG = "Missing configuration parameter, file: '{0}', path: '{1}', tag: '{2}'"
CONF_ERR_MISSING_ATTR = "Missing configuration attribute, file: '{0}', path: '{1}', attribute: '{2}'"


class ExConfErrorMissingTag(Exception):
    def __init__(self, file, path, tag):
        # Call the base class constructor with the parameters it needs
        self.message = CONF_ERR_MISSING_TAG.format(file, path, tag)


class ExConfErrorMissingAttr(Exception):
    def __init__(self, file, path, attr):
        # Call the base class constructor with the parameters it needs
        self.message = CONF_ERR_MISSING_ATTR.format(file, path, attr)


class SSHNodeConn(conn.ConnABC):
    """
    Connection to file node
    """

    def __init__(self):
        """
        Class constructor
        """
        self.conn = paramiko.SSHClient()
        self.conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, **conn_args):
        """
        Connect
        :param conn_args: connection arguments
        :return:
        """
        if not conn_args.get('key_filename', None):
            self.conn.connect(hostname=conn_args['node_name'], username=conn_args['user'],
                              password=conn_args['password'],
                              look_for_keys=False)
        else:
            pkey = paramiko.RSAKey.from_private_key_file(filename=conn_args['key_filename'],
                                                         password=conn_args['key_password'])
            self.conn.connect(hostname=conn_args['node_name'], username=conn_args['user'], pkey=pkey)

    def exec_cmd(self, cmd) -> str:
        """
        Execute command

        :param cmd: command string
        :return: command output
        """
        _, stdout, _ = self.conn.exec_command(cmd)
        return stdout.readlines()

    def close(self):
        """
        Close connection

        :return:
        """
        self.conn.close()


class SSHNode(conn.Node):
    """
    File node
    """

    def __init__(self, trace_fun: conn.TracingFun, name: str, node_name: str, user, password, remote_dir,
                 key_filename, key_password):
        """
        Class constructor

        :param trace_fun: Callback tracing function
        :param name: External node name
        :param node_name: Node name or IP address
        :param user: User name
        :param password: User password
        :param remote_dir: Remote directory
        :param key_filename: Private key file name
        :param key_password: Private key password

        """
        super().__init__(trace_fun, name, node_name=node_name, user=user, password=password, remote_dir=remote_dir,
                         key_filename=key_filename, key_password=key_password)

    def create_conn(self):
        return SSHNodeConn()

    def prepare_in_cmd(self, source, cmd):
        """ Prepare/extend executing command

        :param source: Source
        :param cmd: Input command
        :return: Output command
        """
        remote_dir = self.conn_args['remote_dir']
        return 'cd ' + remote_dir + '\n' + cmd


class SSHNodeGroup(conn.NodeGroup):
    """
    File node group
    """
    def __init__(self, trace_fun: conn.TracingFun, name: str, ng_type: str, nodes: conn.Nodes,
                 sources: conn.Sources, patterns: conn.Patterns):
        """
        Class constructor

        :param trace_fun: Callback tracing function
        :param name: External name of node group
        :param ng_type: Type of nodegroup ('file', 'database')
        :param nodes: Nodes in node group
        :param sources: Sources
        :param patterns: Regex patterns used to sort and present message data
        """
        super().__init__(trace_fun, name, ng_type, nodes, sources, patterns)

        pt_sort: conn.SortPattern = self.patterns.sort
        if pt_sort is not None:
            if pt_sort.expr is not None:
                self.p_sort = re.compile(pt_sort.expr)
            else:
                self.p_sort = None
            self.is_sort_active = pt_sort.is_active
        else:
            self.p_sort = None
            self.is_sort_active = False

    def sort_fun(self, line):
        """
        Extract datetime from message line, e.g.
        ./server.log:132649:2018-11-02 15:26:13,349 DEBUG... -> 2018-11-02 15:26:13,349

        :param line: input line
        :return: sorting key
        """
        key = line
        if self.p_sort is not None:
            m = self.p_sort.match(line)
            if m:
                key = m.group(1)
        return key


class SQLNodeConn(conn.ConnABC):
    """
    Connection to database
    """

    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self, **conn_args):
        if conn_args['sid'] != "":
            dns = cx_Oracle.makedsn(*(conn_args['node_name'].split(':', 2)), sid=conn_args['sid'])

        else:
            dns = cx_Oracle.makedsn(*(conn_args['node_name'].split(':', 2)), service_name=conn_args['service_name'])

        self.conn = cx_Oracle.connect(conn_args['user'], conn_args['password'], dns)

        self.cursor = self.conn.cursor()

    def exec_cmd(self, cmd):
        try:
            self.cursor.execute(cmd)
            res = self.cursor.fetchall()
        except Exception as ex:
            res = None
        return res

    def close(self):
        self.cursor.close()
        self.conn.close()


class SQLNode(conn.Node):
    """
    Database node
    """

    def __init__(self, trace_fun: conn.TracingFun, name: str, node_name: str, user: str, password: str, sid: str,
                 service_name: str):
        """
        Class constructor

        :param trace_fun: Callback tracing function
        :param name: External db name
        :param node_name: Database name or IP address
        :param user: User name
        :param password: User password
        :param sid: Service Id, or
        :param service_name: Service name

        """
        super().__init__(trace_fun, name, node_name=node_name, user=user, password=password, sid=sid,
                         service_name=service_name)

    def create_conn(self):
        return SQLNodeConn()

    def prepare_out_str(self, out, source: conn.Source) -> [str]:
        res_list = []
        if out:
            for row in out:
                row_str = ""
                for i, col in enumerate(row):
                    field: conn.OutField = source.fields[i]
                    if not field.is_xml:  # is not XML
                        row_str += field.name + ":'" + str(col) + "' "
                    else:
                        row_str += "\n" + field.name + ":\n" + indent(str(col)) + "\n"
                res_list.append(row_str + "\n--------------------------------------\n")
        return res_list


class LogConnection(conn.Connection):
    """
    Log connection
    """

    def __init__(self, conf_filename: str, trace_fun: conn.TracingFun = None):
        """
        Class constructor

        :param conf_filename: Configuration file name (*.config.xml)
        :param trace_fun: Callback tracing function
        """
        self.tree = None
        self.keys = {}
        self.nodegroups = []
        super().__init__(conf_filename, trace_fun)

    def get_tag(self, e, tag):
        """
        Get tag element
        :param e: parent element
        :param tag: tag name
        :return: tag element
        """
        res = e.find(tag)
        if res is None:
            raise ExConfErrorMissingTag(self.conf_filename, self.tree.getpath(e), tag)
        return res

    def get_attr(self, e, attr):
        """
        Get attribute value of element
        :param e: element
        :param attr: attribute name
        :return:
        """
        res = e.get(attr)
        if not res:
            raise ExConfErrorMissingAttr(self.conf_filename, self.tree.getpath(e), attr)
        return res

    def parse_xml_config(self, tree: et._ElementTree):
        """
        Read configuration

        :param tree: root of xml tree
        :return:
        """
        self.tree = tree

        root = tree.getroot()
        try:
            # Read ssh keys

            self.keys = {}
            for e in root.findall('./ssh-keys/key'):
                key_name = self.get_attr(e, 'name')
                key_filename = self.get_attr(e, 'file-name')
                key_password = e.get('password', '')
                self.keys[key_name] = [key_filename, key_password]

            # Read nodegroups

            self.nodegroups = []
            for eg in root.findall('./nodegroups/nodegroup'):
                ng_name = self.get_attr(eg, 'name')
                ng_type = eg.get('type', 'file')
                nodes = []
                for e in eg.iterchildren('node'):
                    node = []
                    name = self.get_attr(e, 'name')
                    node_name = self.get_attr(e, 'node-name')
                    user = self.get_attr(e, 'user')
                    password = e.get('password')

                    if ng_type == 'file':
                        remote_dir = self.get_attr(e, 'remote-dir')
                        key_name = e.get('key-name')
                        key_filename = ""
                        key_password = ""
                        if key_name:
                            k = self.keys[key_name]
                            if k:
                                key_filename = k[0]
                                key_password = k[1]

                        node = SSHNode(self.trace_fun, name, node_name, user, password, remote_dir, key_filename,
                                       key_password)
                    elif ng_type == 'database':
                        sid = e.get('sid')
                        service_name = e.get('service-name')

                        node = SQLNode(self.trace_fun, name, node_name, user, password, sid, service_name)

                    if node:
                        nodes.append(node)

                sources: [conn.Source] = []
                es = self.get_tag(eg, 'sources')
                for e in es.iterchildren('source'):
                    name = self.get_attr(e, 'name')

                    expr_fields = []
                    fields = e.get('fields')
                    if fields:
                        for f in fields.split(','):
                            fpair = f.strip().split(':')
                            is_xml = True if len(fpair) == 2 and fpair[1] == 'xml' else False
                            expr_fields.append(conn.OutField(fpair[0], is_xml))
                    expr = e.text
                    sources.append(conn.Source(name, expr, expr_fields))

                ep = self.get_tag(eg, 'patterns')

                """ 'sort' section:
                tag is not present - sorting not active
                "active" attr. is present: value "1" - sorting active, "0" - sorting not active
                "active" attr. is NOT present: implies default value "0" - sorting not active
                empty tag text - sorting by whole line
                """
                e = ep.find('sort')
                if e is not None:
                    sort_active = e.get('active', '1')
                    sort_text = e.text
                else:
                    sort_active = '0'
                    sort_text = ''
                pt_sort = conn.SortPattern(sort_text, bool(int(sort_active)))

                pt_msg_columns: conn.ColumnPatterns = []
                for e in ep.iterchildren('msg-column'):
                    name = self.get_attr(e, 'name')
                    is_main = e.get('main', '0')
                    pt_msg_columns.append(conn.ColumnPattern(name, e.text, bool(int(is_main))))

                patterns = conn.Patterns(pt_sort, pt_msg_columns)
                self.nodegroups.append(SSHNodeGroup(self.trace_fun, ng_name, ng_type, nodes, sources, patterns))

        except ExConfErrorMissingTag as ex:
            self.trace_fun(ex.message)

        except ExConfErrorMissingAttr as ex:
            self.trace_fun(ex.message)

    def get_file_part(self, ng_index, source_name, file_name, num_from, num_to):
        """
        Get part of file by line number

        :param ng_index: Index of active nodegroup 
        :param source_name: Source name
        :param file_name: Source file name
        :param num_from: Number of starting line
        :param num_to: Number of ending line
        """

        # command format:
        # awk '(NR >= 12630) && (NR <= 12680) {print FILENAME, ":", FNR, ":", $0}' './server.log'
        if num_from <= 0:
            num_from = 0
        cmd = r'''awk '(NR >= %d) && (NR <= %d) {print FILENAME ":" FNR ":" $0}' '%s' ''' \
              % (num_from, num_to, file_name)

        self.trace_fun(INFO_GET_LOG_PART.format(num_from, num_to, file_name))

        return self.exec_cmd(ng_index, source_name, cmd)

    def search_extended(self, ng_index, source_name, search_str, search_date):
        """
        Extended search in sources

        """
        # command format:
        # find . -maxdepth 1 -type f -name "server.log*" -newermt "2018-09-18" -exec cat {} /dev/null \;
        # | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}/\n\n&/'
        # | awk 'BEGIN { RS = "\n\n"; ORS=""} /TMO951f53ef-b4f4-4d0d-acff-552710a69d26/ {print}'
        # \n\n -> #$@#$@
        cmd = (r'''find . -maxdepth 1 -type f -name "%s" ''' +
               (r'''-newermt "%s" ''' % search_date if search_date else '') +
               r'''-exec cat {} /dev/null \; | ''' +
               r'''awk 'NF' |'''
               r'''sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}/\n\n&/' | ''' +
               r'''awk 'BEGIN { RS = "\n\n"; ORS=""} /%s/ {print}' ''') % (source_name, search_str)

        self.trace_fun(INFO_SEARCH_EXT.format(search_str, source_name, search_date))

        return self.exec_cmd(ng_index, source_name, cmd)
