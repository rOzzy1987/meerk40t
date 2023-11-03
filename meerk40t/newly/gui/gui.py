def plugin(service, lifecycle):
    if lifecycle == "service":
        return "provider/device/newly"
    if lifecycle == "invalidate":
        return not service.has_feature("wx")
    if lifecycle == "added":
        # Needed to test wx import.
        import wx  # pylint: disable=unused-import

        from meerk40t.gui.icons import icons8_computer_support, icons8_connected

        from .newlyconfig import NewlyConfiguration
        from .newlycontroller import NewlyController

        # from .operationproperties import NewlyOperationPanel

        service.register("window/Controller", NewlyController)
        service.register("window/Configuration", NewlyConfiguration)

        service.register("winpath/Controller", service)
        service.register("winpath/Configuration", service)

        _ = service.kernel.translation

        service.register(
            "button/control/Controller",
            {
                "label": _("Controller"),
                "icon": icons8_connected,
                "tip": _("Opens Controller Window"),
                "action": lambda e: service("window toggle Controller\n"),
            },
        )
        service.register(
            "button/device/Configuration",
            {
                "label": _("Config"),
                "icon": icons8_computer_support,
                "tip": _("Opens device-specific configuration window"),
                "action": lambda v: service("window toggle Configuration\n"),
            },
        )

    if lifecycle == "service_attach":
        from meerk40t.gui.icons import (
            icon_mk_rectangular,
            icons8_circled_play,
            icons8_circled_stop,
            icons8_computer_support,
            icons8_connected,
            icons8_file,
            icons8_move,
            icons8_circled_play,
        )

        _ = service.kernel.translation
        selected = service.setting(int, "file_index", 1)
        autoplay = service.setting(bool, "autoplay", True)
        service.register(
            "button/control/SelectFile",
            {
                "label": _("File {index}").format(index=selected),
                "icon": icons8_file,
                "tip": _("Select active file to use for machine."),
                "identifier": "file_index",
                "object": service,
                "priority": 1,
                "multi": [
                    {
                        "identifier": 1,
                        "label": _("File {index}").format(index=1),
                        "tip": _("File {index}").format(index=1),
                        "action": lambda v: service("select_file 1\n"),
                    },
                    {
                        "identifier": 2,
                        "label": _("File {index}").format(index=2),
                        "tip": _("File {index}").format(index=2),
                        "action": lambda v: service("select_file 2\n"),
                    },
                    {
                        "identifier": 3,
                        "label": _("File {index}").format(index=3),
                        "tip": _("File {index}").format(index=3),
                        "action": lambda v: service("select_file 3\n"),
                    },
                    {
                        "identifier": 4,
                        "label": _("File {index}").format(index=4),
                        "tip": _("File {index}").format(index=4),
                        "action": lambda v: service("select_file 4\n"),
                    },
                    {
                        "identifier": 5,
                        "label": _("File {index}").format(index=5),
                        "tip": _("File {index}").format(index=5),
                        "action": lambda v: service("select_file 5\n"),
                    },
                    {
                        "identifier": 6,
                        "label": _("File {index}").format(index=6),
                        "tip": _("File {index}").format(index=6),
                        "action": lambda v: service("select_file 6\n"),
                    },
                    {
                        "identifier": 7,
                        "label": _("File {index}").format(index=7),
                        "tip": _("File {index}").format(index=7),
                        "action": lambda v: service("select_file 7\n"),
                    },
                    {
                        "identifier": 8,
                        "label": _("File {index}").format(index=8),
                        "tip": _("File {index}").format(index=8),
                        "action": lambda v: service("select_file 8\n"),
                    },
                    {
                        "identifier": 9,
                        "label": _("File {index}").format(index=9),
                        "tip": _("File {index}").format(index=9),
                        "action": lambda v: service("select_file 9\n"),
                    },
                ],
            },
        )
        service.register(
            "button/control/AutoStart",
            {
                "label": _("Send Only"),
                "icon": icons8_circled_stop,
                "tip": _("Send the file but do not start the file"),
                "toggle_attr": "autoplay",
                "object": service,
                "priority": 1,
                "toggle": {
                    "label": _("Send & Start"),
                    "tip": _("Automatically start the device after send"),
                    "icon": icons8_circled_play,
                    "signal": "autoplay",
                },
            },
        )
        service.register(
            "button/control/DrawFrame",
            {
                "label": _("Draw Frame"),
                "icon": icon_mk_rectangular,
                "tip": _(
                    "Draw a bounding rectangle of the object saved in the machine"
                ),
                "action": lambda v: service(
                    "draw_frame {index}\n".format(index=service.file_index)
                ),
                "priority": 3,
            },
        )
        service.register(
            "button/control/MoveFrame",
            {
                "label": _("Move Frame"),
                "icon": icons8_move,
                "tip": _(
                    "Move the bounding rectangle of the object saved in the machine"
                ),
                "action": lambda v: service(
                    "move_frame {index}\n".format(index=service.file_index)
                ),
                "priority": 4,
            },
        )
        service.register(
            "button/control/Replay",
            {
                "label": _("Replay"),
                "icon": icons8_circled_play,
                "tip": _("Replay the file saved in the machine"),
                "action": lambda v: service(
                    "replay {index}\n".format(index=service.file_index)
                ),
                "priority": 5,
            },
        )
        service.add_service_delegate(NewlyGui(service))


class NewlyGui:
    # Class stub.
    def __init__(self, context):
        self.context = context
