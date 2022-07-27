import os
import platform
import sys
from functools import partial

import wx
from PIL import Image
from wx import aui

from meerk40t.core.exceptions import BadFileError
from meerk40t.kernel import lookup_listener, signal_listener

from ..core.element_types import elem_nodes, op_nodes

from ..core.units import UNITS_PER_INCH, Length
from ..svgelements import Color, Matrix, Path
from .icons import (
    STD_ICON_SIZE,
    icon_cag_common_50,
    icon_cag_subtract_50,
    icon_cag_union_50,
    icon_cag_xor_50,
    icon_meerk40t,
    icons8_align_bottom_50,
    icons8_align_left_50,
    icons8_align_right_50,
    icons8_align_top_50,
    icons8_circle_50,
    icons8_cursor_50,
    icons8_flip_vertical,
    icons8_measure_50,
    icons8_mirror_horizontal,
    icons8_opened_folder_50,
    icons8_oval_50,
    icons8_pencil_drawing_50,
    icons8_place_marker_50,
    icons8_point_50,
    icons8_polygon_50,
    icons8_polyline_50,
    icons8_rectangular_50,
    icons8_rotate_left_50,
    icons8_rotate_right_50,
    icons8_save_50,
    icons8_type_50,
    icons8_vector_50,
    icons_centerize,
    icons_evenspace_horiz,
    icons_evenspace_vert,
    icons8_group_objects_50,
    icons8_ungroup_objects_50,
    icons8_next_page_20,
    cap_butt_20,
    cap_round_20,
    cap_square_20,
    fill_evenodd,
    fill_nonzero,
    join_bevel,
    join_miter,
    join_round,
    icons8_direction_20,
    icons8_scatter_plot_20,
    icons8_laser_beam_20,
    icons8_image_20,
    icons8_small_beam_20,
    icons8_diagonal_20,
    set_icon_appearance,
)
from .laserrender import (
    DRAW_MODE_ALPHABLACK,
    DRAW_MODE_ANIMATE,
    DRAW_MODE_BACKGROUND,
    DRAW_MODE_CACHE,
    DRAW_MODE_FILLS,
    DRAW_MODE_FLIPXY,
    DRAW_MODE_GRID,
    DRAW_MODE_GUIDES,
    DRAW_MODE_ICONS,
    DRAW_MODE_IMAGE,
    DRAW_MODE_INVERT,
    DRAW_MODE_LASERPATH,
    DRAW_MODE_LINEWIDTH,
    DRAW_MODE_PATH,
    DRAW_MODE_REFRESH,
    DRAW_MODE_RETICLE,
    DRAW_MODE_SELECTION,
    DRAW_MODE_STROKES,
    DRAW_MODE_TEXT,
    DRAW_MODE_VARIABLES,
    swizzlecolor,
)
from .mwindow import MWindow

_ = wx.GetTranslation

ID_MENU_IMPORT = wx.NewId()
ID_MENU_RECENT = wx.NewId()
ID_MENU_ZOOM_OUT = wx.NewId()
ID_MENU_ZOOM_IN = wx.NewId()
ID_MENU_ZOOM_SIZE = wx.NewId()
ID_MENU_ZOOM_BED = wx.NewId()
ID_MENU_SCENE_MINMAX = wx.NewId()

# 1 fill, 2 grids, 4 guides, 8 laserpath, 16 writer_position, 32 selection
ID_MENU_HIDE_FILLS = wx.NewId()
ID_MENU_HIDE_GUIDES = wx.NewId()
ID_MENU_HIDE_GRID = wx.NewId()
ID_MENU_HIDE_BACKGROUND = wx.NewId()
ID_MENU_HIDE_LINEWIDTH = wx.NewId()
ID_MENU_HIDE_STROKES = wx.NewId()
ID_MENU_HIDE_ICONS = wx.NewId()
ID_MENU_HIDE_LASERPATH = wx.NewId()
ID_MENU_HIDE_RETICLE = wx.NewId()
ID_MENU_HIDE_SELECTION = wx.NewId()
ID_MENU_SCREEN_REFRESH = wx.NewId()
ID_MENU_SCREEN_ANIMATE = wx.NewId()
ID_MENU_SCREEN_INVERT = wx.NewId()
ID_MENU_SCREEN_FLIPXY = wx.NewId()
ID_MENU_PREVENT_CACHING = wx.NewId()
ID_MENU_PREVENT_ALPHABLACK = wx.NewId()
ID_MENU_HIDE_IMAGE = wx.NewId()
ID_MENU_HIDE_PATH = wx.NewId()
ID_MENU_HIDE_TEXT = wx.NewId()
ID_MENU_SHOW_VARIABLES = wx.NewId()

ID_MENU_FILE0 = wx.NewId()
ID_MENU_FILE1 = wx.NewId()
ID_MENU_FILE2 = wx.NewId()
ID_MENU_FILE3 = wx.NewId()
ID_MENU_FILE4 = wx.NewId()
ID_MENU_FILE5 = wx.NewId()
ID_MENU_FILE6 = wx.NewId()
ID_MENU_FILE7 = wx.NewId()
ID_MENU_FILE8 = wx.NewId()
ID_MENU_FILE9 = wx.NewId()
ID_MENU_FILE10 = wx.NewId()
ID_MENU_FILE11 = wx.NewId()
ID_MENU_FILE12 = wx.NewId()
ID_MENU_FILE13 = wx.NewId()
ID_MENU_FILE14 = wx.NewId()
ID_MENU_FILE15 = wx.NewId()
ID_MENU_FILE16 = wx.NewId()
ID_MENU_FILE17 = wx.NewId()
ID_MENU_FILE18 = wx.NewId()
ID_MENU_FILE19 = wx.NewId()
ID_MENU_FILE_CLEAR = wx.NewId()

ID_MENU_KEYMAP = wx.NewId()
ID_MENU_DEVICE_MANAGER = wx.NewId()
ID_MENU_CONFIG = wx.NewId()
ID_MENU_NAVIGATION = wx.NewId()
ID_MENU_NOTES = wx.NewId()
ID_MENU_OPERATIONS = wx.NewId()
ID_MENU_CONTROLLER = wx.NewId()
ID_MENU_CAMERA = wx.NewId()
ID_MENU_CONSOLE = wx.NewId()
ID_MENU_USB = wx.NewId()
ID_MENU_SPOOLER = wx.NewId()
ID_MENU_SIMULATE = wx.NewId()
ID_MENU_RASTER_WIZARD = wx.NewId()
ID_MENU_WINDOW_RESET = wx.NewId()
ID_MENU_PANE_RESET = wx.NewId()
ID_MENU_PANE_LOCK = wx.NewId()
ID_MENU_JOB = wx.NewId()
ID_MENU_TREE = wx.NewId()

ID_BEGINNERS = wx.NewId()
ID_HOMEPAGE = wx.NewId()
ID_RELEASES = wx.NewId()
ID_FACEBOOK = wx.NewId()
ID_DISCORD = wx.NewId()
ID_MAKERS_FORUM = wx.NewId()
ID_IRC = wx.NewId()


class CustomStatusBar(wx.StatusBar):
    """Overloading of Statusbar to allow some elements on it"""

    def __init__(self, parent, panelct):
        # Where shall the different controls be placed?
        self.startup = True
        self.panelct = panelct
        self.context = parent.context
        wx.StatusBar.__init__(self, parent, -1)
        # Make sure that the statusbar elements are visible fully
        self.SetMinHeight(25)
        self.SetFieldsCount(self.panelct)
        self.SetStatusStyles([wx.SB_SUNKEN] * self.panelct)
        self.status_text = [""] * self.panelct
        self.previous_text = [""] * self.panelct
        self.sizeChanged = False
        self.box_id_visible = {}
        self.activesizer = [None] * self.panelct
        self.nextbuttons = []
        for idx in range(self.panelct):
            btn = wx.Button(self, id=wx.ID_ANY, label="", size=wx.Size(20,-1))
            btn.SetBitmap(icons8_next_page_20.GetBitmap(noadjustment=True))
            btn.Show(False)
            btn.Bind(wx.EVT_BUTTON, self.on_button_next)
            btn.Bind(wx.EVT_RIGHT_DOWN, self.on_button_prev)
            self.nextbuttons.append(btn)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        # set the initial position of the checkboxes
        self.Reposition()
        self.startup = False

    def SetStatusText(self, message="", panel=0):
        if panel >= 0 and panel < self.panelct:
            self.status_text[panel] = message
        if self.activesizer[panel] is not None and len(message) > 0:
            # Someone wanted to have a message while displaying some control elements
            return
        super().SetStatusText(message, panel)

    def AddPanel(self, panel_idx, wx_boxsizer, identifier, visible=True, callback = None):
        if panel_idx<0 or panel_idx>= self.panelct:
            return
        # Mke sure they belong to me, else the wx.Boxsizer
        # will have wrong information to work with
        for sizeritem in wx_boxsizer.GetChildren():
            wind = sizeritem.GetWindow()
            if wind is not None:
                wind.Reparent(self)

        storage = [wx_boxsizer, panel_idx, visible, callback] # Visible by default
        self.box_id_visible[identifier] = storage

    def ActivatePanel(self, identifier, newflag):
        # Activate Panel will make the indicated panel become choosable
        try:
            oldflag = self.box_id_visible[identifier][2]
        except (IndexError, KeyError):
            return
        if oldflag != newflag:
            panelidx = self.box_id_visible[identifier][1]

            # Choosable
            self.box_id_visible[identifier][2] = newflag
            if newflag and self.activesizer[panelidx] is None:
                self.activesizer[panelidx] = identifier
            elif not newflag and self.activesizer[panelidx] == identifier:
                # Was the active one
                self.activesizer[panelidx] = None
                for key in self.box_id_visible:
                    entry = self.box_id_visible[key]
                    if entry[2] and entry[1] == panelidx:
                        self.activesizer[panelidx] = key
                        break
            self.Reposition(panelidx=panelidx)

    def ForcePanel(self, identifier):
        # ForcePanel will make the indicated panel choosable and visible
        try:
            oldflag = self.box_id_visible[identifier][2]
        except (IndexError, KeyError):
            return
        if not oldflag:
            # Make it choosable
            self.box_id_visible[identifier][2] = True
        panelidx = self.box_id_visible[identifier][1]
        self.activesizer[panelidx] = identifier
        self.Reposition(panelidx=panelidx)

    def NextEntryInPanel(self, panelidx):
        if panelidx<0 or panelidx>=self.panelct:
            return
        first_entry = None
        next_entry = None
        visible_seen = False
        for key in self.box_id_visible:
            entry = self.box_id_visible[key]
            if entry[1] == panelidx and entry[2]:
                if key == self.activesizer[panelidx]: # Visible
                    visible_seen = True
                else:
                    if visible_seen and next_entry is None:
                        next_entry = key
                        break
                    else:
                        if first_entry is None:
                            first_entry = key
        if next_entry is None:
            next_entry = first_entry
        if next_entry is not None:
            self.ForcePanel(next_entry)
        else:
            self.activesizer[panelidx] = None

    def PreviousEntryInPanel(self, panelidx):
        if panelidx<0 or panelidx>=self.panelct:
            return
        last_entry = None
        prev_entry = None
        visible_seen = False
        for key in self.box_id_visible:
            entry = self.box_id_visible[key]
            if entry[1] == panelidx and entry[2]:
                if key == self.activesizer[panelidx]: # Visible
                    visible_seen = True
                elif visible_seen:
                    last_entry = key
                else:
                    prev_entry = key
        if prev_entry is None:
            prev_entry = last_entry
        if prev_entry is not None:
            self.ForcePanel(prev_entry)
        else:
            self.activesizer[panelidx] = None

    def on_button_next(self, event):
        button = event.GetEventObject()
        for idx in range(self.panelct):
            if self.nextbuttons[idx] == button:
                self.NextEntryInPanel(idx)
                break
#        self.Reposition()
        event.Skip()

    def on_button_prev(self, event):
        button = event.GetEventObject()
        for idx in range(self.panelct):
            if self.nextbuttons[idx] == button:
                self.PreviousEntryInPanel(idx)
                break
#        self.Reposition()
        event.Skip()

    # Draw the panels
    def Reposition(self, panelidx = None):
        def debug_me():
            for key in self.box_id_visible:
                siz = self.box_id_visible[key][0]
                items = siz.GetItemCount()
                print ("Sizer '%s', children=%s" % (key, items))
                for idx in range(items):
                    print("   Item #%d - shown=%s" % (idx, siz.IsShown(idx)))

        def deep_show_hide(sizerbox, key, showit, callback):
            # print ("Showit: key=%s, flag=%s, idx=%d, default=%s" % (key, showit, debugidx, debugdefault))
            if showit:
                if callback is None:
                    sizerbox.ShowItems(True)
                else:
                    callback(True)
                sizerbox.Show(True)
            else:
                if callback is None:
                    sizerbox.ShowItems(False)
                else:
                    callback(True)
                sizerbox.Hide(True)
            # for siz_item in sizerbox.GetChildren():
            #     wind = siz_item.GetWindow()
            #     if wind is not None:
            #         wind.Show(showit)
            sizerbox.Layout()

        selfrect = self.GetRect()
        if panelidx is None:
            targets = range(self.panelct)
        else:
            targets = (panelidx,)
        for pidx in targets:
            # print("panel # %d has default: %s" % (pidx, self.activesizer[pidx]))
            panelrect = self.GetFieldRect(pidx)
            # Establish the amount of 'choosable' sizers
            ct = 0
            sizer = None
            for key in self.box_id_visible:
                entry = self.box_id_visible[key]
                # print ("%s = %s" %(key, entry) )
                if entry[1] == pidx:
                    if entry[2]: # The right one and choosable...
                        ct += 1
                        if self.activesizer[pidx] is None:
                            self.activesizer[pidx] = key
                        if self.activesizer[pidx] != key: # its not the default, so hide
                            deep_show_hide(entry[0], key, False, entry[3])
                    else: # not choosable --> hide:
                        deep_show_hide(entry[0], key, False, entry[3])
            if ct > 1:
                # Show Button and reduce available width for sizer
                myrect = self.nextbuttons[pidx].GetRect()
                myrect.x = panelrect.x + panelrect.width - myrect.width
                myrect.y = panelrect.y
                self.nextbuttons[pidx].SetRect(myrect)
                panelrect.width -= myrect.width
                self.nextbuttons[pidx].Show(True)
            else:
                self.nextbuttons[pidx].Show(False)
            if self.activesizer[pidx] is not None:
                sizer = self.box_id_visible[self.activesizer[pidx]][0]
                callback = self.box_id_visible[self.activesizer[pidx]][3]
                # print ("Panel %s='%s' - %s" % (pidx, self.activesizer[pidx], panelrect))
                # print ("Entries: %s" % sizer.GetItemCount())
                sizer.SetDimension(panelrect.x, panelrect.y, panelrect.width, panelrect.height)
                deep_show_hide(sizer, self.activesizer[pidx], True, callback)
                text = self.status_text[pidx]
                if text != "":
                    self.previous_text[pidx] = text
                self.SetStatusText("", pidx)
            else:
                self.SetStatusText(self.previous_text[pidx], pidx)
        # debug_me()
        self.sizeChanged = False


    def OnSize(self, evt):
        evt.Skip()
        self.Reposition()  # for normal size events
        self.sizeChanged = True

    def OnIdle(self, evt):
        if self.sizeChanged:
            self.Reposition()


