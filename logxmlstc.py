#!/usr/bin/env python3

#  ----------------------------------------------------------------------------
# Name:         logxmlstc.py
# Purpose:
#
# Author:       Sergey Shafranskiy <sergey.shafranskiy@gmail.com>
#
# Version:      1.1.4
# Build:        169
# Created:      2019-01-13
# ----------------------------------------------------------------------------

import wx
import xmlstc

import wx.stc as stc
from yattag import indent
import re

# 	Messages

INVALID_HEADER = r'''Incorrect file line header: {}' '''

# Context menu strings

MNU_FIND = u"Find"
MNU_SEARCH_BY_SELECTED = u"Search by Selected"
MNU_GET_NEXT_PART_BY_LINE_NUMBER = u"Get This and Next 100 Messages"
MNU_GET_CONTAINING_PART_BY_LINE_NUMBER = u"Get This, Previous 100 and Next 100 Messages"
MNU_SAVE_TO_FILE = u"Save to File"

# Context menu ids

ID_FIND = wx.NewIdRef()
ID_SEARCH_BY_SELECTED = wx.NewIdRef()
ID_GET_NEXT_PART_BY_LINE_NUMBER = wx.NewIdRef()
ID_GET_CONTAINIG_PART_BY_LINE_NUMBER = wx.NewIdRef()
ID_SAVE_TO_FILE = wx.NewIdRef()


