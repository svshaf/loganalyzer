#!/usr/bin/env python3

#  ----------------------------------------------------------------------------
# Name:         loganalyzer.py
# Purpose:      Extract logs from different sources (files on groups of nodes nodes, databases)
#
# Author:       Sergey Shafranskiy <sergey.shafranskiy@gmail.com>
#
# Version:      1.1.4
# Build:        166
# Created:      2019-01-11
# ----------------------------------------------------------------------------

import wx
import wx.aui as aui

import re
from datetime import datetime
from yattag import indent
from lxml import etree as et

import loganalyzer_gui
import logconn
import logxmlstc
import msglist

# Max count of elements in search history
MAX_SEARCH_HISTORY = 15


class MainFrame(loganalyzer_gui.LogAnalyzerFrame):
    """
    Main frame class
    """

    # self.conn: logconn.LogConnection - Connection to log sources
    # self.text_lst: [str] - Text extracted from source
    # self.text_lst_shown: [str] - Processed text, shown in GUI

    def __init__(self, parent):
        """
        Class constructor
        """

        super(MainFrame, self).__init__(parent)

        self.exec_module_name = __file__.rsplit(".", 1)[0]  # executing module name w/o extension

        # set window's icon
        icon = wx.Icon(self.exec_module_name + ".ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Dynamically create StyledTextCtrl and ListCtrl widgets
        self.stc_OutLog = logxmlstc.LogXmlSTC(self, self.pn_OutLog)
        self.lc_OutMsg = msglist.MsgListCtrl(self, self.pn_OutMsg)

        self.adjust_nb_tab_close_flag()

        self.text_lst = []
        self.text_lst_shown = []

        # Read configuration
        conf_filename = self.exec_module_name + ".config.xml"
        self.conn = logconn.LogConnection(conf_filename, self.write_trace)

        # Setup GUI controls
        self.fill_nodegroups()
        self.cb_NodeGroups_OnChoice(None)

        self.read_state(self.exec_module_name + ".data.xml")  # Restore GUI settings

    def MainFrame_OnClose(self, event):
        """
        Frame is closing
        """

        self.write_state(self.exec_module_name + ".data.xml")  # Save GUI settings
        event.Skip()

    def cb_NodeGroups_OnChoice(self, event):
        """
        New nodegroup selected in GUI
        """

        self.stc_OutLog.ClearSelections()
        self.stc_OutLog.ClearAll()

        self.nb_OutLog.SetSelection(0)  # switch to 'Log' tab in AuiNotebook

        self.fill_sources(0)  # fill sources from selected nodegroup

        self.lc_OutMsg.init_columns(
            self.selected_nodegroup().patterns.msg_columns)  # init columns on 'Messages' tab of AuiNotebook

    def nb_OutLog_OnPageChanged(self, event):
        """
        AuiNotebook tab changed: set/remove 'x' button on tab changing
        """
        self.adjust_nb_tab_close_flag()

    def nb_OutLog_OnPageClosed(self, event):
        """
        AuiNotebook tab closed
        """

        nb: wx.aui.AuiNotebook = event.GetEventObject()
        tab_index = nb.GetSelection()

        if tab_index >= 2:  # First two tabs ('Log', 'Messages') are fixed
            nb.RemovePage(tab_index)
            nb.DeletePage(tab_index)

    def bt_Search_OnBtnClick(self, event):
        """
        'Search' button pressed
        """

        source_name = self.cb_Sources.GetStringSelection()
        self.ch_SearchText_OnTextEnter(None)
        search_str = self.ch_SearchText.GetValue()
        search_date = self.selected_date()

        self.do_search(source_name, search_str, search_date)

    def ch_SearchText_OnRightUp(self, event):
        """
        Right mouse click in search field: insert text from clipboard
        """

        data_o = wx.TextDataObject()
        if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
            if wx.TheClipboard.GetData(data_o):
                self.ch_SearchText.SetValue(data_o.GetText())
            wx.TheClipboard.Close()

    def ch_SearchText_OnComboBox(self, event):
        """

        :param event:
        :return:
        """
        index = self.ch_SearchText.GetSelection()
        if index != 0:
            value = self.ch_SearchText.GetString(index)
            self.ch_SearchText.Delete(index)
            self.ch_SearchText.Insert(value, 0)
            self.ch_SearchText.SetSelection(0)
        return

    def ch_SearchText_OnTextEnter(self, event):
        """

        :param event:
        :return:
        """
        value = self.ch_SearchText.GetValue()
        index = self.ch_SearchText.FindString(value)
        if index != -1:
            self.ch_SearchText.Delete(index)
        self.ch_SearchText.Insert(value, 0)
        self.ch_SearchText.SetSelection(0)
        return

    def write_trace(self, text: str, is_error: bool = False):
        """
        Write trace message

        :param text: Text to write
        :param is_error: bool = True - is error message
        """

        if is_error:
            self.rt_Status.BeginTextColour((255, 0, 0))
        else:
            self.rt_Status.BeginTextColour((0, 0, 0))

        self.rt_Status.WriteText(text + "\n")

        self.rt_Status.EndTextColour()
        self.rt_Status.Update()

    def selected_nodegroup_index(self):
        """
        Index of selected nodegroup
        """
        return self.cb_NodeGroups.GetSelection()

    def selected_nodegroup(self):
        """
        Selected nodegroup
        """
        return self.conn.nodegroups[self.cb_NodeGroups.GetSelection()]

    def selected_date(self):
        """
        Get date from GUI in string format 'YYYY-MM-DD'
        """
        return self.dt_SearchDate.GetValue().GetDateOnly().FormatISODate()

    def fill_nodegroups(self):
        """
        Fill combobox with nodegroup names
        """

        self.cb_NodeGroups.Clear()
        self.cb_NodeGroups.AppendItems(self.conn.get_nodegroup_names())

        self.cb_NodeGroups.SetSelection(0)
        self.fill_sources(0)

    def fill_sources(self, index=0):
        """
        Fill combobox with source names of selected nodegroup

        :param index: selection in sources list
        """

        self.cb_Sources.Clear()
        src_items = self.selected_nodegroup().get_source_items()
        [self.cb_Sources.Append(*v) for v in src_items]

        if index not in range(self.cb_Sources.GetCount()):
            src_index = 0
        self.cb_Sources.SetSelection(index)

    def adjust_nb_tab_close_flag(self):
        """
        Set/remove 'x' button of AuiNotebook tab
        (closing of tab allowed only for tabs with index >=2)

        :param widget:
        """

        index = self.nb_OutLog.GetSelection()
        flag = self.nb_OutLog.GetWindowStyle()
        if index in [0, 1]:
            flag &= ~aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
        else:
            flag |= aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
        self.nb_OutLog.SetWindowStyle(flag)

    def create_msg_tab(self, msg_index, title):
        """
        Create new tab with XML text of message that was selected in grid

        :param msg_index: Index of message in message grid
        :param title: Title of new tab
        """

        if self.text_lst_shown and msg_index >= 0:
            xml_line = indent(self.text_lst_shown[msg_index])  # message string

            # Create StyledTextCtrl pane with XML syntax highlighting

            panel = wx.Panel(self.nb_OutLog, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
            box_sizer = wx.BoxSizer(wx.HORIZONTAL)
            stc = logxmlstc.LogXmlSTC(self, panel)
            box_sizer.Add(stc, 1, wx.EXPAND | wx.ALL, 5)
            panel.SetSizer(box_sizer)
            panel.Layout()
            box_sizer.Fit(panel)

            stc.SetText(''.join(xml_line))

            self.nb_OutLog.AddPage(panel, title, True, wx.NullBitmap)

    def create_multi_msg_tag(self, msg_index, tag='correlationId'):
        """
        Create new tab with XML text of  all messages that contain same tag value as message that was selected in grid

        :param msg_index: Index of message in message grid
        :param tag: Tag name
        """

        if self.text_lst_shown and msg_index >= 0:
            xml_line = indent(self.text_lst_shown[msg_index])
            cor_id = MainFrame.get_tag_value(xml_line, tag)

            xml_text = []
            cnt = 0
            for line in self.text_lst_shown:
                if MainFrame.get_tag_value(line, tag) == cor_id:
                    xml_line = indent(line)
                    xml_text.append(xml_line)
                    cnt += 1

            self.stc_OutLog.AppendText(''.join(xml_text))
            self.stc_OutLog.Update()

            tab_title = cor_id + " ({0})".format(cnt)

            # Create StyledTextCtrl pane with XML syntax highlighting
            # pn_OutLog is parent of stc_OutLog: StyledTextCtrl
            panel = wx.Panel(self.nb_OutLog, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
            box_sizer = wx.BoxSizer(wx.HORIZONTAL)
            stc = logxmlstc.LogXmlSTC(self, panel)
            box_sizer.Add(stc, 1, wx.EXPAND | wx.ALL, 5)
            panel.SetSizer(box_sizer)
            panel.Layout()
            box_sizer.Fit(panel)

            stc.SetText(''.join(xml_text))

            self.nb_OutLog.AddPage(panel, tab_title, True, wx.NullBitmap)

    @staticmethod
    def get_tag_value(text, tag):
        """
        Get value of tag from XML message

        :param text: XML message text
        :param tag: Tag name
        :return: Tag value
        """

        pattern = r"(?:.*<.*?:{0}>)(.+?)(?:<\/.*?:{0}>)(?:.*)"
        m = re.search(pattern.format(tag), text)
        if not m:
            return ""
        else:
            return m.group(1)

    def copy_tag_value(self, msg_index, tag):
        """
        Copy to clipboard the tag value from message selected in grid

        :param msg_index: Index of message in message grid
        :param tag: Tag name
        :return: Tag value
        """

        if self.text_lst_shown and msg_index >= 0:
            xml_line = indent(self.text_lst_shown[msg_index])
            tag_value = MainFrame.get_tag_value(xml_line, tag)
            data_o = wx.TextDataObject()
            data_o.SetText(tag_value)
            if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
                wx.TheClipboard.SetData(data_o)
                wx.TheClipboard.Flush()
                wx.TheClipboard.Close()
            return tag_value

    def read_file_part(self, file_name, num_from, num_to):
        """
        Read part of file 'file_name' with lines from 'num_from' to 'num_to'

        :param file_name: Source filename
        :param num_from: Number of starting line
        :param num_to: Number of ending line
        """

        self.rt_Status.Clear()
        self.rt_Status.Update()

        source_name = self.cb_Sources.GetStringSelection()

        self.text_lst = self.conn.get_file_part(self.selected_nodegroup_index(), source_name, file_name, num_from,
                                                num_to)

        self.text_lst_shown = self.stc_OutLog.set_output_extended(self.text_lst,
                                                                  [self.selected_nodegroup().p_sort])
        self.lc_OutMsg.set_output(self.text_lst_shown)

    def search_by_str(self, search_str):
        """
        Fill search field in GUI with 'search_str' and search by data set in GUI

        :param search_str: Search string
        :return: none, fill self.text_lst
        """
        self.ch_SearchText_OnTextEnter(None)
        self.ch_SearchText.SetValue(search_str)  # Fill search str in widget
        self.ch_SearchText.Update()

        source_name = self.cb_Sources.GetStringSelection()
        search_date = self.selected_date()

        self.do_search(source_name, search_str, search_date)

    def do_search(self, source_name, search_str, search_date):
        """
        Search by data set in GUI:
        Search in 'source_name' by 'search_str' with date >= 'search_date'

        :param source_name: Search source name
        :param search_str: Search pattern
        :param search_date: Search date (search in files with creation data >= search_date)
        :return: none, fill self.text_lst
        """

        if not (search_str and search_str.strip()):
            return
        search_str = search_str.strip()
        self.rt_Status.Clear()
        self.rt_Status.Update()

        self.text_lst = self.conn.search(self.selected_nodegroup_index(), source_name, search_str, search_date)

        self.text_lst_shown = self.stc_OutLog.set_output(self.text_lst, [self.selected_nodegroup().p_sort])
        self.lc_OutMsg.set_output(self.text_lst_shown)

    def read_state(self, filename: str):
        """
        Restore application state settings

        :param conf_filename: settings config file name
        """
        try:
            tree = et.parse(filename)
            conf_root = tree.getroot()

            s_hostgroup = conf_root.find('nodegroup').text
            s_source = conf_root.find('source').text
            s_date = conf_root.find('date').text
            search_hist = [e.text for e in conf_root.findall('search-history/*')]

            self.ch_SearchText.AppendItems(search_hist)
            self.ch_SearchText.SetSelection(0)
            self.dt_SearchDate.SetValue(datetime.strptime(s_date, '%Y-%m-%d'))

            ng_index = self.cb_NodeGroups.FindString(s_hostgroup)
            if ng_index == wx.NOT_FOUND:
                ng_index = 0
            self.cb_NodeGroups.SetSelection(ng_index)
            self.fill_sources(0)
            self.lc_OutMsg.init_columns(
                self.selected_nodegroup().patterns.msg_columns)  # init columns on 'Messages' tab of AuiNotebook

            src_index = self.cb_Sources.FindString(s_source)
            if src_index == wx.NOT_FOUND:
                src_index = 0
            self.cb_Sources.SetSelection(src_index)

        except Exception as ex:
            pass

    def write_state(self, filename: str):
        """
        Save application state settings

        :param filename: settings config file name
        """
        try:
            conf_root = et.Element("settings")

            el = et.SubElement(conf_root, 'nodegroup')
            el.text = self.cb_NodeGroups.GetString(self.cb_NodeGroups.GetCurrentSelection())
            el = et.SubElement(conf_root, 'source')
            el.text = self.cb_Sources.GetString(self.cb_Sources.GetCurrentSelection())
            el = et.SubElement(conf_root, 'date')
            el.text = self.selected_date()

            count = self.ch_SearchText.GetCount()
            el = et.SubElement(conf_root, 'search-history')
            if count > MAX_SEARCH_HISTORY:
                count = MAX_SEARCH_HISTORY
            for i in range(count):
                et.SubElement(el, 'search-item').text = self.ch_SearchText.GetString(i)

            tree = et.ElementTree(conf_root)
            tree.write(filename, pretty_print=True, xml_declaration=True, encoding="utf-8")

        except Exception as ex:
            pass


def main():
    app = wx.App(False)
    frame = MainFrame(None)
    frame.CenterOnScreen()
    frame.Maximize(True)
    frame.Show(True)
    app.MainLoop()


if __name__ == "__main__":
    main()