class MeerK40t(MWindow):
    """MeerK40t main window"""

    def __init__(self, *args, **kwds):
        width, height = wx.DisplaySize()

        super().__init__(int(width * 0.9), int(height * 0.9), *args, **kwds)
        try:
            self.EnableTouchEvents(wx.TOUCH_ZOOM_GESTURE | wx.TOUCH_PAN_GESTURES)
        except AttributeError:
            # Not WX 4.1
            pass

        self.context.gui = self
        self.usb_running = False
        context = self.context
        self.register_options_and_choices(context)

        if self.context.disable_tool_tips:
            wx.ToolTip.Enable(False)

        self.root_context = context.root
        self.DragAcceptFiles(True)

        self.needs_saving = False
        self.working_file = None

        self.pipe_state = None
        self.previous_position = None
        self.is_paused = False

        self._mgr = aui.AuiManager()
        self._mgr.SetFlags(self._mgr.GetFlags() | aui.AUI_MGR_LIVE_RESIZE)
        self._mgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.on_pane_closed)
        self._mgr.Bind(aui.EVT_AUI_PANE_ACTIVATED, self.on_pane_active)

        self.ui_visible = True
        self.hidden_panes = []

        # notify AUI which frame to use
        self._mgr.SetManagedWindow(self)

        self.__set_panes()
        self.__set_commands()

        # Menu Bar
        self.main_menubar = wx.MenuBar()
        self.__set_menubars()
        # Status Bar
        self.startup = True
        self.main_statusbar = CustomStatusBar(self, 4)
        self.setup_statusbar_panels()
        self.SetStatusBar(self.main_statusbar)
        self.main_statusbar.SetStatusStyles(
            [wx.SB_SUNKEN] * self.main_statusbar.GetFieldsCount()
        )
        # Set the panel sizes
        sizes = [-3] * self.main_statusbar.GetFieldsCount()
        # Make the first Panel large
        sizes[0] = -4
        # And the last one smaller
        sizes[self.main_statusbar.GetFieldsCount() - 1] = -2
        self.SetStatusWidths(sizes)

        # self.main_statusbar.SetStatusWidths([-1] * self.main_statusbar.GetFieldsCount())
        self.SetStatusBarPane(0)
        self.main_statusbar.SetStatusText("", 0)
        self.startup = False
        # Make sure its showing up properly
        self.main_statusbar.Reposition()

        self.Bind(wx.EVT_MENU_OPEN, self.on_menu_open)
        self.Bind(wx.EVT_MENU_CLOSE, self.on_menu_close)
        self.Bind(wx.EVT_MENU_HIGHLIGHT, self.on_menu_highlight)
        self.DoGiveHelp_called = False
        self.menus_open = 0
        self.top_menu = None  # Needed because event.GetMenu is None for submenu titles

        self.Bind(wx.EVT_DROP_FILES, self.on_drop_file)

        self.__set_properties()
        self.Layout()

        self.__set_titlebar()
        self.__kernel_initialize()

        self.Bind(wx.EVT_SIZE, self.on_size)

        self.CenterOnScreen()

    def setup_statusbar_panels(self):
        def define_selection():
            self.handle_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.stroke_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.stroke_options_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.operation_sizer = wx.BoxSizer(wx.HORIZONTAL)

            # These will fall into the last field
            self.cb_move = wx.CheckBox(self, id=wx.ID_ANY, label=_("Move"))
            self.cb_handle = wx.CheckBox(self, id=wx.ID_ANY, label=_("Resize"))
            self.cb_rotate = wx.CheckBox(self, id=wx.ID_ANY, label=_("Rotate"))
            self.cb_skew = wx.CheckBox(self, id=wx.ID_ANY, label=_("Skew"))
            self.cb_move.SetFont(
                wx.Font(
                    FONT_SIZE,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL,
                )
            )
            self.cb_handle.SetFont(
                wx.Font(
                    FONT_SIZE,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL,
                )
            )
            self.cb_rotate.SetFont(
                wx.Font(
                    FONT_SIZE,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL,
                )
            )
            self.cb_skew.SetFont(
                wx.Font(
                    FONT_SIZE,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL,
                )
            )

            self.Bind(wx.EVT_CHECKBOX, self.on_toggle_move, self.cb_move)
            self.Bind(wx.EVT_CHECKBOX, self.on_toggle_handle, self.cb_handle)
            self.Bind(wx.EVT_CHECKBOX, self.on_toggle_rotate, self.cb_rotate)
            self.Bind(wx.EVT_CHECKBOX, self.on_toggle_skew, self.cb_skew)

            self.cb_move.SetValue(self.context.enable_sel_move)
            self.cb_handle.SetValue(self.context.enable_sel_size)
            self.cb_rotate.SetValue(self.context.enable_sel_rotate)
            self.cb_skew.SetValue(self.context.enable_sel_skew)
            self.cb_move.SetToolTip(_("Toggle visibility of Move-indicator"))
            self.cb_handle.SetToolTip(_("Toggle visibility of Resize-handles"))
            self.cb_rotate.SetToolTip(_("Toggle visibility of Rotation-handles"))
            self.cb_skew.SetToolTip(_("Toggle visibility of Skew-handles"))
            self.handle_sizer.PrependSpacer(5)
            self.handle_sizer.Add(self.cb_move, 1, wx.EXPAND, 0)
            self.handle_sizer.Add(self.cb_handle, 1, wx.EXPAND, 0)
            self.handle_sizer.Add(self.cb_rotate, 1, wx.EXPAND, 0)
            self.handle_sizer.Add(self.cb_skew, 1, wx.EXPAND, 0)

        def define_info():
            self.info_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.info_text1 = wx.StaticText(self, wx.ID_ANY, label="")
            self.info_text2 = wx.StaticText(self, wx.ID_ANY, label="")
            self.info_text3 = wx.StaticText(self, wx.ID_ANY, label="")
            self.info_sizer.PrependSpacer(5)
            self.info_sizer.Add(self.info_text1, 1, wx.EXPAND, 0)
            self.info_sizer.Add(self.info_text2, 1, wx.EXPAND, 0)
            self.info_sizer.Add(self.info_text3, 1, wx.EXPAND, 0)

        def define_color():
            # And now 8 Buttons for Stroke / Fill:
            colors = (
                0xFFFFFF,
                0x000000,
                0xFF0000,
                0x00FF00,
                0x0000FF,
                0xFFFF00,
                0xFF00FF,
                0x00FFFF,
            )
            self.button_color = []
            for idx in range(len(colors)):
                wx_button = wx.Button(self.main_statusbar, id=wx.ID_ANY, size=wx.Size(20,-1), label="")
                wx_button.SetBackgroundColour(wx.Colour(colors[idx]))
                wx_button.SetMinSize(wx.Size(10, -1))
                wx_button.SetToolTip(_("Set stroke-color (right click set fill color)"))
                wx_button.Bind(wx.EVT_BUTTON, self.on_button_color_left)
                wx_button.Bind(wx.EVT_RIGHT_DOWN, self.on_button_color_right)
                self.button_color.append(wx_button)
            for idx in range(len(colors)):
                self.stroke_sizer.Add(self.button_color[idx], 1, wx.EXPAND, 0)

        def define_stroke():
            # Plus one combobox + value field for stroke width
            self.strokewidth_label = wx.StaticText(
                self.main_statusbar, id=wx.ID_ANY, label=_("Stroke:")
            )
            self.strokewidth_label.SetFont(
                wx.Font(
                    FONT_SIZE,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL,
                )
            )
            self.spin_width = wx.TextCtrl(self, id=wx.ID_ANY, value="0.10", style=wx.TE_PROCESS_ENTER)
            self.spin_width.SetFont(
                wx.Font(
                    FONT_SIZE,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL,
                )
            )
            self.spin_width.SetMinSize(wx.Size(30, -1))
            self.spin_width.SetMaxSize(wx.Size(80, -1))

            self.choices = ["px", "pt", "mm", "cm", "inch", "mil"]
            self.combo_units = wx.ComboBox(
                self,
                wx.ID_ANY,
                choices=self.choices,
                style=wx.CB_DROPDOWN | wx.CB_READONLY,
            )
            self.combo_units.SetFont(
                wx.Font(
                    FONT_SIZE,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL,
                )
            )
            self.combo_units.SetMinSize(wx.Size(30, -1))
            self.combo_units.SetMaxSize(wx.Size(120, -1))
            self.combo_units.SetSelection(0)
            self.Bind(wx.EVT_COMBOBOX, self.on_stroke_width, self.combo_units)
            # self.Bind(wx.EVT_TEXT_ENTER, self.on_stroke_width, self.spin_width)
            self.Bind(wx.EVT_TEXT_ENTER, self.on_stroke_width, self.spin_width)
            self.stroke_options_sizer.Add(self.strokewidth_label, 0, wx.EXPAND, 1)
            self.stroke_options_sizer.Add(self.spin_width, 1, wx.EXPAND, 1)
            self.stroke_options_sizer.Add(self.combo_units, 1, wx.EXPAND, 1)

        def define_linecap():
            self.linecap_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.cap_lbl = wx.StaticText(self, wx.ID_ANY, label=_("Cap"))
            self.btn_cap_butt = wx.Button(self, id=wx.ID_ANY, size=wx.Size(30, -1))
            self.btn_cap_butt.SetBitmap(cap_butt_20.GetBitmap(noadjustment=True))
            self.btn_cap_butt.SetMaxSize(wx.Size(50, -1))
            self.btn_cap_butt.SetToolTip(_("Set the end of the lines to a butt-shape"))
            self.btn_cap_butt.Bind(wx.EVT_BUTTON, self.on_cap_butt)

            self.btn_cap_round = wx.Button(self, id=wx.ID_ANY, size=wx.Size(30, -1))
            self.btn_cap_round.SetBitmap(cap_round_20.GetBitmap(noadjustment=True))
            self.btn_cap_round.SetMaxSize(wx.Size(50, -1))
            self.btn_cap_round.SetToolTip(_("Set the end of the lines to a round-shape"))
            self.btn_cap_round.Bind(wx.EVT_BUTTON, self.on_cap_round)

            self.btn_cap_square = wx.Button(self, id=wx.ID_ANY, size=wx.Size(30, -1))
            self.btn_cap_square.SetBitmap(cap_square_20.GetBitmap(noadjustment=True))
            self.btn_cap_square.SetMaxSize(wx.Size(50, -1))
            self.btn_cap_square.SetToolTip(_("Set the end of the lines to a square-shape"))
            self.btn_cap_square.Bind(wx.EVT_BUTTON, self.on_cap_square)

            self.linecap_sizer.Add(self.cap_lbl, 0, wx.EXPAND, 0)
            self.linecap_sizer.Add(self.btn_cap_butt, 1, wx.EXPAND, 0)
            self.linecap_sizer.Add(self.btn_cap_round, 1, wx.EXPAND, 0)
            self.linecap_sizer.Add(self.btn_cap_square, 1, wx.EXPAND, 0)

        def define_linejoin():
            self.linejoin_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.join_lbl = wx.StaticText(self, wx.ID_ANY, label=_("Join"))

            self.btn_join_bevel = wx.Button(self, id=wx.ID_ANY, size=wx.Size(25, -1))
            self.btn_join_bevel.SetBitmap(join_bevel.GetBitmap(noadjustment=True))
            self.btn_join_bevel.SetToolTip(_("Set the join of the lines to a bevel-shape"))
            self.btn_join_bevel.Bind(wx.EVT_BUTTON, self.on_join_bevel)

            self.btn_join_round = wx.Button(self, id=wx.ID_ANY, size=wx.Size(25, -1))
            self.btn_join_round.SetBitmap(join_round.GetBitmap(noadjustment=True))
            self.btn_join_round.SetToolTip(_("Set the join of lines to a round-shape"))
            self.btn_join_round.Bind(wx.EVT_BUTTON, self.on_join_round)

            self.btn_join_miter = wx.Button(self, id=wx.ID_ANY, size=wx.Size(25, -1))
            self.btn_join_miter.SetBitmap(join_miter.GetBitmap(noadjustment=True))
            self.btn_join_miter.SetToolTip(_("Set the join of lines to a miter-shape"))
            self.btn_join_miter.Bind(wx.EVT_BUTTON, self.on_join_miter)

            # self.btn_join_arcs = wx.Button(self, id=wx.ID_ANY, size=wx.Size(25, -1))
            # self.btn_join_arcs.SetBitmap(join_round.GetBitmap(noadjustment=True))
            # self.btn_join_arcs.SetToolTip(_("Set the join of lines to an arc-shape"))
            # self.btn_join_arcs.Bind(wx.EVT_BUTTON, self.on_join_arcs)

            # self.btn_join_miterclip = wx.Button(self, id=wx.ID_ANY, size=wx.Size(25, -1))
            # self.btn_join_miterclip.SetBitmap(join_miter.GetBitmap(noadjustment=True))
            # self.btn_join_miterclip.SetToolTip(_("Set the join of lines to a miter-clip-shape"))
            # self.btn_join_miterclip.Bind(wx.EVT_BUTTON, self.on_join_miterclip)

            self.linejoin_sizer.Add(self.join_lbl, 0, wx.EXPAND, 0)
            self.linejoin_sizer.Add(self.btn_join_bevel, 1, wx.EXPAND, 0)
            self.linejoin_sizer.Add(self.btn_join_round, 1, wx.EXPAND, 0)
            self.linejoin_sizer.Add(self.btn_join_miter, 1, wx.EXPAND, 0)
            # Who the h... needs those?
            # self.linejoin_sizer.Add(self.btn_join_arcs, 1, wx.EXPAND, 0)
            # self.linejoin_sizer.Add(self.btn_join_miterclip, 1, wx.EXPAND, 0)

        def define_fill():
            self.fill_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.fill_lbl = wx.StaticText(self, wx.ID_ANY, label=_("Fill"))
            self.btn_fill_nonzero = wx.Button(self, id=wx.ID_ANY, size=wx.Size(30, -1))
            self.btn_fill_nonzero.SetMaxSize(wx.Size(50, -1))
            self.btn_fill_nonzero.SetBitmap(fill_nonzero.GetBitmap(noadjustment=True))
            self.btn_fill_nonzero.SetToolTip(_("Set the fillstyle to non-zero (regular)"))
            self.btn_fill_nonzero.Bind(wx.EVT_BUTTON, self.on_fill_nonzero)

            self.btn_fill_evenodd = wx.Button(self, id=wx.ID_ANY, size=wx.Size(30, -1))
            self.btn_fill_evenodd.SetBitmap(fill_evenodd.GetBitmap(noadjustment=True))
            self.btn_fill_evenodd.SetMaxSize(wx.Size(50, -1))
            self.btn_fill_evenodd.SetToolTip(_("Set the fillstyle to even-odd (alternating areas)"))
            self.btn_fill_evenodd.Bind(wx.EVT_BUTTON, self.on_fill_evenodd)
            self.fill_sizer.Add(self.fill_lbl, 0, wx.EXPAND, 0)
            self.fill_sizer.Add(self.btn_fill_nonzero, 1, wx.EXPAND, 0)
            self.fill_sizer.Add(self.btn_fill_evenodd, 1, wx.EXPAND, 0)

        def define_assign_options():
            self.assign_option_sizer = wx.BoxSizer(wx.HORIZONTAL)
            choices = [
                _("Leave"),
                _("-> OP"),
                _("-> Elem"),
            ]
            self.cbo_apply_color = wx.ComboBox(self, wx.ID_ANY, choices=choices, value=choices[0], style=wx.CB_READONLY | wx.CB_DROPDOWN)
            self.chk_all_similar = wx.CheckBox(self, wx.ID_ANY, _("Similar"))
            self.chk_exclusive = wx.CheckBox(self, wx.ID_ANY, _("Exclusive"))
            self.cbo_apply_color.SetToolTip(
                _("Leave - neither the color of the operation nor of the elements will be changed") + "\n" +
                _("-> OP - the assigned operation will adopt the color of the element") + "\n" +
                _("-> Elem - the elements will adopt the color of the assigned operation")
            )
            self.chk_all_similar.SetToolTip(_("Assign as well all other elements with the same stroke-color (fill-color if right-click"))
            self.chk_exclusive.SetToolTip(_("When assigning to an operation remove all assignments of the elements to other operations"))
            self.assign_option_sizer.Add(self.cbo_apply_color, 1, wx.EXPAND, 0)
            self.assign_option_sizer.Add(self.chk_all_similar, 1, wx.EXPAND, 0)
            self.assign_option_sizer.Add(self.chk_exclusive, 1, wx.EXPAND, 0)
            self.chk_exclusive.Bind(wx.EVT_CHECKBOX, self.on_chk_exclusive)

        def define_assign_buttons():
            self.iconsize = 20
            self.buttonsize = self.iconsize + 4
            self.MAXBUTTONS = 24
            self.assign_hover = 0
            self.assign_buttons = []
            self.op_nodes= []
            self.assign_sizer = wx.BoxSizer(wx.HORIZONTAL)
            for idx in range(self.MAXBUTTONS):
                btn = wx.Button(self, id=wx.ID_ANY, size=(self.buttonsize, self.buttonsize))
                self.assign_buttons.append(btn)
                self.op_nodes.append(None)
                self.assign_sizer.Add(btn, 1, wx.EXPAND, 0)
                btn.Bind(wx.EVT_ENTER_WINDOW, self.on_assign_mouse_over)
                btn.Bind(wx.EVT_LEAVE_WINDOW, self.on_assign_mouse_leave)
                btn.Bind(wx.EVT_BUTTON, self.on_assign_button_left)
                btn.Bind(wx.EVT_RIGHT_DOWN, self.on_assign_button_right)


        FONT_SIZE = 7
        self.idx_selection = self.main_statusbar.panelct - 1
        self.idx_colors = self.main_statusbar.panelct - 2
        self.idx_assign = self.main_statusbar.panelct - 3

        define_selection()
        self.main_statusbar.AddPanel(self.idx_selection, self.handle_sizer, "selection", False)

        define_info()
        self.main_statusbar.AddPanel(self.idx_selection, self.info_sizer, "infos", False)

        # ----- Color buttons and stroke
        define_color()
        self.main_statusbar.AddPanel(self.idx_colors, self.stroke_sizer, "color", True)

        define_stroke()
        self.main_statusbar.AddPanel(self.idx_colors, self.stroke_options_sizer, "stroke", False)

        define_linecap()
        self.main_statusbar.AddPanel(self.idx_colors, self.linecap_sizer, "linecap", False)

        define_linejoin()
        self.main_statusbar.AddPanel(self.idx_colors, self.linejoin_sizer, "linejoin", False)

        define_fill()
        self.main_statusbar.AddPanel(self.idx_colors, self.fill_sizer, "fillrule", False)

        define_assign_buttons()
        self.main_statusbar.AddPanel(self.idx_assign, self.assign_sizer, "assign", True, callback = self.callback_show_assign_buttons)

        define_assign_options()
        self.main_statusbar.AddPanel(self.idx_assign, self.assign_option_sizer, "assign-options", True)
        # Setup assign buttons
        self.assign_show_stuff(False)

