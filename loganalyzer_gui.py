# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Aug  8 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.adv
import wx.aui
import wx.richtext

###########################################################################
## Class LogAnalyzerFrame
###########################################################################

class LogAnalyzerFrame ( wx.Frame ):
	
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Log Analyzer", pos = wx.DefaultPosition, size = wx.Size( 1321,760 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		bsz_Main = wx.BoxSizer( wx.VERTICAL )
		
		bsz_Controls = wx.BoxSizer( wx.HORIZONTAL )
		
		self.lb_Nodegroup = wx.StaticText( self, wx.ID_ANY, u"NodeGroup:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lb_Nodegroup.Wrap( -1 )
		
		bsz_Controls.Add( self.lb_Nodegroup, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		cb_NodeGroupsChoices = [ u"[nodegroups]" ]
		self.cb_NodeGroups = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, cb_NodeGroupsChoices, 0 )
		self.cb_NodeGroups.SetSelection( 0 )
		bsz_Controls.Add( self.cb_NodeGroups, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.lb_SearchFor = wx.StaticText( self, wx.ID_ANY, u"Search for", wx.Point( -1,-1 ), wx.DefaultSize, 0 )
		self.lb_SearchFor.Wrap( -1 )
		
		bsz_Controls.Add( self.lb_SearchFor, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		ch_SearchTextChoices = []
		self.ch_SearchText = wx.ComboBox( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 400,-1 ), ch_SearchTextChoices, 0 )
		bsz_Controls.Add( self.ch_SearchText, 0, wx.ALL, 5 )
		
		self.lb_InLogFile = wx.StaticText( self, wx.ID_ANY, u"in", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lb_InLogFile.Wrap( -1 )
		
		bsz_Controls.Add( self.lb_InLogFile, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		cb_SourcesChoices = [ u"[source]" ]
		self.cb_Sources = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 120,-1 ), cb_SourcesChoices, 0 )
		self.cb_Sources.SetSelection( 0 )
		bsz_Controls.Add( self.cb_Sources, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.lb_Date = wx.StaticText( self, wx.ID_ANY, u"with date >=", wx.Point( -1,-1 ), wx.DefaultSize, 0 )
		self.lb_Date.Wrap( -1 )
		
		bsz_Controls.Add( self.lb_Date, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.dt_SearchDate = wx.adv.DatePickerCtrl( self, wx.ID_ANY, wx.DefaultDateTime, wx.DefaultPosition, wx.DefaultSize, wx.adv.DP_DEFAULT|wx.adv.DP_DROPDOWN )
		bsz_Controls.Add( self.dt_SearchDate, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.bt_Search = wx.Button( self, wx.ID_ANY, u"Search", wx.DefaultPosition, wx.DefaultSize, 0 )
		bsz_Controls.Add( self.bt_Search, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )
		
		
		bsz_Main.Add( bsz_Controls, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.sp_Out = wx.SplitterWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D )
		self.sp_Out.Bind( wx.EVT_IDLE, self.sp_OutOnIdle )
		
		self.pn_Out = wx.Panel( self.sp_Out, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bsz_Out = wx.BoxSizer( wx.HORIZONTAL )
		
		self.nb_OutLog = wx.aui.AuiNotebook( self.pn_Out, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.aui.AUI_NB_DEFAULT_STYLE )
		self.pn_OutLog = wx.Panel( self.nb_OutLog, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.nb_OutLog.AddPage( self.pn_OutLog, u"Log", False, wx.NullBitmap )
		self.pn_OutMsg = wx.Panel( self.nb_OutLog, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.nb_OutLog.AddPage( self.pn_OutMsg, u"Messages", True, wx.NullBitmap )
		
		bsz_Out.Add( self.nb_OutLog, 6, wx.EXPAND |wx.ALL, 0 )
		
		
		self.pn_Out.SetSizer( bsz_Out )
		self.pn_Out.Layout()
		bsz_Out.Fit( self.pn_Out )
		self.pn_Status = wx.Panel( self.sp_Out, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,100 ), wx.TAB_TRAVERSAL )
		bsz_Status = wx.BoxSizer( wx.HORIZONTAL )
		
		self.rt_Status = wx.richtext.RichTextCtrl( self.pn_Status, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TE_READONLY|wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER|wx.WANTS_CHARS )
		self.rt_Status.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		
		bsz_Status.Add( self.rt_Status, 1, wx.EXPAND |wx.ALL, 0 )
		
		
		self.pn_Status.SetSizer( bsz_Status )
		self.pn_Status.Layout()
		self.sp_Out.SplitHorizontally( self.pn_Out, self.pn_Status, -100 )
		bsz_Main.Add( self.sp_Out, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bsz_Main )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.MainFrame_OnClose )
		self.cb_NodeGroups.Bind( wx.EVT_CHOICE, self.cb_NodeGroups_OnChoice )
		self.ch_SearchText.Bind( wx.EVT_COMBOBOX, self.ch_SearchText_OnComboBox )
		self.ch_SearchText.Bind( wx.EVT_RIGHT_UP, self.ch_SearchText_OnRightUp )
		self.ch_SearchText.Bind( wx.EVT_TEXT_ENTER, self.ch_SearchText_OnTextEnter )
		self.bt_Search.Bind( wx.EVT_BUTTON, self.bt_Search_OnBtnClick )
		self.nb_OutLog.Bind( wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.nb_OutLog_OnPageChanged )
		self.nb_OutLog.Bind( wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSED, self.nb_OutLog_OnPageClosed )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def MainFrame_OnClose( self, event ):
		event.Skip()
	
	def cb_NodeGroups_OnChoice( self, event ):
		event.Skip()
	
	def ch_SearchText_OnComboBox( self, event ):
		event.Skip()
	
	def ch_SearchText_OnRightUp( self, event ):
		event.Skip()
	
	def ch_SearchText_OnTextEnter( self, event ):
		event.Skip()
	
	def bt_Search_OnBtnClick( self, event ):
		event.Skip()
	
	def nb_OutLog_OnPageChanged( self, event ):
		event.Skip()
	
	def nb_OutLog_OnPageClosed( self, event ):
		event.Skip()
	
	def sp_OutOnIdle( self, event ):
		self.sp_Out.SetSashPosition( -100 )
		self.sp_Out.Unbind( wx.EVT_IDLE )
	

