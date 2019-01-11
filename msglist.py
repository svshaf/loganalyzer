#!/usr/bin/env python3

# ----------------------------------------------------------------------------
# Name:         msglist.py
# Purpose:      Customized ListCtrl widget for message displaying
#
# Author:       Sergey Shafranskiy <sergey.shafranskiy@gmail.com>
#
# Version:      1.1.4
# Build:        167
# Created:      2019-01-11
# ----------------------------------------------------------------------------

import wx
import re
import wx.lib.mixins.listctrl as listmix

# Context menu strings

MNU_COPY_CORRELATION_ID = u"Copy correlationId"
MNU_SHOW_ALL_WITH_SAME_CORRELATION_ID = u"Show all messages with same correlationId"

# Context menu ids

ID_COPY_CORRELATION_ID = wx.NewIdRef()
ID_SHOW_ALL_WITH_SAME_CORRELATION_ID = wx.NewIdRef()


class MsgListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """
    Log's messages list grid control
    """

    def __init__(self, parent, parent_panel, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.LC_REPORT | wx.LC_SINGLE_SEL):

        super(MsgListCtrl, self).__init__(parent_panel, id, pos, size, style)
        self.parent = parent
        self.parent_panel = parent_panel

        listmix.ListCtrlAutoWidthMixin.__init__(self)

        self.text_lst = []
        self.msg_columns = []
        self.main_mgs_column = 1

        # Create popup menu of message list

        self.menu = wx.Menu()
        self.menu.Append(wx.MenuItem(self.menu, ID_COPY_CORRELATION_ID,
                                     MNU_COPY_CORRELATION_ID, wx.EmptyString, wx.ITEM_NORMAL))
        self.menu.Append(wx.MenuItem(self.menu, ID_SHOW_ALL_WITH_SAME_CORRELATION_ID,
                                     MNU_SHOW_ALL_WITH_SAME_CORRELATION_ID, wx.EmptyString, wx.ITEM_NORMAL))
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRClick)

        self.Bind(wx.EVT_MENU, self.OnMenuMsgList, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.OnMenuMsgList, id=wx.ID_SELECTALL)
        self.Bind(wx.EVT_MENU, self.OnMenuMsgList, id=ID_COPY_CORRELATION_ID)
        self.Bind(wx.EVT_MENU, self.OnMenuMsgList, id=ID_SHOW_ALL_WITH_SAME_CORRELATION_ID)

    def init_columns(self, msg_columns: list):
        self.msg_columns = msg_columns

        self.DeleteAllItems()

        self.text_lst = []
        self.DeleteAllColumns()

        # setup grid list columns
        self.AppendColumn('Line', format=wx.LIST_FORMAT_LEFT, width=60)
        self.main_mgs_column = 1
        for i, col in enumerate(msg_columns):  # enumerate ColumnPatterns
            self.AppendColumn(col.name, format=wx.LIST_FORMAT_LEFT, width=wx.LIST_AUTOSIZE)
            if col.is_main:
                self.main_mgs_column = i

        # event: Message selecting in grid
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnListItemActivated)

        bsz_OutMsg = wx.BoxSizer(wx.HORIZONTAL)
        # method: Add (self, window, proportion=0, flag=0, border=0)
        bsz_OutMsg.Add(self, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.parent_panel.SetSizer(bsz_OutMsg)
        self.parent_panel.Layout()
        bsz_OutMsg.Fit(self.parent_panel)

        self.Update()

    def OnRClick(self, event):
        self.PopupMenu(self.menu)

    def OnMenuMsgList(self, event):
        if event.Id == wx.ID_COPY:
            self.Copy()
        elif event.Id == wx.ID_SELECTALL:
            self.SelectAll()
        elif event.Id == ID_COPY_CORRELATION_ID:
            self.copy_correlaion_id()
        elif event.Id == ID_SHOW_ALL_WITH_SAME_CORRELATION_ID:
            self.get_msgs_by_correlation_id()
        else:
            event.Skip()

    def tab_caption(self, msg_index, format_str, *col_index):
        """
        Get tab caption
        :param msg_index: index of message line 
        :param format_str: format string
        :param col_index: indexes of columns that are substituted in format string
        :return: string, tab caption
        """
        return format_str.format(*[self.GetItemText(msg_index, c) for c in col_index])

    def get_msg_number(self, msg_index):
        return int(self.GetItemText(msg_index, 0))

    def OnListItemActivated(self, event):
        """
        Selecting of the message in listbox
        """
        msg_index = self.GetFirstSelected()
        # tab caption: "datetime (1): message (3)"
        title = self.tab_caption(msg_index, '{0}: {1}', 1, 3)
        self.parent.create_msg_tab(self.get_msg_number(msg_index), title)

    def set_output(self, text_lst):
        """
        Create list of messages

        :param text_lst: Text to add to control
        """

        self.text_lst = text_lst

        self.DeleteAllItems()

        pattern = []
        p = []

        for i, col in enumerate(self.msg_columns):  # enumerate ColumnPatterns
            pattern.append(col.expr)  # re pattern
            p.append(re.compile(pattern[i]))

        for i, line in enumerate(text_lst):
            m = []
            col_val = [str(i)]
            for j, pv in enumerate(p):
                m.append(pv.match(line))
                col_val.append(m[j].group(1) if (m[j] is not None) else " ")

            if m[self.main_mgs_column] is not None:  # is 'message' column?
                self.Append(col_val)

            for j in range(len(self.msg_columns) - 1):  # last column expand to control width
                self.SetColumnWidth(j + 1, wx.LIST_AUTOSIZE)

        self.Update()
        if self.GetItemCount() > 0:
            self.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def get_msgs_by_correlation_id(self):
        self.parent.create_multi_msg_tag(self.get_msg_number(self.GetFirstSelected()), 'correlationId')

    def copy_correlaion_id(self):
        self.parent.copy_tag_value(self.get_msg_number(self.GetFirstSelected()), 'correlationId')

    def GetSelectedItems(self):
        """
        Gets the selected items for the list control.
        Selection is returned as a list of selected indices, low to high.
        """
        selection = []
        index = self.GetFirstSelected()
        selection.append(index)
        while len(selection) != self.GetSelectedItemCount():
            index = self.GetNextSelected(index)
            selection.append(index)
        return selection

    def Copy(self):
        """ Copy selected data to clipboard """
        text = self.GetSelectedText()
        data_o = wx.TextDataObject()
        data_o.SetText(text)
        if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data_o)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()

    def GetSelectedText(self):
        """ Get selected text """
        items = list()
        for item in range(self.GetItemCount()):
            if self.IsSelected(item):
                items.append(self.GetRowText(item))
        text = "\n".join(items)
        return text

    def GetRowText(self, idx):
        """ Get row text """
        txt = list()
        for col in range(self.GetColumnCount()):
            txt.append(self.GetItemText(idx, col))
        return "\t".join(txt)

    def SelectAll(self):
        """ Select all text """
        for item in range(self.GetItemCount()):
            self.Select(item, 1)