# --------- Logic for operation assignment
    def assign_clear_old(self):
        for idx in range(self.MAXBUTTONS):
            self.op_nodes[idx] = None
            self.assign_buttons[idx].SetBitmap(wx.NullBitmap)
            self.assign_buttons[idx].Show(False)
        if self.assign_hover>0:
            self.main_statusbar.SetStatusText("", 0)
            self.assign_hover = 0

    def assign_set_single_button(self, node):
        def get_bitmap():
            def get_color():
                iconcolor = None
                background = node.color
                if background is not None:
                    c1 = Color("Black")
                    c2 = Color("White")
                    if Color.distance(background, c1)> Color.distance(background, c2):
                        iconcolor = c1
                    else:
                        iconcolor = c2
                return iconcolor, background

            iconsize = 20
            result = None
            d = None
            if node.type == "op raster":
                c, d = get_color()
                result = icons8_direction_20.GetBitmap(color=c, resize=(iconsize, iconsize), noadjustment=True, keepalpha=True)
            elif node.type == "op image":
                c, d = get_color()
                result = icons8_image_20.GetBitmap(color=c, resize=(iconsize, iconsize), noadjustment=True, keepalpha=True)
            elif node.type == "op engrave":
                c, d = get_color()
                result = icons8_small_beam_20.GetBitmap(color=c, resize=(iconsize, iconsize), noadjustment=True, keepalpha=True)
            elif node.type == "op cut":
                c, d = get_color()
                result = icons8_laser_beam_20.GetBitmap(color=c, resize=(iconsize, iconsize), noadjustment=True, keepalpha=True)
            elif node.type == "op hatch":
                c, d = get_color()
                result = icons8_diagonal_20.GetBitmap(color=c, resize=(iconsize, iconsize), noadjustment=True, keepalpha=True)
            elif node.type == "op dots":
                c, d = get_color()
                result = icons8_scatter_plot_20.GetBitmap(color=c, resize=(iconsize, iconsize), noadjustment=True, keepalpha=True)
            return d, result

        def process_button(myidx):
            col, image = get_bitmap()
            if image is None:
                return
            if col is not None:
                self.assign_buttons[myidx].SetBackgroundColour(wx.Colour(swizzlecolor(col)))
            else:
                self.assign_buttons[myidx].SetBackgroundColour(wx.LIGHT_GREY)
            if image is None:
                self.assign_buttons[myidx].SetBitmap(wx.NullBitmap)
            else:
                self.assign_buttons[myidx].SetBitmap(image)
                # self.assign_buttons[myidx].SetBitmapDisabled(icons8_padlock_50.GetBitmap(color=Color("Grey"), resize=(self.iconsize, self.iconsize), noadjustment=True, keepalpha=True))
            self.assign_buttons[myidx].SetToolTip(
                str(node) +
                "\n" +
                _("Assign the selected elements to the operation.") +
                "\n" +
                _("Left click: consider stroke as main color, right click: use fill")
            )
            self.assign_buttons[myidx].Show()

        lastfree = -1
        found = False
        for idx in range(self.MAXBUTTONS):
            if node is self.op_nodes[idx]:
                process_button(idx)
                found = True
                break
            else:
                if lastfree<0 and self.op_nodes[idx] is None:
                    lastfree = idx
        if not found:
            if lastfree>=0:
                self.op_nodes[lastfree] = node
                process_button(lastfree)

    def assign_set_buttons(self):
        self.assign_clear_old()
        idx = 0
        for node in list(self.context.elements.flat(types=op_nodes)):
            if node.type.startswith("op "):
                self.op_nodes[idx] = node
                self.assign_set_single_button(node)
                idx += 1
                if idx>=self.MAXBUTTONS:
                    # too many...
                    break
        # We need to call reposition for the updates to be seen
        self.main_statusbar.Reposition(panelidx=self.idx_assign)

    def assign_show_stuff(self, flag):
        if flag:
            self.assign_set_buttons()
        self.chk_all_similar.Enable(flag)
        self.cbo_apply_color.Enable(flag)
        self.chk_exclusive.Enable(flag)

        for idx in range(self.MAXBUTTONS):
            myflag = flag and self.op_nodes[idx] is not None
            self.assign_buttons[idx].Enable(myflag)
            self.assign_buttons[idx].Enable(myflag)
        if not flag:
            if self.assign_hover>0:
                self.main_statusbar.SetStatusText("", 0)
                self.assign_hover = 0
        else:
             self.chk_exclusive.SetValue(self.context.elements.classify_inherit_exclusive)
        self.main_statusbar.Reposition(self.idx_assign)

    # --- Listen to external events to update the bar
    @signal_listener("element_property_reload")
    @signal_listener("element_property_update")
    def on_element_update(self, origin, *args):
        """
        Called by 'element_property_update' when the properties of an element are changed.

        @param origin: the path of the originating signal
        @param args:
        @return:
        """
        if len(args) > 0:
            # Need to do all?!
            element = args[0]
            if isinstance(element, (tuple, list)):
                for node in element:
                    if node.type.startswith("op "):
                        self.assign_set_single_button(node)
            else:
                if element.type.startswith("op "):
                    self.assign_set_single_button(element)

    @signal_listener("rebuild_tree")
    @signal_listener("refresh_tree")
    @signal_listener("tree_changed")
    @signal_listener("operation_removed")
    @signal_listener("add_operation")
    def on_rebuild(self, origin, *args):
        self.assign_set_buttons()

    def callback_show_assign_buttons(self, showit):
        # Callback function that decideds whether to show an element or not
        if showit:
            for idx, btn in enumerate(self.assign_buttons):
                if self.op_nodes[idx] is None:
                    btn.Show(False)
                else:
                    btn.Show(True)
        else:
            for btn in self.assign_buttons:
                btn.Show(False)

    def on_assign_mouse_leave(self, event):
        # Leave events of one tool may come later than the enter events of the next
        self.assign_hover -= 1
        if self.assign_hover<0:
            self.assign_hover = 0
        if self.assign_hover == 0:
            self.main_statusbar.SetStatusText("", 0)
        event.Skip()

    def on_assign_mouse_over(self, event):
        button = event.GetEventObject()
        msg = ""
        for idx in range(self.MAXBUTTONS):
            if button == self.assign_buttons[idx]:
                msg = str(self.op_nodes[idx])
        self.assign_hover += 1
        self.main_statusbar.SetStatusText(msg, 0)
        event.Skip()

    def execute_on(self, targetop, attrib):
        data = list(self.context.elements.flat(emphasized = True))
        idx = self.cbo_apply_color.GetCurrentSelection()
        if idx==1:
            impose = "to_op"
        elif idx==2:
            impose = "to_elem"
        else:
            impose = None
        similar = self.chk_all_similar.GetValue()
        exclusive = self.chk_exclusive.GetValue()
        if len(data) == 0:
            return
        self.context.elements.assign_operation(
            op_assign=targetop, data=data, impose=impose,
            attrib = attrib, similar=similar, exclusive = exclusive)

    def on_assign_button_left(self, event):
        button = event.GetEventObject()
        for idx in range(self.MAXBUTTONS):
            if button == self.assign_buttons[idx]:
                node = self.op_nodes[idx]
                self.execute_on(node, "stroke")
                break
        event.Skip()

    def on_assign_button_right(self, event):
        button = event.GetEventObject()
        for idx in range(self.MAXBUTTONS):
            if button == self.assign_buttons[idx]:
                node = self.op_nodes[idx]
                self.execute_on(node, "fill")
                break
        event.Skip()

    def on_chk_exclusive(self, event):
        newval = self.chk_exclusive.GetValue()
        self.context.elements.classify_inherit_exclusive = newval

# --------- Events for status bar

    def assign_fill(self, filltype):
        self.context("fillrule {fill}".format(fill=filltype))

    def on_fill_evenodd(self, event):
        self.assign_fill("evenodd")

    def on_fill_nonzero(self, event):
        self.assign_fill("nonzero")

    def assign_cap(self, captype):
        self.context("linecap {cap}".format(cap=captype))

    def on_cap_square(self, event):
        self.assign_cap("square")

    def on_cap_butt(self, event):
        self.assign_cap("butt")

    def on_cap_round(self, event):
        self.assign_cap("round")

    def assign_join(self, jointype):
        self.context("linejoin {join}".format(join=jointype))

    def on_join_miter(self, event):
        self.assign_join("miter")

    def on_join_miterclip(self, event):
        self.assign_join("miter-clip")

    def on_join_bevel(self, event):
        self.assign_join("bevel")

    def on_join_arcs(self, event):
        self.assign_join("arcs")

    def on_join_round(self, event):
        self.assign_join("round")

    # the checkbox was clicked
    def on_toggle_move(self, event):
        if not self.startup:
            value = self.cb_move.GetValue()
            self.context.enable_sel_move = value
            self.context.signal("refresh_scene", "Scene")

    def on_toggle_handle(self, event):
        if not self.startup:
            value = self.cb_handle.GetValue()
            self.context.enable_sel_size = value
            self.context.signal("refresh_scene", "Scene")

    def on_toggle_rotate(self, event):
        if not self.startup:
            value = self.cb_rotate.GetValue()
            self.context.enable_sel_rotate = value
            self.context.signal("refresh_scene", "Scene")

    def on_toggle_skew(self, event):
        if not self.startup:
            value = self.cb_skew.GetValue()
            self.context.enable_sel_skew = value
            self.context.signal("refresh_scene", "Scene")

    def on_button_color_left(self, event):
        # Okay my backgroundcolor is...
        if not self.startup:
            button = event.EventObject
            color = button.GetBackgroundColour()
            rgb = [color.Red(), color.Green(), color.Blue()]
            if rgb[0] == 255 and rgb[1] == 255 and rgb[2] == 255:
                colstr = "none"
            else:
                colstr = "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])
            self.context("stroke %s --classify\n" % colstr)
            self.context.signal("selstroke", rgb)

    def on_button_color_right(self, event):
        # Okay my backgroundcolor is...
        if not self.startup:
            button = event.EventObject
            color = button.GetBackgroundColour()
            rgb = [color.Red(), color.Green(), color.Blue()]
            if rgb[0] == 255 and rgb[1] == 255 and rgb[2] == 255:
                colstr = "none"
            else:
                colstr = "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])
            self.context("fill %s --classify\n" % colstr)
            self.context.signal("selfill", rgb)

    def on_stroke_width(self, event):
        if not self.startup:
            chg = False
            if self.combo_units.GetSelection() >= 0:
                newunit = self.choices[self.combo_units.GetSelection()]
                try:
                    newval = float(self.spin_width.GetValue())
                    chg = True
                except ValueError:
                    chg = False
            if chg:
                value = "{wd:.2f}{unit}".format(wd=newval, unit=newunit)
                mysignal = "selstrokewidth"
                self.context.signal(mysignal, value)

    @signal_listener("emphasized")
    def on_update_statusbar(self, origin, *args):
        # First enable/disable the controls in the statusbar
        elements = self.context.elements
        ct = 0
        total_area = 0
        total_length = 0
        _mm = float(Length("1{unit}".format(unit="mm")))
        for e in elements.flat(types=elem_nodes, emphasized=True):
            ct += 1
            this_area, this_length = elements.get_information(e, fine = False)
            total_area += this_area
            total_length += this_length

        value = ct > 0
        total_area = total_area / (_mm * _mm)
        total_length = total_length / _mm
        self.info_text1.SetLabel("# = %d" % ct)
        self.info_text2.SetLabel("A = %.1f mm²" % total_area)
        self.info_text3.SetLabel("D = %.1f mm" % total_length)

        self.assign_show_stuff(value)
        self.main_statusbar.ActivatePanel("selection", value)
        self.main_statusbar.ActivatePanel("infos", value)
        self.main_statusbar.ActivatePanel("fillrule", value)
        self.main_statusbar.ActivatePanel("linejoin", value)
        self.main_statusbar.ActivatePanel("linecap", value)
        self.main_statusbar.ActivatePanel("stroke", value)
        self.main_statusbar.Reposition()
    #         if self.context.show_colorbar:
    #             if self._cb_enabled != cb_enabled:
    #                 # Keep old values...
    #                 for idx, text in enumerate(self.status_text):
    #                     self.previous_text[idx] = text
    #                 self.SetStatusText("", self.pos_handle_options)
    #                 self.SetStatusText("", self.pos_stroke)
    #                 self.SetStatusText("", self.pos_colorbar)
    #             sw_default = None
    #             for e in self.context.elements.flat(types=elem_nodes, emphasized=True):
    #                 if hasattr(e, "stroke_width"):
    #                     if sw_default is None:
    #                         sw_default = e.stroke_width
    #                         break
    #             if not sw_default is None:
    #                 # Set Values
    #                 self.startup = True
    #                 stdlen = float(Length("1mm"))
    #                 value = "%.2f" % (sw_default / stdlen)
    #                 self.spin_width.SetValue(value)
    #                 self.combo_units.SetSelection(self.choices.index("mm"))
    #                 self.startup = False


