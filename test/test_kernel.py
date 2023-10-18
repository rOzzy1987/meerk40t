import unittest
from test import bootstrap


class TestKernel(unittest.TestCase):
    def test_kernel_commands(self):
        """
        Tests all commands with no arguments to test for crashes...
        """
        kernel = bootstrap.bootstrap()
        try:
            for cmd, path, command in kernel.find("command/.*"):
                if "server" in command:
                    continue
                if "ruida" in command:
                    continue
                if "grbl" in command:
                    continue
                if "usb_" in command:
                    continue
                if command in (
                    "quit",
                    "shutdown",
                    "interrupt",
                    "+laser",
                    "-laser",
                    "left",
                    "right",
                    "top",
                    "bottom",
                    "home",
                    "unlock",
                    "lock",
                    "physical_home",
                    "test_dot_and_home",
                ):
                    continue
                if not cmd.regex:
                    print(f"Testing command: {command}")
                    # command should be generated with something like
                    # kernel.console(" ".join(command.split("/")[1:]) + "\n")
                    # if first parameter is not base but this fails so not
                    # changing yet
                    kernel.console(command.split("/")[-1] + "\n")
        finally:
            kernel.shutdown()

    def test_tree_menu(self):
        """
        Tests all commands with no arguments to test for crashes...
        """
        from meerk40t.core.treeop import tree_operations_for_node
        from PIL import Image
        image = Image.new("RGBA", (256, 256))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        draw.ellipse((0, 0, 255, 255), "black")
        image = image.convert("L")

        kwargs_nodes = (

            {"type": "elem ellipse", "center": 0j, "r": 10000},
            {"type": "elem image", "image": image, "dpi": 500},
            {"type": "elem path", "d": "M0,0L10000,10000"},
            {"type": "elem point", "x": 0, "y": 0},
            {"type": "elem polyline", "points": (0j, 10000j, )},
            {"type": "elem rect", "x": 0, "y": 0, "width": 10000, "height": 20000},
            {"type": "elem line","x1": 0, "y1": 0, "x2": 20000, "y2": 20000},
            {"type": "elem text", "text": "Hello World."},
        )
        kernel = bootstrap.bootstrap()
        try:
            for kws in kwargs_nodes:
                print(f"Creating: {kws.get('type')}")
                n = kernel.elements.elem_branch.add(**kws)
                print(n)

                nodes = tree_operations_for_node(kernel.elements, n)
                for func in nodes:
                    func_dict = dict(func.func_dict)
                    print(f"Executing: {func.name}")
                    func(n, **func_dict)
        finally:
            kernel.console("elements\n")
            kernel.shutdown()

    def test_external_plugins(self):
        """
        This tests the functionality of external plugins which typically ran pkg_resources but was switched to
        importlib on the release of python 3.12. This code functions if and only if no crash happens.

        @return:
        """
        class Args:
            no_plugins = False

        kernel = bootstrap.bootstrap()
        kernel.args = Args()
        try:
            from meerk40t.external_plugins import plugin
            q = plugin(kernel=kernel, lifecycle="plugins")
            print(q)
        finally:
            kernel.shutdown()

    def test_kernel_reload_devices(self):
        """
        We start a new bootstrap, delete any services that would have existed previously. Add 1 service and also have
        the default service added by default.
        @return:
        """
        kernel = bootstrap.bootstrap(profile="MeerK40t_REBOOT")
        try:
            for i in range(10):
                kernel.console(f"service device destroy {i}\n")
            kernel.console("service device start -i lhystudios 0\n")
            kernel.console("service device start -i lhystudios 1\n")
            kernel.console("service device start -i lhystudios 2\n")
            kernel.console("service list\n")
            kernel.console("contexts\n")
            kernel.console("plugins\n")
        finally:
            kernel.shutdown()

        kernel = bootstrap.bootstrap(profile="MeerK40t_REBOOT")
        try:
            devs = [name for name in kernel.contexts if name.startswith("lhystudios")]
            self.assertGreater(len(devs), 1)
        finally:
            kernel.shutdown()


class TestGetSafePath(unittest.TestCase):
    def test_get_safe_path(self):
        import os

        from meerk40t.kernel import get_safe_path

        """
        Tests the get_safe_path method for all o/ses
        """
        sep = os.sep
        self.assertEqual(
            str(get_safe_path("test", system="Darwin")),
            (
                os.path.expanduser("~")
                + sep
                + "Library"
                + sep
                + "Application Support"
                + sep
                + "test"
            ),
        )
        self.assertEqual(
            str(get_safe_path("test", system="Windows")),
            (os.path.expandvars("%LOCALAPPDATA%") + sep + "test"),
        )
        self.assertEqual(
            str(get_safe_path("test", system="Linux")),
            (os.path.expanduser("~") + sep + ".config" + sep + "test"),
        )


class TestEchoCommand(unittest.TestCase):
    def test_echo_and_ansi(self):
        """
        Tests all echo options separately and combined
        with output to ansi terminal window
        """
        echo_commands = [
            "echo",
            "echo [bg-white][black] black text",
            "echo [red] red text",
            "echo [green] green text",
            "echo [yellow] yellow text",
            "echo [blue] blue text",
            "echo [magenta] magenta text",
            "echo [cyan] cyan text",
            "echo [bg-black][white] white text",
            "echo [bg-black][white] black background",
            "echo [bg-red] red background",
            "echo [bg-green] green background",
            "echo [bg-yellow] yellow background",
            "echo [bg-blue] blue background",
            "echo [bg-magenta] magenta background",
            "echo [bg-cyan] cyan background",
            "echo [bg-white][black] white background",
            "echo [bg-white][black] bright black text",
            "echo [bold][red] bright red text",
            "echo [bold][green] bright green text",
            "echo [bold][yellow] bright yellow text",
            "echo [bold][blue] bright blue text",
            "echo [bold][magenta] bright magenta text",
            "echo [bold][cyan] bright cyan text",
            "echo [bold][bg-black][white] bright white text",
            "echo [bold] bold text [/bold] normal text",
            "echo [italic] italic text [/italic] normal text",
            "echo [underline] underline text [/underline] normal text",
            "echo [underscore] underscore text [/underscore] normal text",
            "echo [negative] negative text [positive] positive text",
            "echo [negative] negative text [normal] normal text",
            "echo [raw][red] red bbcode and normal text",
        ]

        kernel = bootstrap.bootstrap()
        try:
            for echo in echo_commands:
                print(f"Testing echo command: {echo}")
                kernel.console(echo + "\n")
        finally:
            kernel.shutdown()
