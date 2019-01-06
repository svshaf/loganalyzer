#!/usr/bin/env python3

# ----------------------------------------------------------------------------
# Name:         xmlstc.py
# Purpose:      wx.stc.StyledTextCtrl widget with XML syntax highlighting
#
# Author:       Sergey Shafranskiy <sergey.shafranskiy@gmail.com>
#
# Version:      1.1.3
# Build:        164
# Created:      2018-12-16
# ----------------------------------------------------------------------------

import wx
import wx.stc as stc

if wx.Platform == '__WXMSW__':
    faces = {'times': 'Times New Roman',
             'mono': 'Courier New',
             'helv': 'Arial',
             'other': 'Comic Sans MS',
             'size': 10,
             'size2': 8,
             }
elif wx.Platform == '__WXMAC__':
    faces = {'times': 'Times New Roman',
             'mono': 'Monaco',
             'helv': 'Arial',
             'other': 'Comic Sans MS',
             'size': 12,
             'size2': 10,
             }
else:
    faces = {'times': 'Times',
             'mono': 'Courier',
             'helv': 'Helvetica',
             'other': 'new century schoolbook',
             'size': 12,
             'size2': 10,
             }


class XmlSTC(stc.StyledTextCtrl):
    """
    StyledTextCtrl widget with XML syntax highlighting and support of 'Find' dialog
    """

    def __init__(self, parent, id=wx.ID_ANY,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0):
        """
        Class constructor
        """
        stc.StyledTextCtrl.__init__(self, parent, id, pos, size, style)

        self.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
        self.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        self.SetCaretForeground("BLUE")

        self.SetUseTabs(True)
        self.SetTabWidth(4)
        self.SetIndent(4)
        self.SetTabIndents(True)

        self.SetBackSpaceUnIndents(True)
        self.SetIndentationGuides(True)

        self.SetViewEOL(False)
        self.SetViewWhiteSpace(False)

        self.SetWrapMode(mode=1)  # mode: 0-None | 1-Word Wrap | 2-Character Wrap | 3-White Space Wrap

        # Setup margins #0, 1, 2:

        self.SetMargins(10, 10)  # width of left and right marings

        for i in [0, 2]:
            self.SetMarginWidth(i, 0)

        self.SetMarginType(0, stc.STC_MARGIN_NUMBER)  # 1st margin is used for line numbers
        self.SetMarginWidth(0, self.TextWidth(stc.STC_STYLE_LINENUMBER, "_999999"))
        self.SetMarginSensitive(0, False)

        """
        self.SetMarginType(1, stc.STC_MARGIN_SYMBOL)
        self.SetMarginWidth(1, 10)
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginWidth(2, 10)

        self.SetProperty("fold", "1")
        self.SetProperty("fold.html", "1")
        """

        # Global default styles
        # spec-string is composed of one or more of the following comma separated elements:
        # 'face':[facename] sets the font face name to use
        # 'size':[num] sets the font size in points
        # 'bold' turns on bold
        # 'italic' turns on italics
        # 'underline' turns on underlining
        # 'fore':[name or #``RRGGBB]`` sets the foreground colour
        # 'back':[name or #``RRGGBB]`` sets the background colour
        # 'eol' turns on eol filling

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(mono)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all styles to default

        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "back:#E0E0E0,face:%(mono)s,size:%(size2)d" % faces)

        self.SetLexer(stc.STC_LEX_XML)

        # Styles for XML lexer
        # below is definition of XML lexer's specific styles from Scintilla\lexers\LexHTML.cxx :
        """
        LexicalClass lexicalClassesXML[] = {
        // Lexer.Secondary XML SCLEX_XML SCE_H_:
            0, "SCE_H_DEFAULT", "default", "Default",
            1, "SCE_H_TAG", "tag", "Tags",
            2, "SCE_H_TAGUNKNOWN", "error tag", "Unknown Tags",
            3, "SCE_H_ATTRIBUTE", "attribute", "Attributes",
            4, "SCE_H_ERRORATTRIBUTEUNKNOWN", "error attribute", "Unknown Attributes",
            5, "SCE_H_NUMBER", "literal numeric", "Numbers",
            6, "SCE_H_DOUBLESTRING", "literal string", "Double quoted strings",
            7, "SCE_H_SINGLESTRING", "literal string", "Single quoted strings",
            8, "SCE_H_OTHER", "tag operator", "Other inside tag, including space and '='",
            9, "SCE_H_COMMENT", "comment", "Comment",
            10, "SCE_H_ENTITY", "literal", "Entities",
            11, "SCE_H_TAGEND", "tag", "XML style tag ends '/>'",
            12, "SCE_H_XMLSTART", "identifier", "XML identifier start '<?'",
            13, "SCE_H_XMLEND", "identifier", "XML identifier end '?>'",
            14, "", "unused", "",
            15, "", "unused", "",
            16, "", "unused", "",
            17, "SCE_H_CDATA", "literal", "CDATA",
            18, "SCE_H_QUESTION", "preprocessor", "Question",
            19, "SCE_H_VALUE", "literal string", "Unquoted Value",
            20, "", "unused", "",
            21, "SCE_H_SGML_DEFAULT", "default", "SGML tags <! ... >",
            22, "SCE_H_SGML_COMMAND", "preprocessor", "SGML command",
            23, "SCE_H_SGML_1ST_PARAM", "preprocessor", "SGML 1st param",
            24, "SCE_H_SGML_DOUBLESTRING", "literal string", "SGML double string",
            25, "SCE_H_SGML_SIMPLESTRING", "literal string", "SGML single string",
            26, "SCE_H_SGML_ERROR", "error", "SGML error",
            27, "SCE_H_SGML_SPECIAL", "literal", "SGML special (#XXXX type)",
            28, "SCE_H_SGML_ENTITY", "literal", "SGML entity",
            29, "SCE_H_SGML_COMMENT", "comment", "SGML comment",
            30, "", "unused", "",
            31, "SCE_H_SGML_BLOCK_DEFAULT", "default", "SGML block",
        };
        """
        self.StyleSetSpec(stc.STC_H_DEFAULT, "face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_H_TAG, "fore:#3A00FF,bold,size:%(size)d" % faces)

        self.StyleSetSpec(stc.STC_H_ATTRIBUTE, "fore:red,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_H_NUMBER, "fore:#FAB705,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_H_DOUBLESTRING, "fore:#52B203,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_H_SINGLESTRING, "fore:#52B203,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_H_OTHER, "fore:#939398,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_H_COMMENT, "fore:#A0A0A0,size:%(size)d" % faces)

        self.StyleSetSpec(stc.STC_H_CDATA, "fore:#03B2AD,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_H_VALUE, "fore:#B203AD,size:%(size)d" % faces)

        # Style for selecting of text in Find dialog
        self.STC_MATCH_VALUE = 14  # matched text
        self.StyleSetSpec(self.STC_MATCH_VALUE, "fore:#000000,back:#00D6D6")  # "fore:#F0F058,back:#2966D4")
        self.STC_MATCH_NEXT_VALUE = 15  # matched text, currently selected in find_next event
        self.StyleSetSpec(self.STC_MATCH_NEXT_VALUE, "fore:#FF0000,back:#3BDB1C")  # "fore:#F0F058,back:#2966D4")

        self.Bind(wx.EVT_FIND, self.on_find)
        self.Bind(wx.EVT_FIND_NEXT, self.on_find_next)
        self.Bind(wx.EVT_FIND_CLOSE, self.on_find_close)

        # Keyboard shortcuts event

        self.Bind(wx.EVT_CHAR, self.OnKeyDown)

        self.patterns = None  # regex patterns for custom colourising

    def custom_colourise(self, patterns):
        """
        Custom colourising of text in widget

        :param patterns: regex for applying custom colourising
        """
        pass

    def OnKeyDown(self, event=None):
        """
        Catch Ctrl-F for opening 'Find' dialog
        """
        keycode = event.GetKeyCode()
        if keycode == 6:  # Ctrl-F
            self.find()
        else:
            event.Skip()

    def find(self):
        """
        Show 'Find' dialog
        """

        # Setup for find dialog
        self.matches = []  # structure for storing original styles of selected text fragments (position, style)
        self.match_len = 0  # length of searching text

        self.data = wx.FindReplaceData()  # initializes and holds search parameters
        self.dlg = wx.FindReplaceDialog(self, self.data, 'Find', wx.FR_NOUPDOWN | wx.FR_NOMATCHCASE)
        self.dlg.Show()

    def on_find(self, event):
        """
        Colorize all matched text fragments
        """
        #self.SetLexer(stc.STC_LEX_NULL)
        try:
            self.colorize_text(event.GetFindString(), self.STC_MATCH_VALUE)  # fill structure self.matches[]

            self.match_index = 0  # index of the currently selected fragment within self.matches[]
            self.change_match_style(0, self.STC_MATCH_NEXT_VALUE) # assign "current selection" style to first selected fragment
            self.apply_end_style()
        finally:
            #self.SetLexer(stc.STC_LEX_XML)
            pass

    def on_find_next(self, event):
        """
        Position to the next matched text fragment
        """
        self.change_match_style(self.match_index, self.STC_MATCH_VALUE)  # restore "unselected" style of curr. sel. fragment
        self.match_index += 1
        if self.match_index >=  len(self.matches):
            self.match_index = 0
        self.change_match_style(self.match_index, self.STC_MATCH_NEXT_VALUE)  # assign "selected" style to next sel. fragment
        self.apply_end_style()
        self.GotoPos(self.matches[self.match_index][0])

    def on_find_close(self, event):
        """
        Close 'Find' dialog
        """

        #self.revert_styles()  # restore  original styles of all matched text fragments

        self.Colourise(0, -1)
        self.matches = []

        self.custom_colourise(self.patterns)
      
    def apply_style(self, pos, length, mask, style):
        """
        Apply style
        :param pos: Start position in bytes
        :param length: Length of the text
        :param mask: Style mask
        :param style: Style number
        """
        self.StartStyling(pos=pos, mask=mask)
        self.SetStyling(length=length, style=style)

    def revert_styles(self):
        """
        Restore original styles of all matched text fragments
        """
        for match in self.matches:
            self.apply_style(match[0], self.match_len, 0xFF, match[1])
        self.matches = []

    def change_match_style(self, n, style):
        """
        Apply style 'style' to 'n'-th matched text fragment

        :param n: index in matches[]
        :param style: style to assign
        """
        if self.matches:
            match = self.matches[n]
            self.apply_style(match[0], self.match_len, 0xFF, style)

    @staticmethod
    def calcByteLen(text):
        """
        Get string length in bytes, not in chars
        """
        return len(text.encode('utf-8'))

    @staticmethod
    def calcBytePos(text, pos):
        """
        Convert position in chars into position in bytes
        """
        return len(text[: pos].encode('utf-8'))

    def colorize_text(self, styled_text, style):
        """
        Apply style 'style' to all occurrences of 'styled_text'
        """
        is_match_word = self.data.GetFlags() & wx.FR_WHOLEWORD
        styled_len = len(styled_text)
        styled_byte_len = XmlSTC.calcByteLen(styled_text)  # get length of the matched string in bytes
        self.match_len = styled_byte_len

        text = self.GetText()
        self.end_byte_pos = XmlSTC.calcBytePos(text, len(text)-1)

        # Search for all matches of 'styled_text'
        pos = text.find(styled_text)
        while pos != -1:
            next_sym = text[pos + styled_len: pos + styled_len + 1]
            prev_sym = text[pos - 1: pos]

            if not is_match_word or (
                    (pos == 0 or prev_sym.isspace()) and (pos == len(text) - styled_len or next_sym.isspace())):
                byte_pos = XmlSTC.calcBytePos(text, pos)  # convert position in chars to position in bytes

                # Save old style
                self.matches.append((byte_pos, self.GetStyleAt(byte_pos)))  # (pos in bytes, style number)
                # Apply new style
                self.apply_style(byte_pos, self.match_len, 0xFF, style)
            pos = text.find(styled_text, pos + styled_len)

    def apply_end_style(self):
        self.apply_style(self.end_byte_pos, 1, 0xFF, self.GetStyleAt(self.end_byte_pos))