class LogXmlSTC(xmlstc.XmlSTC):
    """
    StyledTextCtrl control with XML syntax highlighting
    """
    global ID_SEARCH_BY_SELECTED
    global ID_GET_NEXT_PART_BY_LINE_NUMBER
    global ID_GET_CONTAINIG_PART_BY_LINE_NUMBER
    global ID_SAVE_TO_FILE

    def __init__(self, parent, parent_panel):
        """
        Class constructor

        :param parent: Parent class
        :param parent_panel: Parent panel of control
        """

        self.parent = parent
        self.menu = None

        self.p_sort = None

        super(LogXmlSTC, self).__init__(parent_panel)

        # pn_OutLog is parent of newly created stc_OutLog: StyledTextCtrl
        bsz_OutLog = wx.BoxSizer(wx.HORIZONTAL)
        bsz_OutLog.Add(self, 1, wx.EXPAND | wx.ALL, 5)
        parent_panel.SetSizer(bsz_OutLog)
        parent_panel.Layout()
        bsz_OutLog.Fit(parent_panel)

        # Create context popup menu
        self.menu = wx.Menu()

        # Standard context self.menu items
        self.menu.Append(wx.ID_UNDO)
        self.menu.Append(wx.ID_REDO)
        self.menu.Append(wx.ID_SEPARATOR)

        self.menu.Append(wx.ID_CUT)
        self.menu.Append(wx.ID_COPY)
        self.menu.Append(wx.ID_PASTE)
        self.menu.Append(wx.ID_DELETE)
        self.menu.Append(wx.ID_SELECTALL)
        self.menu.Append(wx.ID_SEPARATOR)

        # Custom menu items
        self.menu.Append(wx.MenuItem(self.menu, ID_FIND,
                                     MNU_FIND, wx.EmptyString, wx.ITEM_NORMAL))
        self.menu.Append(wx.ID_SEPARATOR)

        self.menu.Append(wx.MenuItem(self.menu, ID_GET_NEXT_PART_BY_LINE_NUMBER,
                                     MNU_GET_NEXT_PART_BY_LINE_NUMBER, wx.EmptyString, wx.ITEM_NORMAL))
        self.menu.Append(wx.MenuItem(self.menu, ID_GET_CONTAINIG_PART_BY_LINE_NUMBER,
                                     MNU_GET_CONTAINING_PART_BY_LINE_NUMBER, wx.EmptyString, wx.ITEM_NORMAL))
        self.menu.Append(wx.ID_SEPARATOR)

        self.menu.Append(wx.MenuItem(self.menu, ID_SEARCH_BY_SELECTED,
                                     MNU_SEARCH_BY_SELECTED, wx.EmptyString, wx.ITEM_NORMAL))
        self.menu.Append(wx.ID_SEPARATOR)

        self.menu.Append(wx.MenuItem(self.menu, ID_SAVE_TO_FILE,
                                     MNU_SAVE_TO_FILE, wx.EmptyString, wx.ITEM_NORMAL))

        self.Bind(wx.EVT_MENU, self.OnMenu, id=wx.ID_UNDO)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=wx.ID_REDO)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=wx.ID_CUT)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=wx.ID_DELETE)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=wx.ID_SELECTALL)

        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_FIND)

        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_GET_NEXT_PART_BY_LINE_NUMBER)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_GET_CONTAINIG_PART_BY_LINE_NUMBER)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_SEARCH_BY_SELECTED)

        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_SAVE_TO_FILE)

        self.Bind(wx.EVT_CONTEXT_MENU, self.OnRClick)

    def set_output(self, text_lst, patterns = []):
        """
        Set text in widget

        :param text_lst: Input text
        """
        self.ClearSelections()
        self.ClearAll()

        res_lst = []
        for line in text_lst:
            try:
                xml_line = indent(line)
            except Exception as ex:
                xml_line = line
            res_lst.append(xml_line + "\n\n")

        self.AppendText(''.join(res_lst))

        # adjust line number margin width
        width = self.TextWidth(stc.STC_STYLE_LINENUMBER, str(self.GetLineCount()) + ' ')
        self.SetMarginWidth(0, width)

        self.custom_colourise(patterns)
        self.Update()

        return res_lst

    def set_output_extended(self, text_lst, patterns = []):
        """
        Set text in widget

        :param text_lst: Log content
        """
        self.ClearAll()
        self.ClearSelections()

        pattern_xml = r"<\/?.*?:?.+?>"
        p_xml = re.compile(pattern_xml)

        pattern_dt = r"(^[^:]*:[0-9]*:\s*)(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})"
        p_dt = re.compile(pattern_dt)

        res_lst = []
        xml_lst = []

        for line in text_lst:
            if p_dt.match(line):
                xml_line = "\n\n"
                if xml_lst:
                    xml_str = "".join(xml_lst)
                    xml_line = indent(xml_str) + xml_line

                res_lst.append(xml_line)
                xml_lst = []

            if p_xml.match(line):
                line_str = line.strip(' \t\n\r')
            else:
                line_str = line
            xml_lst.append(line_str)

        if xml_lst:
            xml_str = "".join(xml_lst)
            xml_line = indent(xml_str)
            res_lst.append(xml_line)

        self.AppendText(''.join(res_lst).strip())

        # adjust line number margin width
        width = self.TextWidth(stc.STC_STYLE_LINENUMBER, str(self.GetLineCount()) + ' ')
        self.SetMarginWidth(0, width)

        self.custom_colourise(patterns)
        self.Update()

        return res_lst

    def custom_colourise(self, patterns):
        """
        Custom colourising of text in widget

        :param patterns: regex for applying custom colourising
        """
        """
        if self.p_sort is not None:
            text: str = self.GetText()
            self.end_byte_pos = xmlstc.XmlSTC.calcBytePos(text, len(text) - 1)
            for m in re.finditer(self.p_sort, text):
                pos = m.start(1)
                byte_pos = xmlstc.XmlSTC.calcBytePos(text, pos)  # convert position in chars to position in bytes
                len = m.end(1) - m.start(1) + 1
                self.apply_style(byte_pos, len, 0xFF, self.STC_COLOURISE_1)
                self.apply_end_style()
        """
        return

    def OnRClick(self, event):
        """
        Invoke context menu
        """
        self.PopupMenu(self.menu)

    def OnMenu(self, event):
        """
        Menu item selected
        """
        if event.Id == wx.ID_UNDO:
            self.Undo()
        elif event.Id == wx.ID_REDO:
            self.Redo()
        elif event.Id == wx.ID_CUT:
            self.Cut()
        elif event.Id == wx.ID_COPY:
            self.Copy()
        elif event.Id == wx.ID_PASTE:
            self.Paste()
        elif event.Id == wx.ID_DELETE:
            self.parent.Delete()
        elif event.Id == wx.ID_SELECTALL:
            self.SelectAll()
        elif event.Id == ID_FIND:
            self.find()
        elif event.Id == ID_SEARCH_BY_SELECTED:
            self.search_by_selected()
        elif event.Id == ID_GET_NEXT_PART_BY_LINE_NUMBER:
            self.get_part_by_line_number(0, 100)
        elif event.Id == ID_GET_CONTAINIG_PART_BY_LINE_NUMBER:
            self.get_part_by_line_number(100, 100)
        elif event.Id == ID_SAVE_TO_FILE:
            self.save_to_file()
        else:
            event.Skip()

    def search_by_selected(self):
        """
        Search using text selection
        """
        select_str = self.GetSelectedText()
        self.parent.search_by_str(select_str)

    def get_part_by_line_number(self, num_before=0, num_after=50):
        """
        Get part of the source file with selected line

        :param num_before: Number of file lines before current
        :param num_after: Number of file lines after current
        """

        # Get filename and line number from header of current line

        curr_pos = self.GetCurrentPos()
        line_number = self.LineFromPosition(curr_pos)
        line = self.GetLine(line_number)
        if not (line and line.strip()):
            return
        lst = line.split(':')
        if len(lst) >= 2:
            try:
                file_name = lst[0].strip()
                line_number = int(lst[1].strip())

                self.parent.read_file_part(file_name, line_number - num_before, line_number + num_after)
            except Exception as ex:
                self.parent.write_trace(INVALID_HEADER.format(", ".join([str(arg) for arg in ex.args])), True)

    def save_to_file(self):
        """
        Save text from widget to file
        """
        text = self.GetText()

        with wx.FileDialog(self, message="Save Log as...",
                           defaultDir="", defaultFile="",
                           wildcard="XML files (*.xml)|*.xml|LOG files (*.log)|*.log|All files (*.*)|*.*",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            res = fileDialog.ShowModal()
            filename = fileDialog.GetPath()
            # fileDialog.Destroy()

        if res == wx.ID_OK:  # Save button was pressed
            with open(filename, 'w', encoding='utf8') as file:
                file.write(text)
            return True
        elif res == wx.ID_CANCEL:  # Either the cancel button was pressed or the window was closed
            return False

    def OnKeyDown(self, event=None):
        """
        Catch keyboard shortcut for saving to file
        """
        keycode = event.GetKeyCode()
        if keycode == 19:  # Ctrl-S
            self.save_to_file()
        else:
            super().OnKeyDown(event)
