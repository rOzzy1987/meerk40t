"""
GUI to manage material library entries.
In essence a material library setting is a persistent list of operations.
They are stored in the operations.cfg file in the meerk40t working directory
"""

import os
import xml.etree.ElementTree as ET

import wx
import wx.lib.mixins.listctrl as listmix

from ..core.node.node import Node
from ..kernel.kernel import get_safe_path
from ..kernel.settings import Settings
from .icons import (
    icon_hatch,
    icon_library,
    icon_points,
    icons8_caret_down,
    icons8_caret_up,
    icons8_console,
    icons8_direction,
    icons8_image,
    icons8_laser_beam,
    icons8_laserbeam_weak,
)
from .mwindow import MWindow
from .wxutils import (
    ScrolledPanel,
    StaticBoxSizer,
    TextCtrl,
    wxCheckBox,
    wxButton,
    dip_size,
)

_ = wx.GetTranslation


class ImportDialog(wx.Dialog):
    def __init__(self, *args, context=None, filename=None, **kwds):
        kwds["style"] = (
            kwds.get("style", 0) | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        wx.Dialog.__init__(self, *args, **kwds)
        self.context = context
        self.txt_filename = wx.TextCtrl(self, wx.ID_ANY)
        self.btn_file = wxButton(self, wx.ID_ANY, "...")
        self.check_consolidate = wxCheckBox(
            self, wx.ID_ANY, _("Consolidate same thickness for material")
        )
        self.check_lens = wxCheckBox(self, wx.ID_ANY, _("Compensate Lens-Sizes"))
        self.txt_lens_old = wx.TextCtrl(self, wx.ID_ANY)
        self.txt_lens_new = wx.TextCtrl(self, wx.ID_ANY)
        self.check_wattage = wxCheckBox(self, wx.ID_ANY, _("Compensate Power-Levels"))
        self.txt_wattage_old = wx.TextCtrl(self, wx.ID_ANY)
        self.txt_wattage_new = wx.TextCtrl(self, wx.ID_ANY)
        self.btn_ok = wxButton(self, wx.ID_OK, _("OK"))
        self.btn_cancel = wxButton(self, wx.ID_CANCEL, _("Cancel"))

        self._define_layout()
        self.validate(None)
        self.on_check(None)
        self.check_consolidate.SetValue(True)
        self._define_logic()
        if filename is not None:
            self.txt_filename.SetValue(filename)

    def _define_layout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        file_sizer = StaticBoxSizer(self, wx.ID_ANY, _("File to import"), wx.VERTICAL)

        file_box = wx.BoxSizer(wx.HORIZONTAL)

        file_box.Add(self.txt_filename, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        file_box.Add(self.btn_file, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        file_sizer.Add(file_box, 0, wx.EXPAND, 0)

        file_sizer.Add(self.check_consolidate, 0, 0, 0)

        main_sizer.Add(file_sizer, 0, wx.EXPAND, 0)

        lens_sizer = StaticBoxSizer(
            self, wx.ID_ANY, _("Different Lens-Size"), wx.VERTICAL
        )

        lens_param_sizer = wx.BoxSizer(wx.HORIZONTAL)
        label_old = wx.StaticText(self, wx.ID_ANY, _("Old:"))
        unit_old = wx.StaticText(self, wx.ID_ANY, "mm")
        label_new = wx.StaticText(self, wx.ID_ANY, _("New:"))
        unit_new = wx.StaticText(self, wx.ID_ANY, "mm")
        lens_param_sizer.Add(label_old, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        lens_param_sizer.Add(self.txt_lens_old, 0, 0, 0)
        lens_param_sizer.Add(unit_old, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        lens_param_sizer.AddSpacer(25)

        lens_param_sizer.Add(label_new, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        lens_param_sizer.Add(self.txt_lens_new, 0, 0, 0)
        lens_param_sizer.Add(unit_new, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        lens_sizer.Add(self.check_lens, 0, 0, 0)
        lens_sizer.Add(lens_param_sizer, 0, 0, 0)
        main_sizer.Add(lens_sizer, 0, wx.EXPAND, 0)

        wattage_sizer = StaticBoxSizer(
            self, wx.ID_ANY, _("Different Laser-Power"), wx.VERTICAL
        )

        wattage_param_sizer = wx.BoxSizer(wx.HORIZONTAL)
        label_old = wx.StaticText(self, wx.ID_ANY, "Old:")
        unit_old = wx.StaticText(self, wx.ID_ANY, "W")
        label_new = wx.StaticText(self, wx.ID_ANY, "New:")
        unit_new = wx.StaticText(self, wx.ID_ANY, "W")
        wattage_param_sizer.Add(label_old, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        wattage_param_sizer.Add(self.txt_wattage_old, 0, 0, 0)
        wattage_param_sizer.Add(unit_old, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        wattage_param_sizer.AddSpacer(25)

        wattage_param_sizer.Add(label_new, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        wattage_param_sizer.Add(self.txt_wattage_new, 0, 0, 0)
        wattage_param_sizer.Add(unit_new, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        wattage_sizer.Add(self.check_wattage, 0, 0, 0)
        wattage_sizer.Add(wattage_param_sizer, 0, 0, 0)
        main_sizer.Add(wattage_sizer, 0, wx.EXPAND, 0)

        box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        box_sizer.Add(self.btn_ok, 0, 0, 0)
        box_sizer.Add(self.btn_cancel, 0, 0, 0)
        main_sizer.Add(box_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        self.SetSizer(main_sizer)
        self.Layout()
        main_sizer.Fit(self)
        self.txt_filename.SetToolTip(
            _("Provide the full filename for material library")
        )
        self.btn_file.SetToolTip(_("Click to select files"))
        self.check_consolidate.SetToolTip(
            _("This will group entries with the same material description together")
        )
        self.check_lens.SetToolTip(
            _(
                "If active, power and speed values will be adjusted,\nto accommodate different lens-sizes"
            )
        )
        self.check_wattage.SetToolTip(
            _(
                "If active, power and speed values will be adjusted,\nto accommodate different laser power"
            )
        )

    def _define_logic(self):
        self.Bind(wx.EVT_TEXT, self.validate, self.txt_filename)
        self.Bind(wx.EVT_BUTTON, self.on_file, self.btn_file)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, self.check_lens)
        self.Bind(wx.EVT_CHECKBOX, self.on_check, self.check_wattage)

    def on_file(self, event):
        mydlg = wx.FileDialog(
            self,
            message=_("Choose a library-file"),
            wildcard="Supported files|*.lib;*.ini;*.clb|EZcad files (*.lib;*.ini)|*.lib;*.ini|Lightburn files (*.clb)|*.clb|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_PREVIEW,
        )
        if mydlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            self.txt_filename.SetValue(mydlg.GetPath())
            self.validate()
        mydlg.Destroy()

    def on_check(self, event):
        flag = self.check_lens.GetValue()
        self.txt_lens_old.Enable(flag)
        self.txt_lens_new.Enable(flag)
        flag = self.check_wattage.GetValue()
        self.txt_wattage_old.Enable(flag)
        self.txt_wattage_new.Enable(flag)

    def validate(self, *args):
        flag = True
        fname = self.txt_filename.GetValue()
        if fname == "" or not os.path.exists(fname):
            flag = False
        if flag and fname.endswith(".clb"):
            self.check_consolidate.Enable(True)
        else:
            self.check_consolidate.Enable(False)

        self.btn_ok.Enable(flag)

    def result(self):
        old_lens = None
        new_lens = None
        factor_from_lens = 1.0
        if self.check_lens.GetValue():
            a_s = self.txt_lens_old.GetValue()
            b_s = self.txt_lens_new.GetValue()
            try:
                a = float(a_s)
                b = float(b_s)
                if a != 0 and b != 0:
                    old_lens = a_s
                    new_lens = b_s
                    factor_from_lens = b / a
            except ValueError:
                pass

        old_power = None
        new_power = None
        factor_from_power = 1.0
        if self.check_wattage.GetValue():
            a_s = self.txt_wattage_old.GetValue()
            b_s = self.txt_wattage_new.GetValue()
            try:
                a = float(a_s)
                b = float(b_s)
                if a != 0 and b != 0:
                    old_power = a_s
                    new_power = b_s
                    factor_from_power = a / b
            except ValueError:
                pass

        fname = self.txt_filename.GetValue()
        if fname == "" or not os.path.exists(fname):
            fname = None

        consolidate = self.check_consolidate.GetValue()
        if not self.check_consolidate.Enabled:
            consolidate = False
        factor = factor_from_lens * factor_from_power
        info = (
            fname,
            old_lens,
            new_lens,
            old_power,
            new_power,
            factor_from_lens,
            factor_from_power,
            factor,
            consolidate,
        )
        return info


class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin):
    """TextEditMixin allows any column to be edited."""

    # ----------------------------------------------------------------------
    def __init__(
        self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0
    ):
        """Constructor"""
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)


class MaterialPanel(ScrolledPanel):
    """
    Panel to modify material library settings.
    In essence a material library setting is a persistent list of operations.
    They are stored in the operations.cfg file in the meerk40t working directory

    Internal development note:
    I have tried the dataview TreeListCtrl to self.display_list the different entries:
    this was crashing consistently, so I stopped following this path
    """

    def __init__(self, *args, context=None, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.TAB_TRAVERSAL
        ScrolledPanel.__init__(self, *args, **kwds)
        self.context = context
        self.op_data = self.context.elements.op_data
        self.SetHelpText("materialmanager")
        self.parent_panel = None
        self.current_item = None
        self._active_material = None
        self._active_operation = None
        self.no_reload = False
        self.share_ready = False

        # Categorisation
        # 0 = Material (thickness), 1 = Lasertype (Material), 2 = Thickness (Material)
        self.categorisation = 0
        # Intentionally not translated, to allow data exchange
        materials = [
            "Plywood",
            "Solid wood",
            "Acrylic",
            "Foam",
            "Leather",
            "Cardboard",
            "Cork",
            "Textiles",
            "Slate",
            "Paper",
            "Aluminium",
            "Steel",
            "Copper",
            "Silver",
            "Gold",
            "Zinc",
            "Metal",
        ]
        # Dictionary with key=Materialname, entry=Description (Name, Lasertype, entries)
        self.material_list = dict()
        self.operation_list = dict()
        self.display_list = list()
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        filter_box = StaticBoxSizer(
            self, wx.ID_ANY, _("Filter Materials"), wx.HORIZONTAL
        )
        label_1 = wx.StaticText(self, wx.ID_ANY, _("Material"))
        filter_box.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.txt_material = wx.ComboBox(
            self, wx.ID_ANY, choices=materials, style=wx.CB_SORT
        )
        # self.txt_material = TextCtrl(self, wx.ID_ANY, "", limited=True)

        filter_box.Add(self.txt_material, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        label_2 = wx.StaticText(self, wx.ID_ANY, _("Thickness"))
        filter_box.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.txt_thickness = TextCtrl(self, wx.ID_ANY, "", limited=True)
        filter_box.Add(self.txt_thickness, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        label_3 = wx.StaticText(self, wx.ID_ANY, _("Laser"))
        filter_box.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.laser_choices = [
            _("<All Lasertypes>"),
        ]
        dev_infos = list(self.context.find("provider/friendly"))
        # Gets a list of tuples (description, key, path)
        dev_infos.sort(key=lambda e: e[0][1])
        for e in dev_infos:
            self.laser_choices.append(e[0][0])

        self.combo_lasertype = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=self.laser_choices,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.combo_lasertype.SetMaxSize(dip_size(self, 110, -1))

        filter_box.Add(self.combo_lasertype, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        self.btn_reset = wxButton(self, wx.ID_ANY, _("Reset Filter"))
        filter_box.Add(self.btn_reset, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        main_sizer.Add(filter_box, 0, wx.EXPAND, 0)
        result_box = StaticBoxSizer(
            self, wx.ID_ANY, _("Matching library entries"), wx.VERTICAL
        )
        self.tree_library = wx.TreeCtrl(
            self,
            wx.ID_ANY,
            style=wx.BORDER_SUNKEN | wx.TR_HAS_BUTTONS
            # | wx.TR_HIDE_ROOT
            | wx.TR_ROW_LINES | wx.TR_SINGLE,
        )
        self.tree_library.SetToolTip(_("Click to select / Right click for actions"))

        self.list_preview = EditableListCtrl(
            self,
            wx.ID_ANY,
            style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES | wx.LC_SINGLE_SEL,
        )
        self.list_preview.AppendColumn(_("#"), format=wx.LIST_FORMAT_LEFT, width=55)
        self.list_preview.AppendColumn(
            _("Operation"),
            format=wx.LIST_FORMAT_LEFT,
            width=60,
        )
        self.list_preview.AppendColumn(_("Id"), format=wx.LIST_FORMAT_LEFT, width=60)
        self.list_preview.AppendColumn(
            _("Label"), format=wx.LIST_FORMAT_LEFT, width=100
        )
        self.list_preview.AppendColumn(_("Power"), format=wx.LIST_FORMAT_LEFT, width=50)
        self.list_preview.AppendColumn(_("Speed"), format=wx.LIST_FORMAT_LEFT, width=50)
        self.list_preview.AppendColumn(
            _("Frequency"), format=wx.LIST_FORMAT_LEFT, width=50
        )
        self.list_preview.SetToolTip(_("Click to select / Right click for actions"))
        self.opinfo = {
            "op cut": ("Cut", icons8_laser_beam, 0),
            "op raster": ("Raster", icons8_direction, 0),
            "op image": ("Image", icons8_image, 0),
            "op engrave": ("Engrave", icons8_laserbeam_weak, 0),
            "op dots": ("Dots", icon_points, 0),
            "op hatch": ("Hatch", icon_hatch, 0),
            "generic": ("Generic", icons8_console, 0),
        }
        self.state_images = wx.ImageList()
        self.state_images.Create(width=25, height=25)
        for key in self.opinfo:
            info = self.opinfo[key]
            image_id = self.state_images.Add(
                bitmap=info[1].GetBitmap(resize=(25, 25), noadjustment=True)
            )
            info = (info[0], info[1], image_id)
            self.opinfo[key] = info

        self.list_preview.AssignImageList(self.state_images, wx.IMAGE_LIST_SMALL)

        param_box = StaticBoxSizer(self, wx.ID_ANY, _("Information"), wx.VERTICAL)

        box1 = wx.BoxSizer(wx.HORIZONTAL)
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box3 = wx.BoxSizer(wx.HORIZONTAL)
        box4 = wx.BoxSizer(wx.HORIZONTAL)
        self.box_minimal = wx.BoxSizer(wx.VERTICAL)
        self.box_extended = wx.BoxSizer(wx.VERTICAL)

        param_box.Add(self.box_minimal, 0, wx.EXPAND, 0)
        param_box.Add(self.box_extended, 0, wx.EXPAND, 0)

        self.box_minimal.Add(box1, 0, wx.EXPAND, 0)
        self.box_minimal.Add(box2, 0, wx.EXPAND, 0)
        self.box_extended.Add(box3, 0, wx.EXPAND, 0)
        self.box_extended.Add(box4, 0, wx.EXPAND, 0)

        def size_it(ctrl, minsize, maxsize):
            ctrl.SetMinSize(dip_size(self, minsize, -1))
            ctrl.SetMaxSize(dip_size(self, maxsize, -1))

        label = wx.StaticText(self, wx.ID_ANY, _("Title"))
        # size_it(label, 60, 100)
        box1.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.txt_entry_title = wx.TextCtrl(self, wx.ID_ANY, "")
        box1.Add(self.txt_entry_title, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        self.btn_set = wxButton(self, wx.ID_ANY, _("Set"))
        self.btn_set.SetToolTip(
            _(
                "Change the name / lasertype of the current entry\nRight-Click: assign lasertype to all visible entries"
            )
        )

        box1.Add(self.btn_set, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.btn_expand = wxButton(
            self,
            wx.ID_ANY,
        )
        self.btn_expand.SetSize(dip_size(self, 25, 25))
        self.btn_expand.SetMinSize(dip_size(self, 25, 25))
        self.btn_expand.SetMaxSize(dip_size(self, 25, 25))
        box1.Add(self.btn_expand, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        label = wx.StaticText(self, wx.ID_ANY, _("Material"))
        size_it(label, 60, 100)
        box2.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        # self.txt_entry_material = wx.TextCtrl(self, wx.ID_ANY, "")
        self.txt_entry_material = wx.ComboBox(
            self, wx.ID_ANY, choices=materials, style=wx.CB_SORT
        )

        box2.Add(self.txt_entry_material, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        label = wx.StaticText(self, wx.ID_ANY, _("Thickness"))
        size_it(label, 60, 100)
        box2.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.txt_entry_thickness = TextCtrl(self, wx.ID_ANY, "", limited=True)
        box2.Add(self.txt_entry_thickness, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        label = wx.StaticText(self, wx.ID_ANY, _("Laser"))
        size_it(label, 60, 100)
        box3.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        choices = self.laser_choices  # [1:]
        self.combo_entry_type = wx.ComboBox(
            self, wx.ID_ANY, choices=choices, style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self.combo_entry_type.SetMaxSize(dip_size(self, 110, -1))

        box3.Add(self.combo_entry_type, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        box3.AddSpacer(20)

        label = wx.StaticText(self, wx.ID_ANY, _("Id"))
        size_it(label, 60, 100)
        box3.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.txt_entry_section = TextCtrl(
            self,
            wx.ID_ANY,
            "",
            limited=True,
            check="empty",
        )
        box3.Add(self.txt_entry_section, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        label = wx.StaticText(self, wx.ID_ANY, _("Power"))
        size_it(label, 60, 100)
        box4.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.txt_entry_power = TextCtrl(
            self,
            wx.ID_ANY,
            "",
            limited=True,
        )
        unit = wx.StaticText(self, wx.ID_ANY, _("W"))
        box4.Add(self.txt_entry_power, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        box4.Add(unit, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        box4.AddSpacer(20)

        label = wx.StaticText(self, wx.ID_ANY, _("Lens-Size"))
        size_it(label, 60, 100)
        box4.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.txt_entry_lens = TextCtrl(
            self,
            wx.ID_ANY,
            "",
            limited=True,
        )
        unit = wx.StaticText(self, wx.ID_ANY, _("mm"))
        box4.Add(self.txt_entry_lens, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        box4.Add(unit, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.txt_entry_note = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.txt_entry_note.SetMinSize(dip_size(self, -1, 2 * 23))
        self.box_extended.Add(self.txt_entry_note, 0, wx.EXPAND, 0)

        result_box.Add(self.tree_library, 1, wx.EXPAND, 0)
        result_box.Add(param_box, 0, wx.EXPAND, 0)
        result_box.Add(self.list_preview, 1, wx.EXPAND, 0)

        self.txt_material.SetToolTip(_("Filter entries with a certain title."))
        self.txt_thickness.SetToolTip(
            _("Filter entries with a certain material thickness.")
        )
        self.combo_lasertype.SetToolTip(_("Filter entries of a certain laser type"))

        self.txt_entry_section.SetToolTip(_("Internal name of the library entry."))
        self.txt_entry_material.SetToolTip(_("Name of the library entry."))
        self.txt_entry_thickness.SetToolTip(_("Thickness of the material."))
        self.combo_entry_type.SetToolTip(
            _("Is this entry specific for a certain laser?")
        )
        self.txt_entry_note.SetToolTip(_("You can add additional information here."))

        button_box = wx.BoxSizer(wx.VERTICAL)

        self.btn_new = wxButton(self, wx.ID_ANY, _("Add new"))
        self.btn_new.SetToolTip(_("Add a new library entry"))
        self.btn_use_current = wxButton(self, wx.ID_ANY, _("Get current"))
        self.btn_use_current.SetToolTip(_("Use the currently defined operations"))
        self.btn_apply = wxButton(self, wx.ID_ANY, _("Load into Tree"))
        self.btn_apply.SetToolTip(
            _("Apply the current library entry to the operations branch")
        )
        self.btn_simple_apply = wxButton(self, wx.ID_ANY, _("Use for statusbar"))
        self.btn_simple_apply.SetToolTip(
            _("Use the current library entry for the statusbar icons")
        )
        self.btn_delete = wxButton(self, wx.ID_ANY, _("Delete"))
        self.btn_delete.SetToolTip(_("Delete the current library entry"))
        self.btn_duplicate = wxButton(self, wx.ID_ANY, _("Duplicate"))
        self.btn_duplicate.SetToolTip(_("Duplicate the current library entry"))
        self.btn_import = wxButton(self, wx.ID_ANY, _("Import"))
        self.btn_import.SetToolTip(
            _("Import a material library from ezcad or LightBurn")
        )
        self.btn_share = wxButton(self, wx.ID_ANY, _("Share"))
        self.btn_share.SetToolTip(
            _("Share the current library entry with the MeerK40t community")
        )

        button_box.Add(self.btn_new, 0, wx.EXPAND, 0)
        button_box.Add(self.btn_use_current, 0, wx.EXPAND, 0)
        button_box.Add(self.btn_apply, 0, wx.EXPAND, 0)
        button_box.Add(self.btn_simple_apply, 0, wx.EXPAND, 0)
        button_box.Add(self.btn_delete, 0, wx.EXPAND, 0)
        button_box.Add(self.btn_duplicate, 0, wx.EXPAND, 0)
        button_box.AddSpacer(self.btn_duplicate.Size[1])
        button_box.Add(self.btn_import, 0, wx.EXPAND, 0)
        button_box.Add(self.btn_share, 0, wx.EXPAND, 0)
        outer_box = wx.BoxSizer(wx.HORIZONTAL)
        outer_box.Add(result_box, 1, wx.EXPAND, 0)
        outer_box.Add(button_box, 0, wx.EXPAND, 0)
        main_sizer.Add(outer_box, 1, wx.EXPAND, 0)

        self.SetSizer(main_sizer)
        self.btn_reset.Bind(wx.EVT_BUTTON, self.on_reset)
        self.combo_lasertype.Bind(wx.EVT_COMBOBOX, self.update_list)
        self.txt_material.Bind(wx.EVT_TEXT, self.update_list)
        self.txt_thickness.Bind(wx.EVT_TEXT, self.update_list)
        self.btn_new.Bind(wx.EVT_BUTTON, self.on_new)
        self.btn_use_current.Bind(wx.EVT_BUTTON, self.on_use_current)
        self.btn_apply.Bind(wx.EVT_BUTTON, self.on_apply_tree)
        self.btn_simple_apply.Bind(wx.EVT_BUTTON, self.on_apply_statusbar)
        self.btn_delete.Bind(wx.EVT_BUTTON, self.on_delete)
        self.btn_duplicate.Bind(wx.EVT_BUTTON, self.on_duplicate)
        self.btn_import.Bind(wx.EVT_BUTTON, self.on_import)
        self.btn_share.Bind(wx.EVT_BUTTON, self.on_share)
        self.btn_expand.Bind(wx.EVT_BUTTON, self.toggle_extended)
        self.btn_set.Bind(wx.EVT_BUTTON, self.update_entry)
        self.btn_set.Bind(wx.EVT_RIGHT_DOWN, self.update_lasertype_for_all)
        self.tree_library.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_list_selection)
        self.list_preview.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_preview_selection)
        self.list_preview.Bind(
            wx.EVT_LIST_BEGIN_LABEL_EDIT, self.before_operation_update
        )
        self.list_preview.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.on_operation_update)

        self.tree_library.Bind(
            wx.EVT_RIGHT_DOWN,
            self.on_library_rightclick,
        )
        self.Bind(
            wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_preview_rightclick, self.list_preview
        )
        self.Bind(
            wx.EVT_LIST_COL_RIGHT_CLICK, self.on_preview_rightclick, self.list_preview
        )
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.SetupScrolling()
        # Hide not-yet-supported functions
        self.btn_share.Show(self.share_ready)
        self.active_material = None
        self.expanded_info = False
        self.Layout()
        self.on_resize(None)
        self.on_reset(None)

    @property
    def expanded_info(self):
        return self._expanded_info

    @expanded_info.setter
    def expanded_info(self, newvalue):
        self._expanded_info = newvalue
        info = dip_size(self, 20, 20)
        icon_size = info[0]
        if self._expanded_info:
            self.btn_expand.SetBitmap(icons8_caret_up.GetBitmap(resize=icon_size))
            self.btn_expand.SetToolTip(_("Click to hide extended infos"))
        else:
            self.btn_expand.SetBitmap(icons8_caret_down.GetBitmap(resize=icon_size))
            self.btn_expand.SetToolTip(_("Click to show extended infos"))
        self.box_extended.ShowItems(self._expanded_info)
        self.Layout()

    def toggle_extended(self, event):
        self.expanded_info = not self.expanded_info

    @property
    def active_material(self):
        return self._active_material

    @active_material.setter
    def active_material(self, newvalue):
        self._active_material = newvalue
        active = bool(newvalue is not None)
        self.btn_apply.Enable(active)
        self.btn_simple_apply.Enable(active)
        self.btn_delete.Enable(active)
        self.btn_duplicate.Enable(active)
        self.txt_entry_section.Enable(active)
        self.txt_entry_material.Enable(active)
        self.txt_entry_lens.Enable(active)
        self.txt_entry_power.Enable(active)
        self.txt_entry_title.Enable(active)
        self.txt_entry_thickness.Enable(active)
        self.txt_entry_note.Enable(active)
        self.combo_entry_type.Enable(active)
        self.btn_set.Enable(active)
        self.list_preview.Enable(active)
        self.fill_preview()

    @property
    def is_balor(self):
        if self.active_material is None:
            return False
        # a) laser-settings are set to fibre = 3
        # b) laser-settings are set to general and we have a defined fibre laser
        # Will be updated in fill_preview
        return self._balor

    def retrieve_material_list(
        self,
        filtername=None,
        filterlaser=None,
        filterthickness=None,
        reload=True,
        setter=None,
    ):
        if reload:
            self.material_list.clear()
            for section in self.op_data.section_set():
                if section == "previous":
                    continue
                count = 0
                secname = section
                secdesc = ""
                sectitle = ""
                thick = ""
                ltype = 0  # All lasers
                note = ""
                for subsection in self.op_data.derivable(secname):
                    if subsection.endswith(" info"):
                        secdesc = self.op_data.read_persistent(
                            str, subsection, "material", ""
                        )
                        sectitle = self.op_data.read_persistent(
                            str, subsection, "title", ""
                        )
                        thick = self.op_data.read_persistent(
                            str, subsection, "thickness", ""
                        )
                        ltype = self.op_data.read_persistent(
                            int, subsection, "laser", 0
                        )
                        note = self.op_data.read_persistent(str, subsection, "note", "")
                    else:
                        count += 1
                if not sectitle:
                    sectitle = secname.replace("_", " ")
                entry = {
                    "section": secname,
                    "material": secdesc,
                    "title": sectitle,
                    "laser": ltype,
                    "thickness": thick,
                    "note": note,
                    "opcount": count,
                }
                # entry = [secname, secdesc, count, ltype, thick, note]
                self.material_list[secname] = entry
        listidx = -1
        self.display_list.clear()
        display = []

        if self.categorisation == 1:
            # lasertype
            sort_key_primary = "laser"  # 3
            sort_key_secondary = "material"  # 1
            sort_key_tertiary = "thickness"  # 4
        elif self.categorisation == 2:
            # thickness
            sort_key_primary = "thickness"  # 4
            sort_key_secondary = "material"
            sort_key_tertiary = "laser"  # 3
        else:
            # material
            sort_key_primary = "material"
            sort_key_secondary = "thickness"  # 4
            sort_key_tertiary = "laser"  # 3
        for key, entry in self.material_list.items():
            listidx += 1
            display.append((entry, listidx))
        display.sort(
            key=lambda e: (
                e[0][sort_key_primary],
                e[0][sort_key_secondary],
                e[0][sort_key_tertiary],
            )
        )

        tree = self.tree_library
        tree.Freeze()
        tree.DeleteAllItems()
        tree_root = tree.AddRoot(_("Materials"))
        tree.SetItemData(tree_root, -1)
        idx_primary = 0
        idx_secondary = 0
        newvalue = None
        selected = None
        first_item = None
        selected_parent = None
        last_category_primary = None
        last_category_secondary = None
        tree_primary = tree_root
        tree_secondary = tree_root
        visible_count = [0, 0]  # All, subsections
        for content in display:
            entry = content[0]
            listidx = content[1]
            ltype = entry["laser"]
            if ltype is None:
                ltype = 0
            if 0 <= ltype < len(self.laser_choices):
                info = self.laser_choices[ltype]
            else:
                info = "???"
            if sort_key_primary == "laser":  # laser
                this_category_primary = info
            else:
                this_category_primary = entry[sort_key_primary].replace("_", " ")
            if sort_key_secondary == 3:  # laser
                this_category_secondary = info
            else:
                this_category_secondary = entry[sort_key_secondary].replace("_", " ")
            if not this_category_primary:
                this_category_primary = "No " + sort_key_primary
            key = entry["section"]
            if (
                filtername is not None
                and filtername.lower() not in entry["material"].lower()
            ):
                continue
            if filterthickness is not None and not entry[
                "thickness"
            ].lower().startswith(filterthickness.lower()):
                continue
            if filterlaser is not None:
                if filterlaser not in (0, entry["laser"]):
                    continue
            self.display_list.append(entry)
            visible_count[0] += 1
            if last_category_primary != this_category_primary:
                # New item
                last_category_secondary = ""
                idx_primary += 1
                idx_secondary = 0
                tree_primary = tree.AppendItem(tree_root, this_category_primary)
                tree.SetItemData(tree_primary, -1)
                tree_secondary = tree_primary
            if last_category_secondary != this_category_secondary:
                # new subitem
                tree_secondary = tree.AppendItem(tree_primary, this_category_secondary)
                tree.SetItemData(tree_secondary, -1)
                visible_count[1] += 1
            idx_secondary += 1

            description = f"#{idx_primary}.{idx_secondary} - {entry['title']}, {entry['thickness']} ({info}, {entry['opcount']} ops)"
            tree_id = tree.AppendItem(tree_secondary, description)
            tree.SetItemData(tree_id, listidx)
            if first_item is None:
                first_item = tree_id
            if key == setter:
                newvalue = key
                selected = tree_id
                selected_parent = tree_primary

            last_category_primary = this_category_primary
            last_category_secondary = this_category_secondary

        self.active_material = newvalue
        tree.Expand(tree_root)
        # if visible_count[0] <= 10:
        #     tree.ExpandAllChildren(tree_root)
        if visible_count[1] == 1:
            tree.ExpandAllChildren(tree_root)
        elif visible_count[1] <= 10:
            child, cookie = tree.GetFirstChild(tree_root)
            while child.IsOk():
                tree.Expand(child)
                child, cookie = tree.GetNextChild(tree_root, cookie)

        if selected is None:
            if visible_count[0] == 1:  # Just one, why don't we select it
                self.tree_library.SelectItem(first_item)
        else:
            tree.ExpandAllChildren(selected_parent)
            self.tree_library.SelectItem(selected)
        tree.Thaw()
        tree.Refresh()

    @staticmethod
    def get_nth_dict_entry(dictionary: dict, n=0):
        if n < 0:
            n += len(dictionary)
        for i, key in enumerate(dictionary.keys()):
            if i == n:
                return key
        return None

    def get_nth_material(self, n=0):
        return self.get_nth_dict_entry(self.material_list, n)

    def get_nth_operation(self, n=0):
        return self.get_nth_dict_entry(self.operation_list, n)

    def on_share(self, event):
        if self.active_material is None:
            return

        self.context.setting(str, "author", "")
        last_author = self.context.author
        if last_author is None:
            last_author = ""
        dlg = wx.TextEntryDialog(
            self,
            _(
                "Thank you for your willingness to share your material setting with the MeerK40t community.\n"
                + "Please provide a name to honor your authorship."
            ),
            caption=_("Share material setting"),
            value=last_author,
        )
        dlg.SetValue(last_author)
        res = dlg.ShowModal()
        last_author = dlg.GetValue()
        dlg.Destroy()
        if res == wx.ID_CANCEL:
            return
        self.context.author = last_author
        # We will store the relevant section in a separate file
        oplist, opinfo = self.context.elements.load_persistent_op_list(
            self.active_material,
            use_settings=self.op_data,
        )
        if len(oplist) == 0:
            return
        opinfo["author"] = last_author
        directory = get_safe_path(self.context.kernel.name)
        local_file = os.path.join(directory, "op_export.cfg")
        if os.path.exists(local_file):
            try:
                os.remove(local_file)
            except (OSError, PermissionError):
                return
        settings = Settings(
            self.context.kernel.name, "op_export.cfg", ignore_settings=False
        )
        opsection = f"{self.active_material} info"
        for key, value in opinfo.items():
            settings.write_persistent(opsection, key, value)

        def _save_tree(name, op_list):
            for i, op in enumerate(op_list):
                if hasattr(op, "allow_save"):
                    if not op.allow_save():
                        continue
                if op.type == "reference":
                    # We do not save references.
                    continue
                section = f"{name} {i:06d}"
                settings.write_persistent(section, "type", op.type)
                op.save(settings, section)
                try:
                    _save_tree(section, op.children)
                except AttributeError:
                    pass

        _save_tree(opsection, oplist)
        settings.write_configuration()
        # print ("Sharing")
        try:
            with open(local_file, "r") as f:
                data = f.read()
        except (OSError, RuntimeError, PermissionError, FileNotFoundError):
            return
        self.send_data_to_community(local_file, data)

    def send_data_to_community(self, filename, data):
        """
        Sends the material setting to a server using rfc1341 7.2 The multipart Content-Type
        https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html

        @param filename: filename to use when sending file
        @param data: data to send
        @return:
        """
        import socket

        MEERK40T_HOST = "dev.meerk40t.com"

        host = MEERK40T_HOST  # Replace with the actual host
        port = 80  # Replace with the actual port

        # Construct the HTTP request
        boundary = "----------------meerk40t-material"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: text/plain\r\n"
            "\r\n"
            f"{data}\r\n"
            f"--{boundary}--\r\n"
        )

        headers = (
            f"POST /upload HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "User-Agent: meerk40t/1.0.0\r\n"
            f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
            f"Content-Length: {len(body)}\r\n"
            "\r\n"
        )

        try:
            # Create a socket connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((host, port))

                # Send the request
                request = f"{headers}{body}"
                client_socket.sendall(request.encode())

                # Receive and print the response
                response = client_socket.recv(4096)
                response = response.decode("utf-8")
        except Exception:
            response = ""

        response_lines = response.split("\n")
        http_code = response_lines[0]

        # print(response)

        if http_code.startswith("HTTP/1.1 200 OK"):
            message = response_lines[-1]
            dlg = wx.MessageDialog(
                None,
                _("We got your file. Thank you for helping\n\n") + message,
                _("Thanks"),
                wx.OK,
            )
            dlg.ShowModal()
            dlg.Destroy()
        else:
            # print(response)
            dlg = wx.MessageDialog(
                None,
                _("We're sorry, that didn't work.\n\n") + "\n\n" + str(http_code),
                _("Thanks"),
                wx.OK,
            )
            dlg.ShowModal()
            dlg.Destroy()

    def on_duplicate(self, event):
        if self.active_material is None:
            return
        op_list, op_info = self.context.elements.load_persistent_op_list(
            self.active_material,
            use_settings=self.op_data,
        )
        if len(op_list) == 0:
            return
        oldsection = self.active_material
        if oldsection.endswith(")"):
            idx = oldsection.rfind("(")
            if idx >= 0:
                oldsection = oldsection[:idx]
                if oldsection.endswith("_"):
                    oldsection = oldsection[:-1]

        counter = 0
        while True:
            counter += 1
            newsection = f"{oldsection}_({counter})"
            if newsection not in self.material_list:
                break

        oldname = oldsection
        if "title" in op_info:
            oldname = op_info["title"]
            if oldname.endswith(")"):
                idx = oldname.rfind("(")
                if idx >= 0:
                    oldname = oldname[:idx]
        newname = f"{oldname} ({counter})"
        op_info["title"] = newname
        self.context.elements.save_persistent_operations_list(
            newsection,
            oplist=op_list,
            opinfo=op_info,
            inform=False,
            use_settings=self.op_data,
        )
        self.op_data.write_configuration()
        self.retrieve_material_list(reload=True, setter=newsection)

    def on_delete(self, event):
        if self.active_material is None:
            return
        if self.context.kernel.yesno(
            _("Do you really want to delete this entry? This can't be undone.")
        ):
            self.context.elements.clear_persistent_operations(
                self.active_material,
                use_settings=self.op_data,
            )
            self.op_data.write_configuration()
            self.retrieve_material_list(reload=True)

    def on_delete_all(self, event):
        if self.context.kernel.yesno(
            _("Do you really want to delete all visible entries? This can't be undone.")
        ):
            busy = self.context.kernel.busyinfo
            busy.start(msg=_("Deleting data"))
            for idx, entry in enumerate(self.display_list):
                busy.change(msg=f"{idx+1}/{len(self.display_list)}", keep=1)
                material = entry["section"]
                self.context.elements.clear_persistent_operations(
                    material, use_settings=self.op_data, flush=False
                )
            self.op_data.write_configuration()
            busy.end()
            self.on_reset(None)

    def invalid_file(self, filename):
        dlg = wx.MessageDialog(
            self,
            _("Unrecognized format in file {info}".format(info=filename)),
            _("Invalid file"),
            wx.OK | wx.ICON_WARNING,
        )
        dlg.ShowModal()
        dlg.Destroy()

    def import_lightburn(self, info):
        # info = (fname, old_lens, new_lens, old_power, new_power, factor_from_lens, factor_from_power, factor, consolidate)
        filename = info[0]
        factor = info[7]
        join_entries = info[8]
        lens_info = info[2]
        if lens_info is None:
            lens_info = ""
        power_info = info[4]
        if power_info is None:
            power_info = ""

        if not os.path.exists(filename):
            return False
        added = False
        try:
            tree = ET.parse(filename)
        except ET.ParseError:
            self.invalid_file(filename)
            return False

        root = tree.getroot()
        if root.tag.lower() != "lightburnlibrary":
            self.invalid_file(filename)
            return False

        # We need to have a new id...
        new_import_id = 0
        pattern = "import_"
        for section in self.op_data.section_set():
            if section.startswith(pattern):
                s = section[len(pattern) :]
                try:
                    number = int(s)
                except ValueError:
                    number = 0
                if number > new_import_id:
                    new_import_id = number

        # def traverse(node):
        #     print(f"Node: {node.tag}")
        #     for attr in node.attrib:
        #         print(f"Attribute: {attr} = {node.attrib[attr]}")
        #     for child in node:
        #         traverse(child)
        # traverse(root)
        operation_ids = dict()

        for material_node in root:
            material = material_node.attrib["name"]
            last_thickness = None
            for entry_node in material_node:
                thickness = entry_node.attrib.get("Thickness", "-1")
                try:
                    thickness_value = float(thickness)
                except ValueError:
                    thickness_value = -1
                if thickness_value < 0:
                    thickness = ""
                desc = entry_node.attrib.get("Desc", "")
                title = entry_node.attrib.get("NoThickTitle", "")
                label = desc
                if last_thickness == thickness and join_entries:
                    # We keep those together
                    pass
                else:
                    operation_ids.clear()
                    operation_ids["op engrave"] = ["E", 0]
                    operation_ids["op raster"] = ["R", 0]
                    operation_ids["op cut"] = ["C", 0]
                    operation_ids["op image"] = ["I", 0]
                    new_import_id += 1
                    sect_num = -1
                    sect = f"{pattern}{new_import_id:0>4}"
                    info_section_name = f"{sect} info"
                    self.op_data.write_persistent(info_section_name, "title", title)
                    self.op_data.write_persistent(
                        info_section_name, "material", material
                    )
                    self.op_data.write_persistent(info_section_name, "laser", 0)
                    self.op_data.write_persistent(
                        info_section_name, "thickness", thickness
                    )
                    self.op_data.write_persistent(
                        info_section_name, "power", power_info
                    )
                    self.op_data.write_persistent(info_section_name, "lens", lens_info)
                    note = label
                last_thickness = thickness
                added = True
                for cutsetting_node in entry_node:
                    powerval = None
                    speedval = None
                    sect_num += 1
                    section_name = f"{sect} {sect_num:0>6}"
                    cut_type = cutsetting_node.attrib.get("type", "Scan")
                    if cut_type.lower() == "cut":
                        op_type = "op engrave"
                    elif cut_type.lower() == "scan":
                        op_type = "op raster"
                    elif cut_type.lower() == "image":
                        op_type = "op image"
                    else:
                        op_type = "op engrave"
                    if op_type in operation_ids:
                        operation_ids[op_type][1] += 1
                    else:
                        operation_ids[op_type] = [op_type[3].upper(), 1]

                    self.op_data.write_persistent(section_name, "type", op_type)
                    self.op_data.write_persistent(
                        section_name,
                        "id",
                        f"{operation_ids[op_type][0]}{operation_ids[op_type][1]}",
                    )
                    self.op_data.write_persistent(section_name, "label", label)

                    for param_node in cutsetting_node:
                        param = param_node.tag.lower()
                        value = param_node.attrib.get("Value", "")
                        if not value:
                            continue
                        try:
                            numeric_value = float(value)
                        except ValueError:
                            continue

                        if param == "numpasses":
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "passes", numeric_value
                                )
                        elif param == "speed":
                            if numeric_value != 0:
                                speedval = numeric_value
                        elif param == "maxpower":
                            if numeric_value != 0:
                                powerval = numeric_value * 10
                        elif param == "frequency":
                            # khz
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "frequency", numeric_value / 1000.0
                                )
                        elif param == "jumpspeed":
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "rapid_enabled", True
                                )
                                self.op_data.write_persistent(
                                    section_name, "rapid_speed", numeric_value
                                )
                        else:
                            # note += f"\\n{param} = {numeric_value}"
                            pass
                    # Ready, let's write power and speed
                    if factor != 1:
                        old_l = info[1]
                        new_l = info[2]
                        factor_l = info[5]
                        if old_l is not None:
                            note += f"\\n({cut_type}) Converted lens-size {old_l}mm -> {new_l}mm: {factor_l:.2}"
                        old_l = info[3]
                        new_l = info[4]
                        factor_l = info[6]
                        if old_l is not None:
                            note += f"\\n({cut_type}) Converted power {old_l}W -> {new_l}W: {factor_l:.2}"
                    if powerval * factor > 1000:
                        # Too much, let's reduce speed instead
                        if speedval:
                            note += f"\\n({cut_type}) Needed to reduce speed {speedval:.1}mm/s -> {speedval / factor:.2}mm/s"
                            speedval *= 1 / factor
                    else:
                        powerval *= factor
                    self.op_data.write_persistent(section_name, "speed", speedval)
                    self.op_data.write_persistent(section_name, "power", powerval)
                self.op_data.write_persistent(info_section_name, "note", note)

        return added

    def import_ezcad(self, info):
        # info = (fname, old_lens, new_lens, old_power, new_power, factor_from_lens, factor_from_power, factor, consolidate)
        filename = info[0]
        factor = info[7]
        lens_info = info[2]
        if lens_info is None:
            lens_info = ""
        power_info = info[4]
        if power_info is None:
            power_info = ""
        if not os.path.exists(filename):
            return False
        added = False
        # We can safely assume this a fibre laser...
        laser_type = 0
        for idx, desc in enumerate(self.laser_choices):
            if "fibre" in desc.lower():
                laser_type = idx
                break
        try:
            with open(filename, "r") as f:
                # We need to have a new id...
                new_import_id = 0
                pattern = "import_"
                for section in self.op_data.section_set():
                    if section.startswith(pattern):
                        s = section[len(pattern) :]
                        try:
                            number = int(s)
                        except ValueError:
                            number = 0
                        if number > new_import_id:
                            new_import_id = number
                section_name = ""
                info_section_name = ""
                info_box = ""
                powerval = None
                speedval = None

                while True:
                    line = f.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line.startswith("["):
                        if info_box and info_section_name:
                            self.op_data.write_persistent(
                                info_section_name, "note", info_box
                            )
                        if powerval and section_name:
                            if factor != 1:
                                old_l = info[1]
                                new_l = info[2]
                                factor_l = info[5]
                                if old_l is not None:
                                    if info_box:
                                        info_box += "\\n"
                                    info_box += f"Converted lens-size {old_l}mm -> {new_l}mm: {factor_l:.2}"
                                old_l = info[3]
                                new_l = info[4]
                                factor_l = info[6]
                                if old_l is not None:
                                    if info_box:
                                        info_box += "\\n"
                                    info_box += f"Converted power {old_l}W -> {new_l}W: {factor_l:.2}"
                            if powerval * factor > 1000:
                                # Too much, let's reduce speed instead
                                if speedval:
                                    if info_box:
                                        info_box += "\\n"
                                    info_box += f"Needed to reduce speed {numeric_value:.1}mm/s -> {numeric_value * speed_factor:.2}mm/s"
                                    speedval *= 1 / factor
                            else:
                                powerval *= factor
                            self.op_data.write_persistent(
                                section_name, "speed", speedval
                            )
                            self.op_data.write_persistent(
                                section_name, "power", powerval
                            )
                        powerval = None
                        speedval = None
                        info_box = ""
                        new_import_id += 1
                        sect = f"{pattern}{new_import_id:0>4}"
                        info_section_name = f"{sect} info"
                        section_name = f"{sect} {0:0>6}"
                        matname = line[1:-1]
                        if matname.startswith("F "):
                            matname = matname[2:]
                        self.op_data.write_persistent(
                            info_section_name, "material", matname
                        )
                        title = matname
                        if power_info:
                            title += f" {power_info}W"
                        if lens_info:
                            title += f" {lens_info}mm"
                        self.op_data.write_persistent(info_section_name, "title", title)
                        self.op_data.write_persistent(
                            info_section_name, "power", power_info
                        )
                        self.op_data.write_persistent(
                            info_section_name, "lens", lens_info
                        )
                        self.op_data.write_persistent(
                            info_section_name, "laser", laser_type
                        )
                        self.op_data.write_persistent(
                            section_name, "type", "op engrave"
                        )
                        self.op_data.write_persistent(section_name, "id", "F1")
                        speed_factor = 1.0
                        added = True
                    else:
                        if not section_name:
                            continue
                        idx = line.find("=")
                        if idx <= 0:
                            continue
                        param = line[:idx].lower()
                        value = line[idx + 1 :]
                        try:
                            numeric_value = float(value)
                        except ValueError:
                            numeric_value = 0
                        if param == "loop":
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "passes", numeric_value
                                )
                        elif param == "markspeed":
                            if numeric_value != 0:
                                speedval = numeric_value
                        elif param == "powerratio":
                            if numeric_value != 0:
                                powerval = numeric_value * 10
                        elif param == "freq":
                            # khz
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "frequency", numeric_value / 1000.0
                                )
                        elif param == "jumpspeed":
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "rapid_enabled", True
                                )
                                self.op_data.write_persistent(
                                    section_name, "rapid_speed", numeric_value
                                )
                        elif param == "starttc":
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "timing_enabled", True
                                )
                                self.op_data.write_persistent(
                                    section_name, "delay_laser_on", numeric_value
                                )
                        elif param == "laserofftc":
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "timing_enabled", True
                                )
                                self.op_data.write_persistent(
                                    section_name, "delay_laser_off", numeric_value
                                )
                        elif param == "polytc":
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "timing_enabled", True
                                )
                                self.op_data.write_persistent(
                                    section_name, "delay_polygon", numeric_value
                                )
                        elif param == "qpulsewidth":
                            if numeric_value != 0:
                                self.op_data.write_persistent(
                                    section_name, "pulse_width_enabled", True
                                )
                                self.op_data.write_persistent(
                                    section_name, "pulse_width", numeric_value
                                )
                        else:
                            # Unknown / unsupported - a significant amount of the parameters
                            # would require the addition of different things like hatches,
                            # wobbles or device specific settings
                            if numeric_value != 0:
                                if info_box:
                                    info_box += "\\n"
                                info_box += f"{param} = {numeric_value}"
                # Residual information available?
                if powerval and section_name:
                    if factor != 1:
                        old_l = info[1]
                        new_l = info[2]
                        factor_l = info[5]
                        if old_l is not None:
                            if info_box:
                                info_box += "\\n"
                            info_box += f"Converted lens-size {old_l}mm -> {new_l}mm: {factor_l:.2}"
                        old_l = info[3]
                        new_l = info[4]
                        factor_l = info[6]
                        if old_l is not None:
                            if info_box:
                                info_box += "\\n"
                            info_box += (
                                f"Converted power {old_l}W -> {new_l}W: {factor_l:.2}"
                            )
                    if powerval * factor > 1000:
                        # Too much, let's reduce speed instead
                        if speedval:
                            if info_box:
                                info_box += "\\n"
                            info_box += f"Needed to reduce speed {numeric_value:.1}mm/s -> {numeric_value * speed_factor:.2}mm/s"
                            speedval *= 1 / factor
                    else:
                        powerval *= factor
                    self.op_data.write_persistent(section_name, "speed", speedval)
                    self.op_data.write_persistent(section_name, "power", powerval)
                if info_box and info_section_name:
                    self.op_data.write_persistent(info_section_name, "note", info_box)

        except (OSError, RuntimeError, PermissionError, FileNotFoundError):
            return False
        if added:
            self.op_data.write_configuration()
        return added

    def on_import(self, event, filename=None):
        #
        info = None
        mydlg = ImportDialog(
            None, id=wx.ID_ANY, context=self.context, filename=filename
        )
        if mydlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            info = mydlg.result()
        mydlg.Destroy()
        if info is None:
            return
        added = False
        myfile = info[0]
        if myfile.endswith(".clb"):
            added = self.import_lightburn(info)
        elif myfile.endswith(".lib") or myfile.endswith(".ini"):
            added = self.import_ezcad(info)
        else:
            self.invalid_file(myfile)

        if added:
            self.on_reset(None)

    def on_apply_statusbar(self, event):
        if self.active_material is None:
            return
        op_list, op_info = self.context.elements.load_persistent_op_list(
            self.active_material,
            use_settings=self.op_data,
        )
        if len(op_list) == 0:
            return
        self.context.elements.default_operations = list(op_list)
        self.context.signal("default_operations")

    def on_apply_tree(self, event):
        if self.active_material is None:
            return
        op_list, op_info = self.context.elements.load_persistent_op_list(
            self.active_material,
            use_settings=self.op_data,
        )
        if len(op_list) == 0:
            return
        response = self.context.kernel.yesno(
            _("Do you want to remove all existing operations before loading this set?"),
            caption=_("Clear Operation-List"),
        )
        self.context.elements.load_persistent_operations(
            self.active_material, clear=response
        )
        self.context.signal("rebuild_tree")

    def on_new(self, event):
        entry_txt = self.txt_material.GetValue()
        if entry_txt == "":
            entry_txt = "material"
        if entry_txt in self.material_list:
            idx = 0
            while True:
                idx += 1
                pattern = f"{entry_txt}_({idx})"
                if pattern not in self.material_list:
                    break
            entry_txt = pattern
        # entry_type = self.combo_entry_type.GetSelection()
        # if entry_type < 0:
        #     entry_type = 0
        # We need to create a new one...
        op_info = dict()
        op_info["material"] = "New material"
        op_info["laser"] = 0
        op_info["thickness"] = "4mm"
        op_info["note"] = "You can put additional operation instructions here."
        section = entry_txt

        if len(list(self.context.elements.ops())) == 0:
            op_list = self.context.elements.default_operations
            if len(op_list) == 0:
                return
            # op_list = None save op_branch
            self.context.elements.save_persistent_operations_list(
                section,
                oplist=op_list,
                opinfo=op_info,
                inform=False,
                use_settings=self.op_data,
            )
        else:
            # op_list = None save op_branch
            self.context.elements.save_persistent_operations_list(
                section,
                oplist=None,
                opinfo=op_info,
                inform=False,
                use_settings=self.op_data,
            )
        self.op_data.write_configuration()
        self.retrieve_material_list(reload=True, setter=section)

    def on_use_current(self, event):
        section = None
        op_info = None
        if self.active_material is not None:
            if self.context.kernel.yesno(
                _(
                    "Do you want to use the operations in the tree for the current entry?"
                )
            ):
                section = self.active_material
                op_info = self.context.elements.load_persistent_op_info(
                    self.active_material,
                    use_settings=self.op_data,
                )
                if "material" not in op_info:
                    op_info["material"] = "Operations List"
                if "laser" not in op_info:
                    op_info["laser"] = 0

        if section is None:
            entry_txt = self.txt_material.GetValue()
            if entry_txt == "":
                entry_txt = "material"
            if entry_txt in self.material_list:
                idx = 0
                while True:
                    idx += 1
                    pattern = f"{entry_txt}_({idx})"
                    if pattern not in self.material_list:
                        break
                entry_txt = pattern
            # entry_type = self.combo_entry_type.GetSelection()
            # if entry_type < 0:
            #     entry_type = 0
            # We need to create a new one...
            op_info = dict()
            op_info["material"] = "New material"
            op_info["laser"] = 0
            section = entry_txt

        # op_list = None save op_branch
        self.context.elements.save_persistent_operations_list(
            section,
            oplist=None,
            opinfo=op_info,
            inform=False,
            use_settings=self.op_data,
        )
        self.op_data.write_configuration()
        self.retrieve_material_list(reload=True, setter=section)

    def on_reset(self, event):
        self.no_reload = True
        self.txt_material.SetValue("")
        self.txt_thickness.SetValue("")
        self.combo_lasertype.SetSelection(0)
        self.no_reload = False
        self.update_list(reload=True)

    def update_list(self, *args, **kwargs):
        if self.no_reload:
            return
        filter_txt = self.txt_material.GetValue()
        filter_thickness = self.txt_thickness.GetValue()
        filter_type = self.combo_lasertype.GetSelection()
        if filter_txt == "":
            filter_txt = None
        if filter_thickness == "":
            filter_thickness = None
        if filter_type < 0:
            filter_type = None
        reload = False
        if "reload" in kwargs:
            reload = kwargs["reload"]
        self.retrieve_material_list(
            filtername=filter_txt,
            filterlaser=filter_type,
            filterthickness=filter_thickness,
            reload=reload,
            setter=self.active_material,
        )

    def update_lasertype_for_all(self, event):
        op_ltype = self.combo_entry_type.GetSelection()
        if op_ltype < 0:
            return
        changes = False
        for entry in self.display_list:
            material = entry["section"]
            section = f"{material} info"
            self.op_data.write_persistent(section, "laser", op_ltype)
            changes = True
        if changes:
            self.op_data.write_configuration()
        self.on_reset(None)

    def update_entry(self, event):
        if self.active_material is None:
            return
        op_section = self.txt_entry_section.GetValue()
        for forbidden in " []":
            op_section = op_section.replace(forbidden, "_")
        ctrls = (
            self.txt_entry_title,
            self.txt_entry_material,
            self.txt_entry_thickness,
            self.txt_entry_power,
            self.txt_entry_lens,
        )
        fields = (
            "title",
            "material",
            "thickness",
            "power",
            "lens",
        )
        data = [(field, ctrl.GetValue()) for field, ctrl in zip(fields, ctrls)]

        op_ltype = self.combo_entry_type.GetSelection()
        if op_ltype < 0:
            op_ltype = 0
        data.append(("laser", op_ltype))

        # Note, convert linebreaks
        op_note = self.txt_entry_note.GetValue().replace("\n", "\\n")
        data.append(("note", op_note))

        op_list, op_info = self.context.elements.load_persistent_op_list(
            self.active_material,
            use_settings=self.op_data,
        )
        if len(op_list) == 0:
            return
        to_save = False
        for entry in data:
            field, value = entry
            stored_value = op_info.get(field, "")
            if value != stored_value:
                op_info[field] = value
                to_save = True
        if to_save:
            if self.active_material != op_section:
                self.context.elements.clear_persistent_operations(
                    self.active_material,
                    use_settings=self.op_data,
                )
                self.active_material = op_section
            self.context.elements.save_persistent_operations_list(
                self.active_material,
                oplist=op_list,
                opinfo=op_info,
                inform=False,
                use_settings=self.op_data,
            )
            self.op_data.write_configuration()
            self.retrieve_material_list(reload=True, setter=self.active_material)

    def on_list_selection(self, event):
        try:
            item = event.GetItem()
            if item:
                listidx = self.tree_library.GetItemData(item)
                if listidx >= 0:
                    info = self.get_nth_material(listidx)
                    self.active_material = info
                else:
                    self.active_material = None
        except RuntimeError:
            return

    def fill_preview(self):
        self._balor = False
        for obj, name, sname in self.context.find("dev_info"):
            if obj is not None and "balor" in sname.lower():
                self._balor = True
                break

        self.list_preview.Freeze()
        self.list_preview.DeleteAllItems()
        self.operation_list.clear()
        secdesc = ""
        thickness = ""
        info_power = ""
        info_lens = ""
        info_title = ""
        note = ""
        ltype = 0
        if self.active_material is not None:
            secdesc = ""
            idx = 0
            for subsection in self.op_data.derivable(self.active_material):
                if subsection.endswith(" info"):
                    info_title = self.op_data.read_persistent(
                        str, subsection, "title", ""
                    )
                    info_power = self.op_data.read_persistent(
                        str, subsection, "power", ""
                    )
                    info_lens = self.op_data.read_persistent(
                        str, subsection, "lens", ""
                    )
                    secdesc = self.op_data.read_persistent(
                        str, subsection, "material", ""
                    )
                    thickness = self.op_data.read_persistent(
                        str, subsection, "thickness", ""
                    )
                    ltype = self.op_data.read_persistent(int, subsection, "laser", 0)
                    note = self.op_data.read_persistent(str, subsection, "note", "")
                    # We need to replace stored linebreaks with real linebreaks
                    note = note.replace("\\n", "\n")
                    if ltype == 3:
                        self._balor = True
                    elif ltype != 0:
                        self._balor = False
                    continue
                optype = self.op_data.read_persistent(str, subsection, "type", "")
                if optype is None or optype == "":
                    continue
                idx += 1
                opid = self.op_data.read_persistent(str, subsection, "id", "")
                oplabel = self.op_data.read_persistent(str, subsection, "label", "")
                speed = self.op_data.read_persistent(str, subsection, "speed", "")
                power = self.op_data.read_persistent(str, subsection, "power", "")
                frequency = self.op_data.read_persistent(
                    str, subsection, "frequency", ""
                )
                if not self.is_balor:
                    frequency = ""
                command = self.op_data.read_persistent(str, subsection, "command", "")
                if power == "" and optype.startswith("op "):
                    power = "1000"
                list_id = self.list_preview.InsertItem(
                    self.list_preview.GetItemCount(), f"#{idx}"
                )
                try:
                    info = self.opinfo[optype]
                except KeyError:
                    info = self.opinfo["generic"]
                    info = (optype, info[1], info[2])
                if command:
                    if oplabel:
                        oplabel += " "
                    else:
                        oplabel = ""
                    oplabel += f"({command})"
                self.list_preview.SetItem(list_id, 1, info[0])
                self.list_preview.SetItem(list_id, 2, opid)
                self.list_preview.SetItem(list_id, 3, oplabel)
                self.list_preview.SetItem(list_id, 4, power)
                self.list_preview.SetItem(list_id, 5, speed)
                self.list_preview.SetItem(list_id, 6, frequency)
                self.list_preview.SetItemImage(list_id, info[2])
                self.list_preview.SetItemData(list_id, idx - 1)
                self.operation_list[subsection] = (optype, opid, oplabel, power, speed)
        self.list_preview.Thaw()
        self.list_preview.Refresh()
        if self.active_material is None:
            actval = ""
        else:
            actval = self.active_material
        # print (f"id: '{actval}'\ntitle: '{info_title}'\nmaterial: '{secdesc}'")
        if not info_title:
            info_title = actval.replace("_", " ")
        self.txt_entry_section.SetValue(actval)
        self.txt_entry_material.SetValue(secdesc)
        self.txt_entry_thickness.SetValue(thickness)
        self.txt_entry_title.SetValue(info_title)
        self.txt_entry_power.SetValue(info_power)
        self.txt_entry_lens.SetValue(info_lens)
        self.txt_entry_note.SetValue(note)
        self.combo_entry_type.SetSelection(ltype)
        wd4 = self.list_preview.GetColumnWidth(4)
        wd5 = self.list_preview.GetColumnWidth(5)
        wd6 = self.list_preview.GetColumnWidth(6)
        if self.is_balor and wd6 == 0:
            wd = int((wd4 + wd5) / 3)
            for col in range(4, 7):
                self.list_preview.SetColumnWidth(col, wd)
        elif not self.is_balor and wd6 != 0:
            self.list_preview.SetColumnWidth(6, 0)
            wd = int((wd4 + wd5 + wd6) / 2)
            for col in range(4, 6):
                self.list_preview.SetColumnWidth(col, wd)

    def on_preview_selection(self, event):
        event.Skip()

    def on_library_rightclick(self, event):
        event.Skip()
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, _("Add new"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.on_new, item)

        item = menu.Append(wx.ID_ANY, _("Get current"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.on_use_current, item)

        item = menu.Append(wx.ID_ANY, _("Load into Tree"), "", wx.ITEM_NORMAL)
        menu.Enable(item.GetId(), bool(self.active_material is not None))
        self.Bind(wx.EVT_MENU, self.on_apply_tree, item)

        item = menu.Append(wx.ID_ANY, _("Use for statusbar"), "", wx.ITEM_NORMAL)
        menu.Enable(item.GetId(), bool(self.active_material is not None))
        self.Bind(wx.EVT_MENU, self.on_apply_statusbar, item)

        item = menu.Append(wx.ID_ANY, _("Duplicate"), "", wx.ITEM_NORMAL)
        menu.Enable(item.GetId(), bool(self.active_material is not None))
        self.Bind(wx.EVT_MENU, self.on_duplicate, item)

        item = menu.Append(wx.ID_ANY, _("Delete"), "", wx.ITEM_NORMAL)
        menu.Enable(item.GetId(), bool(self.active_material is not None))
        self.Bind(wx.EVT_MENU, self.on_delete, item)

        if self.share_ready:
            menu.AppendSeparator()
            item = menu.Append(wx.ID_ANY, _("Share"), "", wx.ITEM_NORMAL)
            menu.Enable(item.GetId(), bool(self.active_material is not None))
            self.Bind(wx.EVT_MENU, self.on_share, item)

        def create_minimal(event):
            section = "minimal"
            oplist = self.context.elements.create_minimal_op_list()
            opinfo = {"material": "Minimal list", "laser": 0}
            self.context.elements.save_persistent_operations_list(
                section,
                oplist,
                opinfo,
                False,
                use_settings=self.op_data,
            )
            self.op_data.write_configuration()
            self.retrieve_material_list(reload=True, setter=section)

        def create_basic(event):
            section = "basic"
            oplist = self.context.elements.create_basic_op_list()
            opinfo = {"material": "Basic list", "laser": 0}
            self.context.elements.save_persistent_operations_list(
                section,
                oplist,
                opinfo,
                False,
                use_settings=self.op_data,
            )
            self.op_data.write_configuration()
            self.retrieve_material_list(reload=True, setter=section)

        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY, _("Create minimal"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, create_minimal, item)
        item = menu.Append(wx.ID_ANY, _("Create basic"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, create_basic, item)
        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY, _("Delete all"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.on_delete_all, item)
        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY, _("Sort by..."), "", wx.ITEM_NORMAL)
        menu.Enable(item.GetId(), False)

        def set_sort_key(sortvalue):
            local_value = sortvalue

            def sort_handler(event):
                self.categorisation = local_value
                self.retrieve_material_list(reload=False, setter=self.active_material)

            return sort_handler

        item = menu.Append(wx.ID_ANY, _("Material"), "", wx.ITEM_RADIO)
        item.Check(bool(self.categorisation == 0))
        self.Bind(wx.EVT_MENU, set_sort_key(0), item)
        item = menu.Append(wx.ID_ANY, _("Laser"), "", wx.ITEM_RADIO)
        item.Check(bool(self.categorisation == 1))
        self.Bind(wx.EVT_MENU, set_sort_key(1), item)
        item = menu.Append(wx.ID_ANY, _("Thickness"), "", wx.ITEM_RADIO)
        item.Check(bool(self.categorisation == 2))
        self.Bind(wx.EVT_MENU, set_sort_key(2), item)
        menu.AppendSeparator()

        def on_expand(flag):
            def exp_handler(event):
                tree = self.tree_library
                tree_root = tree.GetRootItem()
                child, cookie = tree.GetFirstChild(tree_root)
                while child.IsOk():
                    if local_flag:
                        tree.ExpandAllChildren(child)
                    else:
                        tree.CollapseAllChildren(child)
                    child, cookie = tree.GetNextChild(tree_root, cookie)

            local_flag = flag
            return exp_handler

        item = menu.Append(wx.ID_ANY, _("Expand all"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, on_expand(True), item)
        item = menu.Append(wx.ID_ANY, _("Collapse all"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, on_expand(False), item)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_preview_rightclick(self, event):
        # A couple of basic operations
        def max_keynum(secname):
            maxfound = 0
            for subsection in self.op_data.derivable(secname):
                parts = subsection.split(" ")
                number = parts[-1]
                try:
                    nr = int(number)
                    if nr > maxfound:
                        maxfound = nr
                except ValueError:
                    pass
            return maxfound

        def newkey():
            sect = self.active_material
            # fetch all section names...
            sect_num = max_keynum(sect) + 1
            section_name = f"{sect} {sect_num:0>6}"
            return section_name

        event.Skip()
        if self.active_material is None:
            return
        key = None
        try:
            # main click
            listindex = event.Index
            if listindex >= 0:
                index = self.list_preview.GetItemData(listindex)
                key = self.get_nth_operation(index)
        except AttributeError:
            # Column click
            pass

        menu = wx.Menu()

        def on_menu_popup_delete(op_section):
            def remove_handler(*args):
                settings = self.op_data
                # print (f"Remove {sect}")
                settings.clear_persistent(sect)
                self.fill_preview()

            sect = op_section
            return remove_handler

        def on_menu_popup_duplicate(op_section):
            def dup_handler(*args):
                settings = self.op_data
                # print (f"Remove {sect}")
                nkey = newkey()
                for info in settings.keylist(sect):
                    secdesc = settings.read_persistent(str, sect, info, "")
                    if info == "id":
                        continue
                    if info == "label":
                        idx = 0
                        if secdesc.endswith(")") and secdesc[-2] in (
                            str(i) for i in range(0, 10)
                        ):
                            i = secdesc.rfind("(")
                            if i >= 0:
                                try:
                                    s = secdesc[i + 1 :]
                                    t = secdesc[:i]
                                    idx = int(s[:-1])
                                    secdesc = t
                                except ValueError:
                                    pass
                        secdesc += f"({idx + 1})"
                    settings.write_persistent(nkey, info, secdesc)

                on_menu_popup_missing()
                settings.write_configuration()
                self.fill_preview()

            sect = op_section
            return dup_handler

        def on_menu_popup_newop(op_dict):
            def add_handler(*args):
                settings = self.op_data
                # print (f"Remove {sect}")
                nkey = newkey()
                for key, value in opd.items():
                    settings.write_persistent(nkey, key, value)

                on_menu_popup_missing()
                settings.write_configuration()
                self.fill_preview()

            opd = op_dict
            return add_handler

        def on_menu_popup_apply_to_tree(op_section):
            def apply_to_tree_handler(*args):
                settings = self.op_data
                op_type = settings.read_persistent(str, sect, "type")
                op_attr = dict()
                for key in settings.keylist(sect):
                    if key == "type":
                        # We need to ignore it to avoid double attribute issues.
                        continue
                    content = settings.read_persistent(str, sect, key)
                    op_attr[key] = content
                try:
                    targetop = Node().create(type=op_type, **op_attr)
                except ValueError:
                    # Attempted to create a non-bootstrapped node type.
                    return
                op_id = targetop.id
                if op_id is None:
                    # WTF, that should not be the case
                    op_list = [targetop]
                    self.context.elements.validate_ids(nodelist=op_list, generic=False)
                newone = True
                for op in self.context.elements.ops():
                    # Already existing?
                    if op.id == targetop.id:
                        newone = False
                        op_attr["type"] = targetop.type
                        op.replace_node(keep_children=True, **op_attr)
                        break
                if newone:
                    try:
                        self.context.elements.op_branch.add_node(targetop)
                    except ValueError:
                        # This happens when he have somehow lost sync with the node,
                        # and we try to add a node that is already added...
                        # In principle this should be covered by the check
                        # above, but you never know
                        pass
                self.context.signal("rebuild_tree")

            sect = op_section
            return apply_to_tree_handler

        def on_menu_popup_apply_to_statusbar(op_section):
            def apply_to_tree_handler(*args):
                settings = self.op_data
                op_type = settings.read_persistent(str, sect, "type")
                op_attr = dict()
                for key in settings.keylist(sect):
                    if key == "type":
                        # We need to ignore it to avoid double attribute issues.
                        continue
                    content = settings.read_persistent(str, sect, key)
                    op_attr[key] = content
                try:
                    targetop = Node().create(type=op_type, **op_attr)
                except ValueError:
                    # Attempted to create a non-bootstrapped node type.
                    return
                op_id = targetop.id
                if op_id is None:
                    # WTF, that should not be the case
                    op_list = [targetop]
                    self.context.elements.validate_ids(nodelist=op_list, generic=False)
                newone = True
                for idx, op in enumerate(self.context.elements.default_operations):
                    # Already existing?
                    if op.id == targetop.id:
                        newone = False
                        self.context.elements.default_operations[idx] = targetop
                        break
                if newone:
                    self.context.elements.default_operations.append(targetop)
                self.context.signal("default_operations")

            sect = op_section
            return apply_to_tree_handler

        def on_menu_popup_missing(*args):
            if self.active_material is None:
                return
            op_list, op_info = self.context.elements.load_persistent_op_list(
                self.active_material,
                use_settings=self.op_data,
            )
            if len(op_list) == 0:
                return
            changes = False
            # Which ones do we have already?
            replace_mk_pattern = True
            mkpattern = "meerk40t:"
            uid = list()
            for op in op_list:
                if not hasattr(op, "id"):
                    continue
                if not op.id:
                    continue
                if replace_mk_pattern and op.id.startswith(mkpattern):
                    continue
                uid.append(op.id)
            for op in op_list:
                if hasattr(op, "label") and op.label is None:
                    pattern = op.type
                    if pattern.startswith("op "):
                        pattern = pattern[3].upper() + pattern[4:]
                    s1 = ""
                    s2 = ""
                    if hasattr(op, "power"):
                        if op.power is None:
                            pwr = 1000
                        else:
                            pwr = op.power
                        s1 = f"{pwr/10.0:.0f}%"
                    if hasattr(op, "speed") and op.speed is not None:
                        s2 = f"{op.speed:.0f}mm/s"
                    if s1 or s2:
                        pattern += f" ({s1}{', ' if s1 and s2 else ''}{s2})"
                    op.label = pattern
                    changes = True
                replace_id = True
                if not hasattr(op, "id"):
                    # oldid = "unknown"
                    replace_id = False
                else:
                    # oldid = op.id
                    if op.id and not (
                        replace_mk_pattern and op.id.startswith(mkpattern)
                    ):
                        replace_id = False
                # print (oldid, replace_id)
                if replace_id:
                    # oldid = op.id
                    changes = True
                    if op.type.startswith("op "):
                        pattern = op.type[3].upper()
                    else:
                        pattern = op.type[0:2].upper()
                    idx = 1
                    while f"{pattern}{idx}" in uid:
                        idx += 1
                    op.id = f"{pattern}{idx}"
                    # print (f"{oldid} -> {op.id}")
                    uid.append(op.id)

            if changes:
                self.context.elements.save_persistent_operations_list(
                    self.active_material,
                    op_list,
                    op_info,
                    flush=False,
                    use_settings=self.op_data,
                )
                self.op_data.write_configuration()
                self.fill_preview()

        op_dict = {
            "type": "op raster",
            "speed": "140",
            "power": "1000",
            "label": "Raster",
            "color": "#000000",
        }
        if self.is_balor:
            op_dict["frequency"] = "35"
        item = menu.Append(wx.ID_ANY, _("Add Raster"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, on_menu_popup_newop(op_dict), item)
        op_dict = {
            "type": "op engrave",
            "speed": "50",
            "power": "1000",
            "label": "Engrave",
            "color": "#0000FF",
        }
        if self.is_balor:
            op_dict["frequency"] = "35"
        item = menu.Append(wx.ID_ANY, _("Add Engrave"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, on_menu_popup_newop(op_dict), item)
        op_dict = {
            "type": "op cut",
            "speed": "5",
            "power": "1000",
            "label": "Cut",
            "color": "#FF0000",
        }
        if self.is_balor:
            op_dict["frequency"] = "35"
        item = menu.Append(wx.ID_ANY, _("Add Cut"), "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, on_menu_popup_newop(op_dict), item)

        if key:
            menu.AppendSeparator()
            item = menu.Append(wx.ID_ANY, _("Duplicate"), "", wx.ITEM_NORMAL)
            self.Bind(wx.EVT_MENU, on_menu_popup_duplicate(key), item)
            item = menu.Append(wx.ID_ANY, _("Delete"), "", wx.ITEM_NORMAL)
            self.Bind(wx.EVT_MENU, on_menu_popup_delete(key), item)

            menu.AppendSeparator()

            item = menu.Append(wx.ID_ANY, _("Load into Tree"), "", wx.ITEM_NORMAL)
            self.Bind(wx.EVT_MENU, on_menu_popup_apply_to_tree(key), item)

            settings = self.op_data
            op_type = settings.read_persistent(str, key, "type")
            if op_type.startswith("op "):
                item = menu.Append(
                    wx.ID_ANY, _("Use for statusbar"), "", wx.ITEM_NORMAL
                )
                menu.Enable(item.GetId(), bool(self.active_material is not None))
                self.Bind(wx.EVT_MENU, on_menu_popup_apply_to_statusbar(key), item)

        if self.list_preview.GetItemCount() > 0:
            menu.AppendSeparator()

            item = menu.Append(
                wx.ID_ANY, _("Fill missing ids/label"), "", wx.ITEM_NORMAL
            )
            self.Bind(wx.EVT_MENU, on_menu_popup_missing, item)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_resize(self, event):
        size = self.GetClientSize()
        if size[0] != 0 and size[1] != 0:
            self.tree_library.SetMaxSize(wx.Size(-1, int(0.4 * size[1])))
            self.list_preview.SetMaxSize(wx.Size(-1, int(0.4 * size[1])))

        # Resize the columns in the listctrl
        size = self.list_preview.GetSize()
        if size[0] == 0 or size[1] == 0:
            return
        remaining = size[0] * 0.8
        # 0 "#"
        # 1 "Operation"
        # 2 "Id"
        # 3 "Label"
        # 4 "Power"
        # 5 "Speed"
        # 6 "Frequency"
        if self.is_balor:
            p1 = 0.15
            p2 = 0.35
            p3 = (1.0 - p1 - p2) / 4
            p4 = p3
        else:
            p1 = 0.15
            p2 = 0.40
            p3 = (1.0 - p1 - p2) / 3
            p4 = 0
        self.list_preview.SetColumnWidth(0, int(p3 * remaining))
        self.list_preview.SetColumnWidth(1, int(p1 * remaining))
        self.list_preview.SetColumnWidth(2, int(p1 * remaining))
        self.list_preview.SetColumnWidth(3, int(p2 * remaining))
        self.list_preview.SetColumnWidth(4, int(p3 * remaining))
        self.list_preview.SetColumnWidth(5, int(p3 * remaining))
        self.list_preview.SetColumnWidth(6, int(p4 * remaining))

    def before_operation_update(self, event):
        list_id = event.GetIndex()  # Get the current row
        if list_id < 0:
            event.Veto()
            return
        col_id = event.GetColumn()  # Get the current column
        ok = True
        try:
            index = self.list_preview.GetItemData(list_id)
            key = self.get_nth_operation(index)
            entry = self.operation_list[key]
            if not entry[0].startswith("op "):
                ok = False
        except (AttributeError, KeyError):
            ok = False
        if col_id not in range(2, 7):
            ok = False
        if col_id == 6 and not self.is_balor:
            ok = False
        if ok:
            event.Allow()
        else:
            event.Veto()

    def on_operation_update(self, event):
        list_id = event.GetIndex()  # Get the current row
        col_id = event.GetColumn()  # Get the current column
        new_data = event.GetLabel()  # Get the changed data
        index = self.list_preview.GetItemData(list_id)
        key = self.get_nth_operation(index)

        if list_id >= 0 and col_id in range(2, 7):
            if col_id == 2:
                # id
                self.op_data.write_persistent(key, "id", new_data)
            elif col_id == 3:
                # label
                self.op_data.write_persistent(key, "label", new_data)
            elif col_id == 4:
                # power
                self.op_data.write_persistent(key, "power", new_data)
            elif col_id == 5:
                # speed
                self.op_data.write_persistent(key, "speed", new_data)
            elif col_id == 6:
                # speed
                self.op_data.write_persistent(key, "frequency", new_data)
            # Set the new data in the listctrl
            self.op_data.write_configuration()

            self.list_preview.SetItem(list_id, col_id, new_data)

    def set_parent(self, par_panel):
        self.parent_panel = par_panel

    def pane_show(self):
        self.update_list(reload=True)

    def pane_hide(self):
        pass


class ImportPanel(wx.Panel):
    """
    Displays a how-to summary
    """

    def __init__(self, *args, context=None, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.context = context
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, wx.ID_ANY, "UNDER CONSTRUCTION")
        main_sizer.Add(label, 0, wx.EXPAND, 0)
        self.SetSizer(main_sizer)


class AboutPanel(wx.Panel):
    """
    Displays a how-to summary
    """

    def __init__(self, *args, context=None, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.context = context
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        info_box = StaticBoxSizer(self, wx.ID_ANY, _("How to use..."), wx.VERTICAL)
        self.parent_panel = None
        s = self.context.asset("material_howto")
        info_label = wx.TextCtrl(
            self, wx.ID_ANY, value=s, style=wx.TE_READONLY | wx.TE_MULTILINE
        )
        font = wx.Font(
            10,
            wx.FONTFAMILY_TELETYPE,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
        )
        info_label.SetFont(font)
        info_label.SetBackgroundColour(self.GetBackgroundColour())
        info_box.Add(info_label, 1, wx.EXPAND, 0)
        main_sizer.Add(info_box, 1, wx.EXPAND, 0)
        self.SetSizer(main_sizer)
        self.Layout()

    def set_parent(self, par_panel):
        self.parent_panel = par_panel


class MaterialManager(MWindow):
    def __init__(self, *args, **kwds):
        super().__init__(860, 800, *args, **kwds)

        self.panel_library = MaterialPanel(self, wx.ID_ANY, context=self.context)
        # self.panel_import = ImportPanel(self, wx.ID_ANY, context=self.context)
        self.panel_about = AboutPanel(self, wx.ID_ANY, context=self.context)

        self.panel_library.set_parent(self)
        # self.panel_import.set_parent(self)
        self.panel_about.set_parent(self)

        _icon = wx.NullIcon
        _icon.CopyFromBitmap(icon_library.GetBitmap())
        self.SetIcon(_icon)
        self.notebook_main = wx.aui.AuiNotebook(
            self,
            -1,
            style=wx.aui.AUI_NB_TAB_EXTERNAL_MOVE
            | wx.aui.AUI_NB_SCROLL_BUTTONS
            | wx.aui.AUI_NB_TAB_SPLIT
            | wx.aui.AUI_NB_TAB_MOVE,
        )
        self.sizer.Add(self.notebook_main, 1, wx.EXPAND, 0)
        self.notebook_main.AddPage(self.panel_library, _("Library"))
        # self.notebook_main.AddPage(self.panel_import, _("Import"))
        self.notebook_main.AddPage(self.panel_about, _("How to use"))
        # begin wxGlade: Keymap.__set_properties
        self.DragAcceptFiles(True)
        self.Bind(wx.EVT_DROP_FILES, self.on_drop_file)
        self.SetTitle(_("Material Library"))
        self.restore_aspect(honor_initial_values=True)

    def on_drop_file(self, event):
        """
        Drop file handler
        Accepts only a single file drop.
        """
        for pathname in event.GetFiles():
            self.panel_library.on_import(None, filename=pathname)
            break

    def delegates(self):
        yield self.panel_library
        # yield self.panel_import
        yield self.panel_about

    @staticmethod
    def sub_register(kernel):
        kernel.register(
            "button/config/Material",
            {
                "label": _("Material Library"),
                "icon": icon_library,
                "tip": _("Manages Material Settings"),
                "help": "materialmanager",
                "action": lambda v: kernel.console("window toggle MatManager\n"),
            },
        )

    def window_open(self):
        pass

    def window_close(self):
        pass

    def edit_message(self, msg):
        self.panel_library.edit_message(msg)

    def populate_gui(self):
        self.panel_library.populate_gui()

    @staticmethod
    def submenu():
        # Suppress to avoid double menu-appearance
        return "", "Material Library", True