# ------------ Setup
    def register_options_and_choices(self, context):
        _ = context._
        context.setting(bool, "disable_tool_tips", False)
        context.setting(bool, "disable_auto_zoom", False)
        context.setting(bool, "enable_sel_move", True)
        context.setting(bool, "enable_sel_size", True)
        context.setting(bool, "enable_sel_rotate", True)
        context.setting(bool, "enable_sel_skew", False)
        context.setting(int, "zoom_level", 4) # 4%
        # Standard-Icon-Sizes
        # default, factor 1 - leave as is
        # small = factor 2/3, min_size = 32
        # tiny  = factor 1/2, min_size = 25
        context.setting(str, "icon_size", "default")
        # Ribbon-Size (NOT YET ACTIVE)
        # default - std icon size + panel-labels,
        # small - std icon size / no labels
        # tiny - reduced icon size / no labels
        context.setting(str, "ribbon_appearance", "default")
        choices = [
            {
                "attr": "ribbon_appearance",
                "object": self.context.root,
                "default": "default",
                "type": str,
                "style": "combosmall",
                "choices": [
                    "default",
                    "small",
                    "tiny"
                ],
                "label": _("Ribbon-Size:"),
                "tip": _("Appearance of ribbon at the top (requires a restart to take effect))"),
                "page": "Gui",
                "section": "Appearance",
            },
        ]
        # context.kernel.register_choices("preferences", choices)
        choices = [
            {
                "attr": "icon_size",
                "object": self.context.root,
                "default": "default",
                "type": str,
                "style": "combosmall",
                "choices": [
                    "large",
                    "big",
                    "default",
                    "small",
                    "tiny"
                ],
                "label": _("Icon size:"),
                "tip": _("Appearance of all icons in the GUI (requires a restart to take effect))"),
                "page": "Gui",
                "section": "Appearance",
            },
        ]
        context.kernel.register_choices("preferences", choices)

        choices = [
            {
                "attr": "zoom_level",
                "object": self.context.root,
                "default": 4,
                "trailer": "%",
                "type": int,
                "style": "combosmall",
                "choices": [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    15,
                    20,
                    25,
                ],
                "label": _("Default zoom level:"),
                "tip": _("Default zoom level when changing zoom (automatically or via Ctrl-B)"),
                "page": "Gui",
                "section": "Zoom",
            },
        ]
        context.kernel.register_choices("preferences", choices)
        choices = [
            {
                "attr": "disable_auto_zoom",
                "object": self.context.root,
                "default": False,
                "type": bool,
                "label": _("Don't autoadjust zoom level"),
                "tip": _("Don't autoadjust zoom level when resizing the main window"),
                "page": "Gui",
                "section": "Zoom",
            },
        ]
        context.kernel.register_choices("preferences", choices)

        choices = [
            {
                "attr": "select_smallest",
                "object": context.root,
                "default": True,
                "type": bool,
                "label": _("Select smallest element on scene"),
                "tip": _(
                    "Active: Single click selects the smallest element under cursor (ctrl+click selects the largest) / Inactive: Single click selects the largest element  (ctrl+click the smallest)."
                ),
                "page": "Scene",
                "section": "General",
            },
        ]
        context.kernel.register_choices("preferences", choices)

        choices = [
            {
                "attr": "show_colorbar",
                "object": self.context.root,
                "default": True,
                "type": bool,
                "label": _("Display colorbar in statusbar"),
                "tip": _(
                    "Enable the display of a colorbar at the bottom of the screen."
                ),
                "page": "Gui",
                "section": "General",
            },
        ]
        context.kernel.register_choices("preferences", choices)

        choices = [
            {
                "attr": "outer_handles",
                "object": context.root,
                "default": False,
                "type": bool,
                "label": _("Draw selection handle outside of bounding box"),
                "tip": _(
                    "Active: draw handles outside of / Inactive: Draw them on the bounding box of the selection."
                ),
                "page": "Scene",
                "section": "General",
            },
        ]
        context.kernel.register_choices("preferences", choices)

        choices = [
            {
                "attr": "show_attract_len",
                "object": context.root,
                "default": 45,
                "type": int,
                "style": "slider",
                "min": 1,
                "max": 75,
                "label": _("Distance"),
                "tip": _("Defines until which distance snap points will be highlighted"),
                "page": "Scene",
                "section": "Snap-Options",
            },
            {
                "attr": "snap_points",
                "object": context.root,
                "default": True,
                "type": bool,
                "label": _("Snap to element"),
                "tip": _("Shall the cursor snap to the next element point?"),
                "page": "Scene",
                "section": "Snap-Options",
            },
            {
                "attr": "action_attract_len",
                "object": context.root,
                "conditional": (context.root, "snap_points"),
                "default": 20,
                "type": int,
                "style": "slider",
                "min": 1,
                "max": 75,
                "label": _("Distance"),
                "tip": _("Set the distance inside which the cursor will snap to the next element point"),
                "page": "Scene",
                "section": "Snap-Options",
            },
            {
                "attr": "snap_grid",
                "object": context.root,
                "default": True,
                "type": bool,
                "label": _("Snap to Grid"),
                "tip": _("Shall the cursor snap to the next grid intersection?"),
                "page": "Scene",
                "section": "Snap-Options",
            },
            {
                "attr": "grid_attract_len",
                "object": context.root,
                "default": 15,
                "conditional": (context.root, "snap_grid"),
                "type": int,
                "style": "slider",
                "min": 1,
                "max": 75,
                "label": _("Distance"),
                "tip": _("Set the distance inside which the cursor will snap to the next grid intersection"),
                "page": "Scene",
                "section": "Snap-Options",
            },
        ]
        context.kernel.register_choices("preferences", choices)
        choices = [
            {
                "attr": "menu_autohide",
                "object": context.root,
                "default": True,
                "type": bool,
                "label": _("Menu auto-minimize"),
                "tip": _(
                    "The scene-menu will minimize itself automatically after selection of a tool."
                ),
                "page": "Gui",
                "section": "Scene",
            },
        ]
        context.kernel.register_choices("preferences", choices)

        context.register(
            "function/open_property_window_for_node", self.open_property_window_for_node
        )
        if context.icon_size == "tiny":
            set_icon_appearance(0.5, int(0.5 * STD_ICON_SIZE))
        elif context.icon_size == "small":
            set_icon_appearance(2/3, int(2/3 * STD_ICON_SIZE))
        elif context.icon_size == "big":
            set_icon_appearance(1.5, 0)
        elif context.icon_size == "large":
            set_icon_appearance(2.0, 0)
        else:
            set_icon_appearance(1.0, 0)

    def open_property_window_for_node(self, node):
        """
        Activate the node in question.

        @param node:
        @return:
        """
        gui = self
        root = self.context.root
        root.open("window/Properties", gui)

    @staticmethod
    def sub_register(kernel):
        buttonsize = STD_ICON_SIZE
        kernel.register(
            "button/project/Open",
            {
                "label": _("Open"),
                "icon": icons8_opened_folder_50,
                "tip": _("Opens new project"),
                "action": lambda e: kernel.console(".dialog_load\n"),
                "priority": -200,
                "size": buttonsize,
            },
        )
        kernel.register(
            "button/project/Save",
            {
                "label": _("Save"),
                "icon": icons8_save_50,
                "tip": _("Saves a project to disk"),
                "action": lambda e: kernel.console(".dialog_save\n"),
                "priority": -100,
                "size": buttonsize,
            },
        )

        # Default Size for tool buttons - none: use icon size
        buttonsize = STD_ICON_SIZE

        kernel.register(
            "button/tools/Scene",
            {
                "label": _("Select"),
                "icon": icons8_cursor_50,
                "tip": _("Regular selection tool"),
                "action": lambda v: kernel.elements("tool none\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "none",
            },
        )

        kernel.register(
            "button/tools/Relocate",
            {
                "label": _("Set Position"),
                "icon": icons8_place_marker_50,
                "tip": _("Set position to given location"),
                "action": lambda v: kernel.elements("tool relocate\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "relocate",
            },
        )

        kernel.register(
            "button/tools/Draw",
            {
                "label": _("Draw"),
                "icon": icons8_pencil_drawing_50,
                "tip": _("Add a free-drawing element"),
                "action": lambda v: kernel.elements("tool draw\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "draw",
            },
        )

        kernel.register(
            "button/tools/ellipse",
            {
                "label": _("Ellipse"),
                "icon": icons8_oval_50,
                "tip": _("Add an ellipse element"),
                "action": lambda v: kernel.elements("tool ellipse\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "ellipse",
            },
        )

        kernel.register(
            "button/tools/circle",
            {
                "label": _("Circle"),
                "icon": icons8_circle_50,
                "tip": _("Add a circle element"),
                "action": lambda v: kernel.elements("tool circle\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "circle",
            },
        )

        kernel.register(
            "button/tools/Polygon",
            {
                "label": _("Polygon"),
                "icon": icons8_polygon_50,
                "tip": _(
                    "Add a polygon element\nLeft click: point/line\nDouble click: complete\nRight click: cancel"
                ),
                "action": lambda v: kernel.elements("tool polygon\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "polygon",
            },
        )

        kernel.register(
            "button/tools/Polyline",
            {
                "label": _("Polyline"),
                "icon": icons8_polyline_50,
                "tip": _(
                    "Add a polyline element\nLeft click: point/line\nDouble click: complete\nRight click: cancel"
                ),
                "action": lambda v: kernel.elements("tool polyline\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "polyline",
            },
        )

        kernel.register(
            "button/tools/Rectangle",
            {
                "label": _("Rectangle"),
                "icon": icons8_rectangular_50,
                "tip": _("Add a rectangular element"),
                "action": lambda v: kernel.elements("tool rect\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "rect",
            },
        )

        kernel.register(
            "button/tools/Point",
            {
                "label": _("Point"),
                "icon": icons8_point_50,
                "tip": _("Add point to the scene"),
                "action": lambda v: kernel.elements("tool point\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "point",
            },
        )

        kernel.register(
            "button/tools/Vector",
            {
                "label": _("Vector"),
                "icon": icons8_vector_50,
                "tip": _(
                    "Add a shape\nLeft click: point/line\nClick and hold: curve\nDouble click: complete\nRight click: cancel"
                ),
                "action": lambda v: kernel.elements("tool vector\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "vector",
            },
        )

        kernel.register(
            "button/tools/Text",
            {
                "label": _("Text"),
                "icon": icons8_type_50,
                "tip": _("Add a text element"),
                "action": lambda v: kernel.elements("tool text\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "text",
            },
        )

        kernel.register(
            "button/tools/Measure",
            {
                "label": _("Measure"),
                "icon": icons8_measure_50,
                "tip": _(
                    "Measure distance / perimeter / area\nLeft click: point/line\nDouble click: complete\nRight click: cancel"
                ),
                "action": lambda v: kernel.elements("tool measure\n"),
                "group": "tool",
                "size": buttonsize,
                "identifier": "measure",
            },
        )
        # Default Size for smaller buttons
        buttonsize = STD_ICON_SIZE / 2

        kernel.register(
            "button/modify/Flip",
            {
                "label": _("Flip Vertical"),
                "icon": icons8_flip_vertical,
                "tip": _("Flip the selected element vertically"),
                "action": lambda v: kernel.elements("scale 1 -1\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 0,
            },
        )
        kernel.register(
            "button/modify/Mirror",
            {
                "label": _("Mirror Horizontal"),
                "icon": icons8_mirror_horizontal,
                "tip": _("Mirror the selected element horizontally"),
                "action": lambda v: kernel.elements("scale -1 1\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 0,
            },
        )
        kernel.register(
            "button/modify/Rotate90CW",
            {
                "label": _("Rotate CW"),
                "icon": icons8_rotate_right_50,
                "tip": _("Rotate the selected element clockwise by 90 deg"),
                "action": lambda v: kernel.elements("rotate 90deg\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 0,
            },
        )
        kernel.register(
            "button/modify/Rotate90CCW",
            {
                "label": _("Rotate CCW"),
                "icon": icons8_rotate_left_50,
                "tip": _("Rotate the selected element counterclockwise by 90 deg"),
                "action": lambda v: kernel.elements("rotate -90deg\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 0,
            },
        )
        kernel.register(
            "button/geometry/Union",
            {
                "label": _("Union"),
                "icon": icon_cag_union_50,
                "tip": _("Create a union of the selected elements"),
                "action": lambda v: kernel.elements("element union\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 1,
            },
        )
        kernel.register(
            "button/geometry/Difference",
            {
                "label": _("Difference"),
                "icon": icon_cag_subtract_50,
                "tip": _("Create a difference of the selected elements"),
                "action": lambda v: kernel.elements("element difference\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 1,
            },
        )
        kernel.register(
            "button/geometry/Xor",
            {
                "label": _("Xor"),
                "icon": icon_cag_xor_50,
                "tip": _("Create a xor of the selected elements"),
                "action": lambda v: kernel.elements("element xor\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 1,
            },
        )
        kernel.register(
            "button/geometry/Intersection",
            {
                "label": _("Intersection"),
                "icon": icon_cag_common_50,
                "tip": _("Create a intersection of the selected elements"),
                "action": lambda v: kernel.elements("element intersection\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 1,
            },
        )

        def group_selection():
            group_node = None
            lets_do_it = False
            data = list(kernel.elements.elems(emphasized=True))
            sel_count = len(data)
            my_parent = None
            for node in data:
                this_parent = None
                if hasattr(node, "parent"):
                    if hasattr(node.parent, "type"):
                        if node.parent.type in ("group", "file"):
                            this_parent = node.parent
                if my_parent is None:
                    if this_parent is not None:
                        my_parent = this_parent
                else:
                    if my_parent != this_parent:
                        # different parents, so definitely a do it
                        lets_do_it = True
                        break
            if not lets_do_it:
                if my_parent is None:
                    # All base elements
                    lets_do_it = True
                else:
                    parent_ct = len(my_parent.children)
                    if parent_ct != sel_count:
                        # Not the full group...
                        lets_do_it = True

            if lets_do_it:
                for node in data:
                    if group_node is None:
                        group_node = node.parent.add(type="group", label="Group")
                    group_node.append_child(node)
                kernel.signal("element_property_reload", "Scene", group_node)

        kernel.register(
            "button/geometry/Group",
            {
                "label": _("Group"),
                "icon": icons8_group_objects_50,
                "tip": _("Group elements together"),
                "action": lambda v: group_selection(),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 1,
            },
        )

        def ungroup_selection():
            def release_em(node):
                for n in list(node.children):
                    node.insert_sibling(n)
                node.remove_node()  # Removing group/file node.
            found_some = False
            for node in list(kernel.elements.elems(emphasized=True)):
                if not node is None:
                    if node.type in ("group", "file"):
                        found_some = True
                        release_em(node)
            if not found_some:
                # So let's see that we address the parents...
                for node in list(kernel.elements.elems(emphasized=True)):
                    if not node is None:
                        if hasattr(node, "parent"):
                            if hasattr(node.parent, "type"):
                                if node.parent.type in ("group", "file"):
                                    release_em(node.parent)

        def part_of_group():
            result = False
            for node in list(kernel.elements.elems(emphasized=True)):
                if hasattr(node, "parent"):
                    if node.parent.type in ("group", "file"):
                        result = True
                        break
            return result

        kernel.register(
            "button/geometry/Ungroup",
            {
                "label": _("Ungroup"),
                "icon": icons8_ungroup_objects_50,
                "tip": _("Ungroup elements"),
                "action": lambda v: ungroup_selection(),
                "size": buttonsize,
                "rule_enabled": lambda cond: part_of_group(),
            },
        )
        kernel.register(
            "button/align/AlignLeft",
            {
                "label": _("Align Left"),
                "icon": icons8_align_left_50,
                "tip": _(
                    "Align selected elements at the leftmost position (right click: of the bed)"
                ),
                "action": lambda v: kernel.elements("align left\n"),
                "right": lambda v: kernel.elements("align bedleft\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 0,
            },
        )
        kernel.register(
            "button/align/AlignRight",
            {
                "label": _("Align Right"),
                "icon": icons8_align_right_50,
                "tip": _(
                    "Align selected elements at the rightmost position (right click: of the bed)"
                ),
                "action": lambda v: kernel.elements("align right\n"),
                "right": lambda v: kernel.elements("align bedright\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 0,
            },
        )
        kernel.register(
            "button/align/AlignTop",
            {
                "label": _("Align Top"),
                "icon": icons8_align_top_50,
                "tip": _(
                    "Align selected elements at the topmost position (right click: of the bed)"
                ),
                "action": lambda v: kernel.elements("align top\n"),
                "right": lambda v: kernel.elements("align bedtop\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 0,
            },
        )
        kernel.register(
            "button/align/AlignBottom",
            {
                "label": _("Align Bottom"),
                "icon": icons8_align_bottom_50,
                "tip": _(
                    "Align selected elements at the lowest position (right click: of the bed)"
                ),
                "action": lambda v: kernel.elements("align bottom\n"),
                "right": lambda v: kernel.elements("align bedbottom\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 0,
            },
        )
        kernel.register(
            "button/align/AlignCenter",
            {
                "label": _("Align Center"),
                "icon": icons_centerize,
                "tip": _(
                    "Align selected elements at their center (right click: of the bed)"
                ),
                "action": lambda v: kernel.elements("align center\n"),
                "right": lambda v: kernel.elements("align bedcenter\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 0,
            },
        )
        kernel.register(
            "button/align/AlignHorizontally",
            {
                "label": _("Distr. Hor."),
                "icon": icons_evenspace_horiz,
                "tip": _("Distribute Space Horizontally"),
                "action": lambda v: kernel.elements("align spaceh\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 2,
            },
        )
        kernel.register(
            "button/align/AlignVertically",
            {
                "label": _("Distr. Vert."),
                "icon": icons_evenspace_vert,
                "tip": _("Distribute Space Vertically"),
                "action": lambda v: kernel.elements("align spacev\n"),
                "size": buttonsize,
                "rule_enabled": lambda cond: len(list(kernel.elements.elems(emphasized=True))) > 2,
            },
        )

    def window_menu(self):
        return False

    def __set_commands(self):
        context = self.context
        gui = self

        @context.console_command("dialog_transform", hidden=True)
        def transform(**kwargs):
            dlg = wx.TextEntryDialog(
                gui,
                _(
                    "Enter SVG Transform Instruction e.g. 'scale(1.49, 1, $x, $y)', rotate, translate, etc..."
                ),
                _("Transform Entry"),
                "",
            )
            dlg.SetValue("")

            if dlg.ShowModal() == wx.ID_OK:
                elements = context.elements

                m = str(dlg.GetValue())
                x, y = self.context.device.current
                m = m.replace("$x", str(x))
                m = m.replace("$y", str(y))
                matrix = Matrix(m)
                unit_width = context.device.unit_width
                unit_height = context.device.unit_height
                matrix.render(ppi=UNITS_PER_INCH, width=unit_width, height=unit_height)
                if matrix.is_identity():
                    dlg.Destroy()
                    dlg = wx.MessageDialog(
                        None,
                        _("The entered command does nothing."),
                        _("Non-Useful Matrix."),
                        wx.OK | wx.ICON_WARNING,
                    )
                    dlg.ShowModal()
                    dlg.Destroy()
                else:
                    for element in elements.elems():
                        try:
                            element.matrix *= matrix
                            element.modified()
                        except AttributeError:
                            pass

        @context.console_command("dialog_flip", hidden=True)
        def flip(**kwargs):
            dlg = wx.TextEntryDialog(
                gui,
                _(
                    "Material must be jigged at 0,0 either home or home offset.\nHow wide is your material (give units: in, mm, cm, px, etc)?"
                ),
                _("Double Side Flip"),
                "",
            )
            dlg.SetValue("")
            if dlg.ShowModal() == wx.ID_OK:
                unit_width = context.device.unit_width
                length = float(Length(dlg.GetValue(), relative_length=unit_width))
                matrix = Matrix()
                matrix.post_scale(-1.0, 1, length / 2.0, 0)
                for element in context.elements.elems(emphasized=True):
                    try:
                        element.matrix *= matrix
                        element.modified()
                    except AttributeError:
                        pass
            dlg.Destroy()

        @context.console_command("dialog_path", hidden=True)
        def path(**kwargs):
            dlg = wx.TextEntryDialog(gui, _("Enter SVG Path Data"), _("Path Entry"), "")
            dlg.SetValue("")

            if dlg.ShowModal() == wx.ID_OK:
                path = Path(dlg.GetValue())
                path.stroke = "blue"
                p = abs(path)
                node = context.elements.elem_branch.add(path=p, type="elem path")
                context.elements.classify([node])
            dlg.Destroy()

        @context.console_command("dialog_fill", hidden=True)
        def fill(**kwargs):
            elements = context.elements
            first_selected = elements.first_element(emphasized=True)
            if first_selected is None:
                return
            data = wx.ColourData()
            if first_selected.fill is not None and first_selected.fill != "none":
                data.SetColour(wx.Colour(swizzlecolor(first_selected.fill)))
            dlg = wx.ColourDialog(gui, data)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                color = data.GetColour()
                rgb = color.GetRGB()
                color = swizzlecolor(rgb)
                color = Color(color, 1.0)
                for elem in elements.elems(emphasized=True):
                    elem.fill = color
                    elem.altered()

        @context.console_command("dialog_stroke", hidden=True)
        def stroke(**kwargs):
            elements = context.elements
            first_selected = elements.first_element(emphasized=True)
            if first_selected is None:
                return
            data = wx.ColourData()
            if first_selected.stroke is not None and first_selected.stroke != "none":
                data.SetColour(wx.Colour(swizzlecolor(first_selected.stroke)))
            dlg = wx.ColourDialog(gui, data)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                color = data.GetColour()
                rgb = color.GetRGB()
                color = swizzlecolor(rgb)
                color = Color(color, 1.0)
                for elem in elements.elems(emphasized=True):
                    elem.stroke = color
                    elem.altered()

        @context.console_command("dialog_gear", hidden=True)
        def gear(**kwargs):
            dlg = wx.TextEntryDialog(gui, _("Enter Forced Gear"), _("Gear Entry"), "")
            dlg.SetValue("")

            if dlg.ShowModal() == wx.ID_OK:
                value = dlg.GetValue()
                if value in ("0", "1", "2", "3", "4"):
                    context._stepping_force = int(value)
                else:
                    context._stepping_force = None
            dlg.Destroy()

        @context.console_argument(
            "message", help=_("Message to display, optional"), default=""
        )
        @context.console_command("interrupt", hidden=True)
        def interrupt(message="", **kwargs):
            if not message:
                message = _("Spooling Interrupted.")

            dlg = wx.MessageDialog(
                None,
                message + "\n\n" + _("Press OK to Continue."),
                _("Interrupt"),
                wx.OK,
            )
            dlg.ShowModal()
            dlg.Destroy()

        @context.console_command("dialog_load", hidden=True)
        def load_dialog(**kwargs):
            # This code should load just specific project files rather than all importable formats.
            files = context.elements.load_types()
            with wx.FileDialog(
                gui, _("Open"), wildcard=files, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind
                pathname = fileDialog.GetPath()
                gui.clear_and_open(pathname)

        @context.console_command("dialog_import", hidden=True)
        def import_dialog(**kwargs):
            files = context.elements.load_types()
            with wx.FileDialog(
                gui,
                _("Import"),
                wildcard=files,
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind
                pathname = fileDialog.GetPath()
                gui.load(pathname)

        @context.console_command("dialog_save_as", hidden=True)
        def save_dialog(**kwargs):
            files = context.elements.save_types()
            with wx.FileDialog(
                gui,
                _("Save Project"),
                wildcard=files,
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind
                pathname = fileDialog.GetPath()
                if not pathname.lower().endswith(".svg"):
                    pathname += ".svg"
                context.elements.save(pathname)
                gui.validate_save()
                gui.working_file = pathname
                gui.set_file_as_recently_used(gui.working_file)

        @context.console_command("dialog_save", hidden=True)
        def save_or_save_as(**kwargs):
            if gui.working_file is None:
                context(".dialog_save_as\n")
            else:
                gui.set_file_as_recently_used(gui.working_file)
                gui.validate_save()
                context.elements.save(gui.working_file)

        @context.console_command("dialog_import_egv", hidden=True)
        def egv_in_dialog(**kwargs):
            files = "*.egv"
            with wx.FileDialog(
                gui,
                _("Import EGV"),
                wildcard=files,
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind
                pathname = fileDialog.GetPath()
            if pathname is None:
                return
            with wx.BusyInfo(_("Loading File...")):
                context("egv_import %s\n" % pathname)
                return

        @context.console_command("dialog_export_egv", hidden=True)
        def egv_out_dialog(**kwargs):
            files = "*.egv"
            with wx.FileDialog(
                gui, _("Export EGV"), wildcard=files, style=wx.FD_SAVE
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind
                pathname = fileDialog.GetPath()
            if pathname is None:
                return
            with wx.BusyInfo(_("Saving File...")):
                context("egv_export %s\n" % pathname)
                return

    def __set_panes(self):
        self.context.setting(bool, "pane_lock", False)

        for register_panel in list(self.context.lookup_all("wxpane")):
            register_panel(self, self.context)

        # AUI Manager Update.
        self._mgr.Update()

        self.default_perspective = self._mgr.SavePerspective()
        self.context.setting(str, "perspective")
        if self.context.perspective is not None:
            self._mgr.LoadPerspective(self.context.perspective)

        self.on_config_panes()
        self.__console_commands()

    def __console_commands(self):
        context = self.context

        @context.console_command(
            "pane",
            help=_("control various panes for main window"),
            output_type="panes",
        )
        def panes(**kwargs):
            return "panes", self

        @context.console_argument("pane", help=_("pane to be shown"))
        @context.console_command(
            "show",
            input_type="panes",
            help=_("show the pane"),
            all_arguments_required=True,
        )
        def show_pane(command, _, channel, pane=None, **kwargs):
            _pane = context.lookup("pane", pane)
            if _pane is None:
                channel(_("Pane not found."))
                return
            _pane.Show()
            self._mgr.Update()

        @context.console_command(
            "toggleui",
            input_type="panes",
            help=_("Hides/Restores all the visible panes (except scen)"),
        )
        def toggle_ui(command, _, channel, pane=None, **kwargs):
            # Toggle visibility of all UI-elements
            self.ui_visible = not self.ui_visible

            if self.ui_visible:
                for pane_name in self.hidden_panes:
                    pane = self._mgr.GetPane(pane_name)
                    pane.Show()
                self._mgr.Update()
                channel(_("Panes restored."))
            else:
                self.hidden_panes = []
                for pane in self._mgr.GetAllPanes():
                    if pane.IsShown():
                        if pane.name == "scene":
                            # Scene remains
                            pass
                        else:
                            self.hidden_panes.append(pane.name)
                            pane.Hide()
                self._mgr.Update()
                channel(_("Panes hidden."))

        @context.console_argument("pane", help=_("pane to be hidden"))
        @context.console_command(
            "hide",
            input_type="panes",
            help=_("show the pane"),
            all_arguments_required=True,
        )
        def hide_pane(command, _, channel, pane=None, **kwargs):
            _pane = context.lookup("pane", pane)
            if _pane is None:
                channel(_("Pane not found."))
                return
            _pane.Hide()
            self._mgr.Update()

        @context.console_option("always", "a", type=bool, action="store_true")
        @context.console_argument("pane", help=_("pane to be shown"))
        @context.console_command(
            "float",
            input_type="panes",
            help=_("show the pane"),
            all_arguments_required=True,
        )
        def float_pane(command, _, channel, always=False, pane=None, **kwargs):
            _pane = context.lookup("pane", pane)
            if _pane is None:
                channel(_("Pane not found."))
                return
            _pane.Float()
            _pane.Show()
            _pane.Dockable(not always)
            self._mgr.Update()

        @context.console_command(
            "reset",
            input_type="panes",
            help=_("reset all panes restoring the default perspective"),
        )
        def reset_pane(command, _, channel, **kwargs):
            self.on_pane_reset(None)

        @context.console_command(
            "lock",
            input_type="panes",
            help=_("lock the panes"),
        )
        def lock_pane(command, _, channel, **kwargs):
            self.on_pane_lock(None, lock=True)

        @context.console_command(
            "unlock",
            input_type="panes",
            help=_("unlock the panes"),
        )
        def unlock_pane(command, _, channel, **kwargs):
            self.on_pane_lock(None, lock=False)

        @context.console_argument("pane", help=_("pane to create"))
        @context.console_command(
            "create",
            input_type="panes",
            help=_("create a floating about pane"),
        )
        def create_pane(command, _, channel, pane=None, **kwargs):
            if pane == "about":
                from .about import AboutPanel as CreatePanel

                caption = _("About")
                width = 646
                height = 519
            elif pane == "preferences":
                from .preferences import PreferencesPanel as CreatePanel

                caption = _("Preferences")
                width = 565
                height = 327
            else:
                channel(_("Pane not found."))
                return
            panel = CreatePanel(self, context=context)
            _pane = (
                aui.AuiPaneInfo()
                .Dockable(False)
                .Float()
                .Caption(caption)
                .FloatingSize(width, height)
                .Name(pane)
                .CaptionVisible(True)
            )
            _pane.control = panel
            self.on_pane_add(_pane)
            if hasattr(panel, "pane_show"):
                panel.pane_show()
            self.context.register("pane/about", _pane)
            self._mgr.Update()

    def on_pane_reset(self, event=None):
        self.on_panes_closed()
        self._mgr.LoadPerspective(self.default_perspective, update=True)
        self.on_config_panes()

    def on_panes_closed(self):
        for pane in self._mgr.GetAllPanes():
            if pane.IsShown():
                window = pane.window
                if hasattr(window, "pane_hide"):
                    window.pane_hide()
                if isinstance(window, wx.aui.AuiNotebook):
                    for i in range(window.GetPageCount()):
                        page = window.GetPage(i)
                        if hasattr(page, "pane_hide"):
                            page.pane_hide()

    def on_panes_opened(self):
        for pane in self._mgr.GetAllPanes():
            window = pane.window
            if pane.IsShown():
                if hasattr(window, "pane_show"):
                    window.pane_show()
                if isinstance(window, wx.aui.AuiNotebook):
                    for i in range(window.GetPageCount()):
                        page = window.GetPage(i)
                        if hasattr(page, "pane_show"):
                            page.pane_show()
            else:
                if hasattr(window, "pane_noshow"):
                    window.pane_noshow()
                if isinstance(window, wx.aui.AuiNotebook):
                    for i in range(window.GetPageCount()):
                        page = window.GetPage(i)
                        if hasattr(page, "pane_noshow"):
                            page.pane_noshow()

    def on_config_panes(self):
        self.on_panes_opened()
        self.on_pane_lock(lock=self.context.pane_lock)
        wx.CallAfter(self.on_pane_changed, None)

    def on_pane_lock(self, event=None, lock=None):
        if lock is None:
            self.context.pane_lock = not self.context.pane_lock
        else:
            self.context.pane_lock = lock
        for pane in self._mgr.GetAllPanes():
            if pane.IsShown():
                pane.CaptionVisible(not self.context.pane_lock)
                if hasattr(pane.window, "lock"):
                    pane.window.lock()
        self._mgr.Update()

    def on_pane_add(self, paneinfo: aui.AuiPaneInfo):
        pane = self._mgr.GetPane(paneinfo.name)
        control = paneinfo.control
        if isinstance(control, wx.aui.AuiNotebook):
            for i in range(control.GetPageCount()):
                page = control.GetPage(i)
                self.add_module_delegate(page)
        else:
            self.add_module_delegate(control)
        if len(pane.name):
            if not pane.IsShown():
                pane.Show()
                pane.CaptionVisible(not self.context.pane_lock)
                if hasattr(pane.window, "pane_show"):
                    pane.window.pane_show()
                    wx.CallAfter(self.on_pane_changed, None)
                self._mgr.Update()
            return
        self._mgr.AddPane(
            control,
            paneinfo,
        )

    def on_pane_active(self, event):
        pane = event.GetPane()
        if hasattr(pane.window, "active"):
            pane.window.active()

    def on_pane_closed(self, event):
        pane = event.GetPane()
        if pane.IsShown():
            if hasattr(pane.window, "pane_hide"):
                pane.window.pane_hide()
        wx.CallAfter(self.on_pane_changed, None)

    def on_pane_changed(self, *args):
        for pane in self._mgr.GetAllPanes():
            try:
                shown = pane.IsShown()
                check = pane.window.check
                check(shown)
            except AttributeError:
                pass

    @property
    def is_dark(self):
        return wx.SystemSettings().GetColour(wx.SYS_COLOUR_WINDOW)[0] < 127

    def __kernel_initialize(self):
        context = self.context
        context.setting(int, "draw_mode", 0)
        context.setting(bool, "print_shutdown", False)

        @context.console_command(
            "theme", help=_("Theming information and assignments"), hidden=True
        )
        def theme(command, channel, _, **kwargs):
            channel(str(wx.SystemSettings().GetColour(wx.SYS_COLOUR_WINDOW)))

        context.setting(str, "file0", None)
        context.setting(str, "file1", None)
        context.setting(str, "file2", None)
        context.setting(str, "file3", None)
        context.setting(str, "file4", None)
        context.setting(str, "file5", None)
        context.setting(str, "file6", None)
        context.setting(str, "file7", None)
        context.setting(str, "file8", None)
        context.setting(str, "file9", None)
        context.setting(str, "file10", None)
        context.setting(str, "file11", None)
        context.setting(str, "file12", None)
        context.setting(str, "file13", None)
        context.setting(str, "file14", None)
        context.setting(str, "file15", None)
        context.setting(str, "file16", None)
        context.setting(str, "file17", None)
        context.setting(str, "file18", None)
        context.setting(str, "file19", None)
        self.populate_recent_menu()

    @lookup_listener("pane")
    def dynamic_fill_pane_menu(self, new=None, old=None):
        def toggle_pane(pane_toggle):
            def toggle(event=None):
                pane_obj = self._mgr.GetPane(pane_toggle)
                if pane_obj.IsShown():
                    if hasattr(pane_obj.window, "pane_hide"):
                        pane_obj.window.pane_hide()
                    pane_obj.Hide()
                    self._mgr.Update()
                    return
                pane_init = self.context.lookup("pane", pane_toggle)
                self.on_pane_add(pane_init)

            return toggle

        self.panes_menu = wx.Menu()
        label = _("Panes")
        index = self.main_menubar.FindMenu(label)
        if index != -1:
            self.main_menubar.Replace(index, self.panes_menu, label)
        else:
            self.main_menubar.Append(self.panes_menu, label)
        submenus = {}
        for pane, _path, suffix_path in self.context.find("pane/.*"):
            try:
                suppress = pane.hide_menu
                if suppress:
                    continue
            except AttributeError:
                pass
            submenu = None
            try:
                submenu_name = pane.submenu
                if submenu_name in submenus:
                    submenu = submenus[submenu_name]
                elif submenu_name is not None:
                    submenu = wx.Menu()
                    self.panes_menu.AppendSubMenu(submenu, submenu_name)
                    submenus[submenu_name] = submenu
            except AttributeError:
                pass
            menu_context = submenu if submenu is not None else self.panes_menu
            try:
                pane_name = pane.name
            except AttributeError:
                pane_name = suffix_path

            pane_caption = pane_name[0].upper() + pane_name[1:] + "."
            try:
                pane_caption = pane.caption
            except AttributeError:
                pass
            if not pane_caption:
                pane_caption = pane_name[0].upper() + pane_name[1:] + "."

            id_new = wx.NewId()
            menu_item = menu_context.Append(id_new, pane_caption, "", wx.ITEM_CHECK)
            self.Bind(
                wx.EVT_MENU,
                toggle_pane(pane_name),
                id=id_new,
            )
            pane = self._mgr.GetPane(pane_name)
            try:
                menu_item.Check(pane.IsShown())
                pane.window.check = menu_item.Check
            except AttributeError:
                pass

        self.panes_menu.AppendSeparator()
        item = self.main_menubar.lockpane = self.panes_menu.Append(
            ID_MENU_PANE_LOCK, _("Lock Panes"), "", wx.ITEM_CHECK
        )
        item.Check(self.context.pane_lock)
        self.panes_menu.AppendSeparator()
        self.main_menubar.panereset = self.panes_menu.Append(
            ID_MENU_PANE_RESET, _("Reset Panes"), ""
        )

    @lookup_listener("window")
    def dynamic_fill_window_menu(self, new=None, old=None):
        def toggle_window(window):
            def toggle(event=None):
                self.context("window toggle {window}\n".format(window=window))

            return toggle

        label = _("Tools")
        self.window_menu = wx.Menu()
        index = self.main_menubar.FindMenu(label)
        if index != -1:
            self.main_menubar.Replace(index, self.window_menu, label)
        else:
            self.main_menubar.Append(self.window_menu, label)

        submenus = {}
        for window, _path, suffix_path in self.context.find("window/.*"):
            if not window.window_menu(None):
                continue
            submenu = None
            try:
                submenu_name = window.submenu
                if submenu_name in submenus:
                    submenu = submenus[submenu_name]
                elif submenu_name is not None:
                    submenu = wx.Menu()
                    self.window_menu.AppendSubMenu(submenu, submenu_name)
                    submenus[submenu_name] = submenu
            except AttributeError:
                pass
            menu_context = submenu if submenu is not None else self.window_menu
            try:
                name = window.name
            except AttributeError:
                name = suffix_path

            try:
                caption = window.caption
            except AttributeError:
                caption = name[0].upper() + name[1:]
            if name in ("Scene", "About"):  # make no sense, so we omit these...
                continue
            # print ("Menu - Name: %s, Caption=%s" % (name, caption))
            id_new = wx.NewId()
            menu_context.Append(id_new, caption, "", wx.ITEM_NORMAL)
            self.Bind(
                wx.EVT_MENU,
                toggle_window(suffix_path),
                id=id_new,
            )

        self.window_menu.AppendSeparator()
        # If the Main-window has disappeared out of sight (i.e. on a multi-monitor environment)
        # then resetting windows becomes difficult, so a shortcut is in order...
        # REVISED: CTRL-W is needed for mac close-window
        self.window_menu.windowreset = self.window_menu.Append(
            ID_MENU_WINDOW_RESET, _("Reset Windows"), ""
        )
        self.Bind(
            wx.EVT_MENU,
            lambda v: self.context("window reset *\n"),
            id=ID_MENU_WINDOW_RESET,
        )

    def __set_menubars(self):
        self.__set_file_menu()
        self.__set_view_menu()
        self.__set_pane_menu()
        self.__set_tool_menu()
        self.__set_window_menu()
        self.__set_help_menu()
        self.__set_menu_binds()
        self.add_language_menu()
        self.__set_draw_modes()

    def __set_file_menu(self):
        self.file_menu = wx.Menu()
        # ==========
        # FILE MENU
        # ==========

        self.file_menu.Append(
            wx.ID_NEW, _("&New\tCtrl-N"), _("Clear Operations, Elements and Notes")
        )
        self.file_menu.Append(
            wx.ID_OPEN,
            _("&Open Project\tCtrl-O"),
            _("Clear existing elements and notes and open a new file"),
        )
        self.recent_file_menu = wx.Menu()
        if not getattr(sys, "frozen", False) or platform.system() != "Darwin":
            self.file_menu.AppendSubMenu(self.recent_file_menu, _("&Recent"))
        self.file_menu.Append(
            ID_MENU_IMPORT,
            _("&Import File"),
            _("Import another file into the same project"),
        )
        self.file_menu.AppendSeparator()
        self.file_menu.Append(
            wx.ID_SAVE,
            _("&Save\tCtrl-S"),
            _("Save the project as an SVG file (overwriting any existing file)"),
        )
        self.file_menu.Append(
            wx.ID_SAVEAS,
            _("Save &As\tCtrl-Shift-S"),
            _("Save the project in a new SVG file"),
        )
        self.file_menu.AppendSeparator()
        if platform.system() == "Darwin":
            self.file_menu.Append(
                wx.ID_CLOSE, _("&Close Window\tCtrl-W"), _("Close Meerk40t")
            )
        self.file_menu.Append(wx.ID_EXIT, _("E&xit"), _("Close Meerk40t"))
        self.main_menubar.Append(self.file_menu, _("File"))

    def __set_view_menu(self):
        # ==========
        # VIEW MENU
        # ==========
        self.view_menu = wx.Menu()

        self.view_menu.Append(
            ID_MENU_ZOOM_OUT, _("Zoom &Out\tCtrl--"), _("Make the scene smaller")
        )
        self.view_menu.Append(
            ID_MENU_ZOOM_IN, _("Zoom &In\tCtrl-+"), _("Make the scene larger")
        )
        self.view_menu.Append(
            ID_MENU_ZOOM_SIZE,
            _("Zoom to &Selected\tCtrl-Shift-B"),
            _("Fill the scene area with the selected elements"),
        )
        self.view_menu.Append(
            ID_MENU_ZOOM_BED, _("Zoom to &Bed\tCtrl-B"), _("View the whole laser bed")
        )
        self.view_menu.Append(
            ID_MENU_SCENE_MINMAX,
            _("Show/Hide UI-Panels\tCtrl-U"),
            _("Show/Hide all panels/ribbon bar"),
        )

        self.view_menu.AppendSeparator()

        self.view_menu.Append(
            ID_MENU_HIDE_GRID,
            _("Hide Grid"),
            _("Don't show the sizing grid"),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_HIDE_BACKGROUND,
            _("Hide Background"),
            _("Don't show any background image"),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_HIDE_GUIDES,
            _("Hide Guides"),
            _("Don't show the measurement guides"),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_HIDE_PATH,
            _("Hide Shapes"),
            _("Don't show shapes (i.e. Rectangles, Paths etc.)"),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_HIDE_STROKES,
            _("Hide Strokes"),
            _("Don't show the strokes (i.e. the edges of SVG shapes)"),
            wx.ITEM_CHECK,
        )
        # TODO - this function doesn't work.
        self.view_menu.Append(
            ID_MENU_HIDE_LINEWIDTH,
            _("No Stroke-Width Render"),
            _("Ignore the stroke width when drawing the stroke"),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_HIDE_FILLS,
            _("Hide Fills"),
            _("Don't show fills (i.e. the fill inside strokes)"),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_HIDE_IMAGE, _("Hide Images"), _("Don't show images"), wx.ITEM_CHECK
        )
        self.view_menu.Append(
            ID_MENU_HIDE_TEXT,
            _("Hide Text"),
            _("Don't show text elements"),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_HIDE_LASERPATH,
            _("Hide Laserpath"),
            _("Don't show the path that the laserhead has followed (blue line)"),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_HIDE_RETICLE,
            _("Hide Reticle"),
            _(
                "Don't show the small read circle showing the current laserhead position"
            ),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_HIDE_SELECTION,
            _("Hide Selection"),
            _("Don't show the selection boundaries and dimensions"),
            wx.ITEM_CHECK,
        )
        # TODO This menu does not clear existing icons or create icons when it is changed
        self.view_menu.Append(ID_MENU_HIDE_ICONS, _("Hide Icons"), "", wx.ITEM_CHECK)
        self.view_menu.Append(
            ID_MENU_PREVENT_CACHING, _("Do Not Cache Image"), "", wx.ITEM_CHECK
        )
        self.view_menu.Append(
            ID_MENU_PREVENT_ALPHABLACK,
            _("Do Not Alpha/Black Images"),
            "",
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_SCREEN_REFRESH, _("Do Not Refresh"), _(""), wx.ITEM_CHECK
        )
        self.view_menu.Append(
            ID_MENU_SCREEN_ANIMATE, _("Do Not Animate"), _(""), wx.ITEM_CHECK
        )
        self.view_menu.Append(
            ID_MENU_SCREEN_INVERT,
            _("Invert"),
            _("Show a negative image of the scene by inverting colours"),
            wx.ITEM_CHECK,
        )
        self.view_menu.Append(
            ID_MENU_SCREEN_FLIPXY,
            _("Flip XY"),
            _("Effectively rotate the scene display by 180 degrees"),
            wx.ITEM_CHECK,
        )

        self.view_menu.AppendSeparator()
        self.view_menu.Append(
            ID_MENU_SHOW_VARIABLES,
            _("Show Variables"),
            _("Replace variables in textboxes by their 'real' content"),
            wx.ITEM_CHECK,
        )

        self.main_menubar.Append(self.view_menu, _("View"))

    def __set_pane_menu(self):
        # ==========
        # PANE MENU
        # ==========
        self.dynamic_fill_pane_menu()

    def __set_tool_menu(self):
        # ==========
        # TOOL MENU
        # ==========

        self.dynamic_fill_window_menu()

    def __set_window_menu(self):
        # ==========
        # OSX-ONLY WINDOW MENU
        # ==========
        if platform.system() == "Darwin":
            wt_menu = wx.Menu()
            self.main_menubar.Append(wt_menu, _("Window"))

    def __set_help_menu(self):
        # ==========
        # HELP MENU
        # ==========
        self.help_menu = wx.Menu()

        def launch_help_osx(event=None):
            _resource_path = "help/meerk40t.help"
            if not os.path.exists(_resource_path):
                try:  # pyinstaller internal location
                    # pylint: disable=no-member
                    _resource_path = os.path.join(sys._MEIPASS, "help/meerk40t.help")
                except Exception:
                    pass
            if not os.path.exists(_resource_path):
                try:  # Mac py2app resource
                    _resource_path = os.path.join(
                        os.environ["RESOURCEPATH"], "help/meerk40t.help"
                    )
                except Exception:
                    pass
            if os.path.exists(_resource_path):
                os.system("open %s" % _resource_path)
            else:
                dlg = wx.MessageDialog(
                    None,
                    _('Offline help file ("%s") was not found.') % _resource_path,
                    _("File Not Found"),
                    wx.OK | wx.ICON_WARNING,
                )
                dlg.ShowModal()
                dlg.Destroy()

        if platform.system() == "Darwin":
            self.help_menu.Append(
                wx.ID_HELP, _("&MeerK40t Help"), _("Open the MeerK40t Mac help file")
            )
            self.Bind(wx.EVT_MENU, launch_help_osx, id=wx.ID_HELP)
            ONLINE_HELP = wx.NewId()
            self.help_menu.Append(
                ONLINE_HELP, _("&Online Help"), _("Open the Meerk40t online wiki")
            )
            self.Bind(
                wx.EVT_MENU, lambda e: self.context("webhelp help\n"), id=ONLINE_HELP
            )
        else:
            self.help_menu.Append(
                wx.ID_HELP,
                _("&Help"),
                _("Open the Meerk40t online wiki Beginners page"),
            )
            self.Bind(
                wx.EVT_MENU, lambda e: self.context("webhelp help\n"), id=wx.ID_HELP
            )

        self.help_menu.Append(
            ID_BEGINNERS,
            _("&Beginners' Help"),
            _("Open the Meerk40t online wiki Beginners page"),
        )
        self.help_menu.Append(
            ID_HOMEPAGE, _("&Github"), _("Visit Meerk40t's Github home page")
        )
        self.help_menu.Append(
            ID_RELEASES,
            _("&Releases"),
            _("Check for a new release on Meerk40t's Github releases page"),
        )
        self.help_menu.Append(
            ID_FACEBOOK,
            _("&Facebook"),
            _("Get help from the K40 Meerk40t Facebook group"),
        )
        self.help_menu.Append(
            ID_DISCORD,
            _("&Discord"),
            _("Chat with developers to get help on the Meerk40t Discord server"),
        )
        self.help_menu.Append(
            ID_MAKERS_FORUM,
            _("&Makers Forum"),
            _("Get help from the Meerk40t page on the Makers Forum"),
        )
        self.help_menu.Append(
            ID_IRC,
            _("&IRC"),
            _("Chat with developers to get help on the Meerk40t IRC channel"),
        )
        self.help_menu.AppendSeparator()
        self.help_menu.Append(
            wx.ID_ABOUT,
            _("&About MeerK40t"),
            _(
                "Toggle the About window acknowledging those who contributed to creating Meerk40t"
            ),
        )

        self.main_menubar.Append(self.help_menu, _("Help"))

        self.SetMenuBar(self.main_menubar)

    def __set_menu_binds(self):
        self.__set_file_menu_binds()
        self.__set_view_menu_binds()
        self.__set_panes_menu_binds()
        self.__set_help_menu_binds()

    def __set_file_menu_binds(self):
        # ==========
        # BINDS
        # ==========
        self.Bind(wx.EVT_MENU, self.on_click_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_click_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_click_import, id=ID_MENU_IMPORT)
        self.Bind(wx.EVT_MENU, self.on_click_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_click_save_as, id=wx.ID_SAVEAS)

        self.Bind(wx.EVT_MENU, self.on_click_close, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_MENU, self.on_click_exit, id=wx.ID_EXIT)

    def __set_view_menu_binds(self):
        self.Bind(wx.EVT_MENU, self.on_click_zoom_out, id=ID_MENU_ZOOM_OUT)
        self.Bind(wx.EVT_MENU, self.on_click_zoom_in, id=ID_MENU_ZOOM_IN)
        self.Bind(wx.EVT_MENU, self.on_click_zoom_selected, id=ID_MENU_ZOOM_SIZE)
        self.Bind(wx.EVT_MENU, self.on_click_zoom_bed, id=ID_MENU_ZOOM_BED)
        self.Bind(wx.EVT_MENU, self.on_click_toggle_ui, id=ID_MENU_SCENE_MINMAX)

        self.Bind(
            wx.EVT_MENU, self.toggle_draw_mode(DRAW_MODE_GRID), id=ID_MENU_HIDE_GRID
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_BACKGROUND),
            id=ID_MENU_HIDE_BACKGROUND,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_LINEWIDTH),
            id=ID_MENU_HIDE_LINEWIDTH,
        )
        self.Bind(
            wx.EVT_MENU, self.toggle_draw_mode(DRAW_MODE_GUIDES), id=ID_MENU_HIDE_GUIDES
        )
        self.Bind(
            wx.EVT_MENU, self.toggle_draw_mode(DRAW_MODE_PATH), id=ID_MENU_HIDE_PATH
        )
        self.Bind(
            wx.EVT_MENU, self.toggle_draw_mode(DRAW_MODE_IMAGE), id=ID_MENU_HIDE_IMAGE
        )
        self.Bind(
            wx.EVT_MENU, self.toggle_draw_mode(DRAW_MODE_TEXT), id=ID_MENU_HIDE_TEXT
        )
        self.Bind(
            wx.EVT_MENU, self.toggle_draw_mode(DRAW_MODE_FILLS), id=ID_MENU_HIDE_FILLS
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_LASERPATH),
            id=ID_MENU_HIDE_LASERPATH,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_RETICLE),
            id=ID_MENU_HIDE_RETICLE,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_SELECTION),
            id=ID_MENU_HIDE_SELECTION,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_STROKES),
            id=ID_MENU_HIDE_STROKES,
        )
        self.Bind(
            wx.EVT_MENU, self.toggle_draw_mode(DRAW_MODE_ICONS), id=ID_MENU_HIDE_ICONS
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_CACHE),
            id=ID_MENU_PREVENT_CACHING,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_ALPHABLACK),
            id=ID_MENU_PREVENT_ALPHABLACK,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_REFRESH),
            id=ID_MENU_SCREEN_REFRESH,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_ANIMATE),
            id=ID_MENU_SCREEN_ANIMATE,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_INVERT),
            id=ID_MENU_SCREEN_INVERT,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_FLIPXY),
            id=ID_MENU_SCREEN_FLIPXY,
        )
        self.Bind(
            wx.EVT_MENU,
            self.toggle_draw_mode(DRAW_MODE_VARIABLES),
            id=ID_MENU_SHOW_VARIABLES,
        )

    def __set_panes_menu_binds(self):
        self.Bind(
            wx.EVT_MENU,
            self.on_pane_reset,
            id=ID_MENU_PANE_RESET,
        )
        self.Bind(
            wx.EVT_MENU,
            self.on_pane_lock,
            id=ID_MENU_PANE_LOCK,
        )

    def __set_help_menu_binds(self):
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.context("webhelp beginners\n"),
            id=ID_BEGINNERS,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.context("webhelp main\n"),
            id=ID_HOMEPAGE,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.context("webhelp releases\n"),
            id=ID_RELEASES,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.context("webhelp makers\n"),
            id=ID_MAKERS_FORUM,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.context("webhelp facebook\n"),
            id=ID_FACEBOOK,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.context("webhelp discord\n"),
            id=ID_DISCORD,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.context("webhelp irc\n"),
            id=ID_IRC,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda v: self.context("window toggle About\n"),
            id=wx.ID_ABOUT,
        )

    def __set_draw_modes(self):
        self.context.setting(int, "draw_mode", 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_FILLS)
        m.Check(self.context.draw_mode & DRAW_MODE_FILLS != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_GUIDES)
        m.Check(self.context.draw_mode & DRAW_MODE_GUIDES != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_BACKGROUND)
        m.Check(self.context.draw_mode & DRAW_MODE_BACKGROUND != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_LINEWIDTH)
        m.Check(self.context.draw_mode & DRAW_MODE_LINEWIDTH != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_GRID)
        m.Check(self.context.draw_mode & DRAW_MODE_GRID != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_LASERPATH)
        m.Check(self.context.draw_mode & DRAW_MODE_LASERPATH != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_RETICLE)
        m.Check(self.context.draw_mode & DRAW_MODE_RETICLE != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_SELECTION)
        m.Check(self.context.draw_mode & DRAW_MODE_SELECTION != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_STROKES)
        m.Check(self.context.draw_mode & DRAW_MODE_STROKES != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_ICONS)
        m.Check(self.context.draw_mode & DRAW_MODE_ICONS != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_PREVENT_CACHING)
        m.Check(self.context.draw_mode & DRAW_MODE_CACHE != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_PREVENT_ALPHABLACK)
        m.Check(self.context.draw_mode & DRAW_MODE_ALPHABLACK != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_SCREEN_REFRESH)
        m.Check(self.context.draw_mode & DRAW_MODE_REFRESH != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_SCREEN_ANIMATE)
        m.Check(self.context.draw_mode & DRAW_MODE_ANIMATE != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_PATH)
        m.Check(self.context.draw_mode & DRAW_MODE_PATH != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_IMAGE)
        m.Check(self.context.draw_mode & DRAW_MODE_IMAGE != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_HIDE_TEXT)
        m.Check(self.context.draw_mode & DRAW_MODE_TEXT != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_SCREEN_FLIPXY)
        m.Check(self.context.draw_mode & DRAW_MODE_FLIPXY != 0)
        m = self.GetMenuBar().FindItemById(ID_MENU_SCREEN_INVERT)
        m.Check(self.context.draw_mode & DRAW_MODE_INVERT != 0)

    def add_language_menu(self):
        tl = wx.FileTranslationsLoader()
        trans = tl.GetAvailableTranslations("meerk40t")

        if trans:
            wxglade_tmp_menu = wx.Menu()
            i = 0
            for lang in self.context.app.supported_languages:
                language_code, language_name, language_index = lang
                m = wxglade_tmp_menu.Append(
                    wx.ID_ANY, language_name, language_name, wx.ITEM_RADIO
                )
                if i == self.context.language:
                    m.Check(True)

                def language_update(q):
                    return lambda e: self.context.app.update_language(q)

                self.Bind(wx.EVT_MENU, language_update(i), id=m.GetId())
                if language_code not in trans and i != 0:
                    m.Enable(False)
                i += 1
            self.main_menubar.Append(wxglade_tmp_menu, _("Languages"))

    @signal_listener("device;renamed")
    @lookup_listener("service/device/active")
    def on_active_change(self, *args):
        self.__set_titlebar()

    def window_close_veto(self):
        if self.usb_running:
            message = _("The device is actively sending data. Really quit?")
            answer = wx.MessageBox(
                message, _("Currently Sending Data..."), wx.YES_NO | wx.CANCEL, None
            )
            if answer != wx.YES:
                return True  # VETO
        if self.needs_saving:
            message = _(
                "Save changes to project before closing?\n\n"
                "Your changes will be lost if you do not save them."
            )
            answer = wx.MessageBox(
                message, _("Save Project..."), wx.YES_NO | wx.CANCEL, None
            )
            if answer == wx.YES:
                self.context("dialog_save\n")
            if answer == wx.CANCEL:
                return True  # VETO
        return False

    def window_close(self):
        context = self.context

        context.perspective = self._mgr.SavePerspective()
        self.on_panes_closed()
        self._mgr.UnInit()

        if context.print_shutdown:
            context.channel("shutdown").watch(print)
        self.context(".timer 0 1 quit\n")

    @signal_listener("altered")
    @signal_listener("modified")
    def on_invalidate_save(self, origin, *args):
        self.needs_saving = True
        app = self.context.app.GetTopWindow()
        if isinstance(app, wx.TopLevelWindow):
            app.OSXSetModified(self.needs_saving)

    def validate_save(self):
        self.needs_saving = False
        app = self.context.app.GetTopWindow()
        if isinstance(app, wx.TopLevelWindow):
            app.OSXSetModified(self.needs_saving)

    @signal_listener("warning")
    def on_warning_signal(self, origin, message, caption, style):
        if style is None:
            style = wx.OK | wx.ICON_WARNING
        dlg = wx.MessageDialog(
            None,
            message,
            caption,
            style,
        )
        dlg.ShowModal()
        dlg.Destroy()

    @signal_listener("device;noactive")
    def on_device_noactive(self, origin, value):
        dlg = wx.MessageDialog(
            None,
            _("No active device existed. Add a primary device."),
            _("Active Device"),
            wx.OK | wx.ICON_WARNING,
        )
        dlg.ShowModal()
        dlg.Destroy()

    @signal_listener("pipe;failing")
    def on_usb_error(self, origin, value):
        if value == 5:
            self.context.signal("controller", origin)
            dlg = wx.MessageDialog(
                None,
                _("All attempts to connect to USB have failed."),
                _("Usb Connection Problem."),
                wx.OK | wx.ICON_WARNING,
            )
            dlg.ShowModal()
            dlg.Destroy()

    @signal_listener("cutplanning;failed")
    def on_usb_error(self, origin, error):
        dlg = wx.MessageDialog(
            None,
            _("Cut planning failed because: {error}".format(error=error)),
            _("Cut Planning Failed"),
            wx.OK | wx.ICON_WARNING,
        )
        dlg.ShowModal()
        dlg.Destroy()

    @signal_listener("pipe;running")
    def on_usb_running(self, origin, value):
        self.usb_running = value

    @signal_listener("pipe;usb_status")
    def on_usb_state_text(self, origin, value):
        self.main_statusbar.SetStatusText(
            _("Usb: %s") % value,
            1,
        )

    @signal_listener("pipe;thread")
    def on_pipe_state(self, origin, state):
        if state == self.pipe_state:
            return
        self.pipe_state = state

        self.main_statusbar.SetStatusText(
            _("Controller: %s") % self.context.kernel.get_text_thread_state(state),
            2,
        )

    @signal_listener("spooler;thread")
    def on_spooler_state(self, origin, value):
        self.main_statusbar.SetStatusText(
            _("Spooler: %s") % self.context.get_text_thread_state(value),
            3,
        )

    @signal_listener("export-image")
    def on_export_signal(self, origin, frame):
        image_width, image_height, frame = frame
        if frame is not None:
            elements = self.context.elements
            img = Image.fromarray(frame)
            node = elements.elem_branch.add(
                image=img, width=image_width, height=image_height, type="elem image"
            )
            elements.classify([node])

    @signal_listener("statusmsg")
    def on_update_statusmsg(self, origin, value):
        self.main_statusbar.SetStatusText(value, 0)


    def __set_titlebar(self):
        device_name = ""
        device_version = ""
        title = _("%s v%s") % (
            str(self.context.kernel.name),
            self.context.kernel.version,
        )
        title += "      %s" % self.context.device.label
        self.SetTitle(title)

    def __set_properties(self):
        # begin wxGlade: MeerK40t.__set_properties
        self.__set_titlebar()
        _icon = wx.NullIcon
        _icon.CopyFromBitmap(icon_meerk40t.GetBitmap())
        self.SetIcon(_icon)

    def load_or_open(self, filename):
        """
        Loads recent file name given. If the filename cannot be opened attempts open dialog at last known location.
        """
        if os.path.exists(filename):
            try:
                self.load(filename)
            except PermissionError:
                self.tryopen(filename)
        else:
            self.tryopen(filename)

    def tryopen(self, filename):
        """
        Loads an open dialog at given filename to load data.
        """
        files = self.context.elements.load_types()
        default_file = os.path.basename(filename)
        default_dir = os.path.dirname(filename)

        with wx.FileDialog(
            self,
            _("Open"),
            defaultDir=default_dir,
            defaultFile=default_file,
            wildcard=files,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            fileDialog.SetFilename(default_file)
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind
            pathname = fileDialog.GetPath()
            self.load(pathname)

    def populate_recent_menu(self):
        if not hasattr(self, "recent_file_menu"):
            return  # No menu, cannot populate.

        context = self.context
        recents = [
            (context.file0, ID_MENU_FILE0, "&1 "),
            (context.file1, ID_MENU_FILE1, "&2 "),
            (context.file2, ID_MENU_FILE2, "&3 "),
            (context.file3, ID_MENU_FILE3, "&4 "),
            (context.file4, ID_MENU_FILE4, "&5 "),
            (context.file5, ID_MENU_FILE5, "&6 "),
            (context.file6, ID_MENU_FILE6, "&7 "),
            (context.file7, ID_MENU_FILE7, "&8 "),
            (context.file8, ID_MENU_FILE8, "&9 "),
            (context.file9, ID_MENU_FILE9, "1&0"),
            (context.file10, ID_MENU_FILE10, "11"),
            (context.file11, ID_MENU_FILE11, "12"),
            (context.file12, ID_MENU_FILE12, "13"),
            (context.file13, ID_MENU_FILE13, "14"),
            (context.file14, ID_MENU_FILE14, "15"),
            (context.file15, ID_MENU_FILE15, "16"),
            (context.file16, ID_MENU_FILE16, "17"),
            (context.file17, ID_MENU_FILE17, "18"),
            (context.file18, ID_MENU_FILE18, "19"),
            (context.file19, ID_MENU_FILE19, "20"),
        ]

        # for i in range(self.recent_file_menu.MenuItemCount):
        # self.recent_file_menu.Remove(self.recent_file_menu.FindItemByPosition(0))

        for item in self.recent_file_menu.GetMenuItems():
            self.recent_file_menu.Remove(item)

        for file, id, shortcode in recents:
            if file is not None and file:
                shortfile = _("Load {file}...").format(file=os.path.basename(file))
                self.recent_file_menu.Append(
                    id, shortcode + "  " + file.replace("&", "&&"), shortfile
                )
                self.Bind(
                    wx.EVT_MENU,
                    partial(lambda f, event: self.load_or_open(f), file),
                    id=id,
                )

        if self.recent_file_menu.MenuItemCount != 0:
            self.recent_file_menu.AppendSeparator()
            self.recent_file_menu.Append(
                ID_MENU_FILE_CLEAR,
                _("Clear Recent"),
                _("Delete the list of recent projects"),
            )
            self.Bind(wx.EVT_MENU, lambda e: self.clear_recent(), id=ID_MENU_FILE_CLEAR)

    def clear_recent(self):
        for i in range(20):
            try:
                setattr(self.context, "file" + str(i), "")
            except IndexError:
                break
        self.populate_recent_menu()

    def set_file_as_recently_used(self, pathname):
        recent = list()
        for i in range(20):
            recent.append(getattr(self.context, "file" + str(i)))
        recent = [r for r in recent if r is not None and r != pathname and len(r) > 0]
        recent.insert(0, pathname)
        for i in range(20):
            try:
                setattr(self.context, "file" + str(i), recent[i])
            except IndexError:
                break
        self.populate_recent_menu()

    def clear_project(self):
        context = self.context
        self.working_file = None
        self.validate_save()
        context.elements.clear_all()
        self.context(".laserpath_clear\n")

    def clear_and_open(self, pathname):
        self.clear_project()
        if self.load(pathname):
            try:
                if self.context.uniform_svg and pathname.lower().endswith("svg"):
                    # or (len(elements) > 0 and "meerK40t" in elements[0].values):
                    # TODO: Disabled uniform_svg, no longer detecting namespace.
                    self.working_file = pathname
                    self.validate_save()
            except AttributeError:
                pass

    def load(self, pathname):
        try:
            try:
                # Reset to standard tool
                self.context("tool none\n")
                self.context.signal("freeze_tree", True)
                # wxPython 4.1.+
                with wx.BusyInfo(
                    wx.BusyInfoFlags().Title(_("Loading File...")).Label(pathname)
                ):
                    n = self.context.elements.note
                    results = self.context.elements.load(
                        pathname,
                        channel=self.context.channel("load"),
                        svg_ppi=self.context.elements.svg_ppi,
                    )
                self.context.signal("freeze_tree", False)
            except AttributeError:
                # wxPython 4.0
                self.context.signal("freeze_tree", True)
                with wx.BusyInfo(_("Loading File...")):
                    n = self.context.elements.note
                    results = self.context.elements.load(
                        pathname,
                        channel=self.context.channel("load"),
                        svg_ppi=self.context.elements.svg_ppi,
                    )
                self.context.signal("freeze_tree", False)
        except BadFileError as e:
            dlg = wx.MessageDialog(
                None,
                str(e),
                _("File is Malformed"),
                wx.OK | wx.ICON_WARNING,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False
        else:
            if results:
                self.context("scene focus -{zoom}% -{zoom}% {zoom100}% {zoom100}%\n".format(zoom=self.context.zoom_level, zoom100=100 + self.context.zoom_level))

                self.set_file_as_recently_used(pathname)
                if n != self.context.elements.note and self.context.elements.auto_note:
                    self.context("window open Notes\n")  # open/not toggle.
                return True
            return False

    def on_drop_file(self, event):
        """
        Drop file handler

        Accepts multiple files drops.
        """
        accepted = 0
        rejected = 0
        rejected_files = []
        for pathname in event.GetFiles():
            if self.load(pathname):
                accepted += 1
            else:
                rejected += 1
                rejected_files.append(pathname)
        if rejected != 0:
            reject = "\n".join(rejected_files)
            err_msg = _("Some files were unrecognized:\n%s") % reject
            dlg = wx.MessageDialog(
                None, err_msg, _("Error encountered"), wx.OK | wx.ICON_ERROR
            )
            dlg.ShowModal()
            dlg.Destroy()

    def on_size(self, event):
        if self.context is None:
            return
        self.Layout()
        if not self.context.disable_auto_zoom:
            self.context("scene focus -{zoom}% -{zoom}% {zoom100}% {zoom100}%\n".format(zoom=self.context.zoom_level, zoom100=100 + self.context.zoom_level))

    def on_focus_lost(self, event):
        self.context("-laser\nend\n")
        # event.Skip()

    def on_click_new(self, event=None):  # wxGlade: MeerK40t.<event_handler>
        self.clear_project()

    def on_click_open(self, event=None):  # wxGlade: MeerK40t.<event_handler>
        self.context(".dialog_load\n")

    def on_click_import(self, event=None):  # wxGlade: MeerK40t.<event_handler>
        self.context(".dialog_import\n")

    def on_click_stop(self, event=None):
        self.context("estop\n")

    def on_click_pause(self, event=None):
        self.context("pause\n")

    def on_click_save(self, event):
        self.context(".dialog_save\n")

    def on_click_save_as(self, event=None):
        self.context(".dialog_save_as\n")

    def on_click_close(self, event=None):
        try:
            window = self.context.app.GetTopWindow().FindFocus().GetTopLevelParent()
            if window is self:
                return
            window.Close(False)
        except RuntimeError:
            pass

    def on_click_exit(self, event=None):  # wxGlade: MeerK40t.<event_handler>
        try:
            self.Close()
        except RuntimeError:
            pass

    def on_click_zoom_out(self, event=None):  # wxGlade: MeerK40t.<event_handler>
        """
        Zoomout button press
        """
        self.context("scene zoom %f\n" % (1.0 / 1.5))

    def on_click_zoom_in(self, event=None):  # wxGlade: MeerK40t.<event_handler>
        """
        Zoomin button press
        """
        self.context("scene zoom %f\n" % 1.5)

    def on_click_zoom_selected(self, event=None):  # wxGlade: MeerK40t.<event_handler>
        """
        Zoom scene to selected items.
        """
        bbox = self.context.elements.selected_area()
        if bbox is None:
            self.on_click_zoom_bed(event=event)
        else:
            zfact = self.context.zoom_level / 100.0

            x_delta = (bbox[2] - bbox[0]) * zfact
            y_delta = (bbox[3] - bbox[1]) * zfact
            x0 = Length(
                amount=bbox[0] - x_delta, relative_length=self.context.device.width
            ).length_mm
            y0 = Length(
                amount=bbox[1] - y_delta, relative_length=self.context.device.height
            ).length_mm
            x1 = Length(
                amount=bbox[2] + x_delta, relative_length=self.context.device.width
            ).length_mm
            y1 = Length(
                amount=bbox[3] + y_delta, relative_length=self.context.device.height
            ).length_mm
            self.context(f"scene focus {x0} {y0} {x1} {y1}\n")

    def on_click_toggle_ui(self, event=None):
        self.context("pane toggleui\n")
        self.context("scene focus -{zoom}% -{zoom}% {zoom100}% {zoom100}%\n".format(zoom=self.context.zoom_level, zoom100=100 + self.context.zoom_level))

    def on_click_zoom_bed(self, event=None):  # wxGlade: MeerK40t.<event_handler>
        """
        Zoom scene to bed size.
        """
        self.context("scene focus -{zoom}% -{zoom}% {zoom100}% {zoom100}%\n".format(zoom=self.context.zoom_level, zoom100=100 + self.context.zoom_level))

    def toggle_draw_mode(self, bits):
        """
        Toggle the draw mode.
        @param bits: Bit to toggle.
        @return: Toggle function.
        """

        def toggle(event=None):
            self.context.draw_mode ^= bits
            self.context.signal("draw_mode", self.context.draw_mode)
            self.context.signal("refresh_scene", "Scene")

        return toggle

    def update_statusbar(self, text):
        self.main_statusbar.SetStatusText(text, 0)

    def status_update(self):
        self.update_statusbar("")

    # The standard wx.Frame version of DoGiveHelp is not passed the help text in Windows
    # (no idea about other platforms - wxWidgets code for each platform is different)
    # and has no way of knowing the menuitem and getting the text itself.

    # So we override the standard wx.Frame version and make it do nothing
    # and capture the EVT_MENU_HIGHLIGHT ourselves to process it.
    def DoGiveHelp(self, text, show):
        """Override wx default DoGiveHelp method

        Because we do not call event.Skip() on EVT_MENU_HIGHLIGHT, this should not be called.
        """
        if self.DoGiveHelp_called:
            return
        if text:
            print("DoGiveHelp called with help text:", text)
        else:
            print("DoGiveHelp called but still no help text")
        self.DoGiveHelp_called = True

    def on_menu_open(self, event):
        self.menus_open += 1
        menu = event.GetMenu()
        if menu:
            title = menu.GetTitle()
            if title:
                self.update_statusbar(title + "...")

    def on_menu_close(self, event):
        self.menus_open -= 1
        if self.menus_open <= 0:
            self.top_menu = None
        self.status_update()

    def on_menu_highlight(self, event):
        menuid = event.GetId()
        menu = event.GetMenu()
        if menuid == wx.ID_SEPARATOR:
            self.update_statusbar("...")
            return
        if not self.top_menu and not menu:
            self.status_update()
            return
        if menu and not self.top_menu:
            self.top_menu = menu
        if self.top_menu and not menu:
            menu = self.top_menu
        menuitem, submenu = menu.FindItem(menuid)
        if not menuitem:
            self.update_statusbar("...")
            return
        helptext = menuitem.GetHelp()
        if not helptext:
            helptext = "{m} ({s})".format(
                m=menuitem.GetItemLabelText(),
                s=_("No help text"),
            )
        self.update_statusbar(helptext)
