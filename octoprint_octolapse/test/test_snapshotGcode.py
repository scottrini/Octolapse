import unittest
from tempfile import NamedTemporaryFile

from octoprint_octolapse.extruder import Extruder
from octoprint_octolapse.gcode import SnapshotGcodeGenerator
from octoprint_octolapse.settings import OctolapseSettings


class TestSnapshotGcode(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
        self.Extruder = Extruder(self.Settings)

    def tearDown(self):
        del self.Settings
        del self.Extruder

    @staticmethod
    def create_octoprint_printer_profile():
        return dict(
            volume=dict(
                width=250,
                depth=200,
                height=200,
                formFactor="Not A Circle",
                custom_box=False,
            )
        )

    def test_GetSnapshotPosition_Absolute(self):
        """Test getting absolute snapshot positions for x and y"""
        # adjust the settings for absolute position and create the snapshot gcode generator
        self.Settings.current_stabilization().x_type = "fixed_coordinate"
        self.Settings.current_stabilization().x_fixed_coordinate = 10
        self.Settings.current_stabilization().y_type = "fixed_coordinate"
        self.Settings.current_stabilization().y_fixed_coordinate = 20
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())

        # get the coordinates and test
        coords = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coords["X"] == 10 and coords["Y"] == 20)
        # get the coordinates and test
        coords = snapshot_gcode_generator.get_snapshot_position(1, 1)
        self.assertTrue(coords["X"] == 10 and coords["Y"] == 20)
        # get the coordinates and test
        coords = snapshot_gcode_generator.get_snapshot_position(100, 100)
        self.assertTrue(coords["X"] == 10 and coords["Y"] == 20)

    def test_GetSnapshotPosition_AbsolutePath(self):
        """Test getting absolute path snapshot positions for x and y"""
        # adjust the settings for absolute position and create the snapshot gcode generator
        self.Settings.current_stabilization().x_type = "fixed_path"
        self.Settings.current_stabilization().x_fixed_path = "0,1,2,3,4,5"
        self.Settings.current_stabilization().y_type = "fixed_path"
        self.Settings.current_stabilization().y_fixed_path = "5,4,3,2,1,0"

        # test with no loop
        self.Settings.current_stabilization().x_fixed_path_loop = False
        self.Settings.current_stabilization().x_fixed_path_invert_loop = False
        self.Settings.current_stabilization().y_fixed_path_loop = False
        self.Settings.current_stabilization().y_fixed_path_invert_loop = False
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 0 and coordinates["Y"] == 5)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 1 and coordinates["Y"] == 4)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 0)
        self.assertTrue(coordinates["X"] == 2 and coordinates["Y"] == 3)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 1)
        self.assertTrue(coordinates["X"] == 3 and coordinates["Y"] == 2)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 1)
        self.assertTrue(coordinates["X"] == 4 and coordinates["Y"] == 1)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 5 and coordinates["Y"] == 0)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 5 and coordinates["Y"] == 0)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 5 and coordinates["Y"] == 0)

        # test with loop, no invert
        self.Settings.current_stabilization().x_fixed_path_loop = True
        self.Settings.current_stabilization().x_fixed_path_invert_loop = False
        self.Settings.current_stabilization().y_fixed_path_loop = True
        self.Settings.current_stabilization().y_fixed_path_invert_loop = False
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 0 and coordinates["Y"] == 5)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 1 and coordinates["Y"] == 4)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 0)
        self.assertTrue(coordinates["X"] == 2 and coordinates["Y"] == 3)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 1)
        self.assertTrue(coordinates["X"] == 3 and coordinates["Y"] == 2)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 1)
        self.assertTrue(coordinates["X"] == 4 and coordinates["Y"] == 1)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 5 and coordinates["Y"] == 0)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 0 and coordinates["Y"] == 5)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 1 and coordinates["Y"] == 4)

        # test with loop and invert
        self.Settings.current_stabilization().x_fixed_path_loop = True
        self.Settings.current_stabilization().x_fixed_path_invert_loop = True
        self.Settings.current_stabilization().y_fixed_path_loop = True
        self.Settings.current_stabilization().y_fixed_path_invert_loop = True
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 0 and coordinates["Y"] == 5)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 1 and coordinates["Y"] == 4)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 0)
        self.assertTrue(coordinates["X"] == 2 and coordinates["Y"] == 3)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 1)
        self.assertTrue(coordinates["X"] == 3 and coordinates["Y"] == 2)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 1)
        self.assertTrue(coordinates["X"] == 4 and coordinates["Y"] == 1)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 5 and coordinates["Y"] == 0)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 4 and coordinates["Y"] == 1)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 3 and coordinates["Y"] == 2)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 2 and coordinates["Y"] == 3)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 1 and coordinates["Y"] == 4)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 0 and coordinates["Y"] == 5)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 1 and coordinates["Y"] == 4)

    def test_GetSnapshotPosition_BedRelative(self):
        """Test getting bed relative snapshot positions for x and y"""
        # adjust the settings for absolute position and create the snapshot gcode generator
        self.Settings.current_stabilization().x_type = "relative"
        self.Settings.current_stabilization().x_relative = 0
        self.Settings.current_stabilization().y_type = "relative"
        self.Settings.current_stabilization().y_relative = 100
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())

        # get the coordinates and test
        coords = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coords["X"] == 0 and coords["Y"] == 200)
        # get the coordinates and test
        coords = snapshot_gcode_generator.get_snapshot_position(1, 1)
        self.assertTrue(coords["X"] == 0 and coords["Y"] == 200)
        # get the coordinates and test
        coords = snapshot_gcode_generator.get_snapshot_position(100, 100)
        self.assertTrue(coords["X"] == 0 and coords["Y"] == 200)

    def test_GetSnapshotPosition_BedRelativePath(self):
        """Test getting bed relative path snapshot positions for x and y"""
        # adjust the settings for absolute position and create the snapshot gcode generator
        self.Settings.current_stabilization().x_type = "relative_path"
        self.Settings.current_stabilization().x_relative_path = "0,25,50,75,100"
        self.Settings.current_stabilization().y_type = "relative_path"
        self.Settings.current_stabilization().y_relative_path = "100,75,50,25,0"

        # test with no loop
        self.Settings.current_stabilization().x_relative_path_loop = False
        self.Settings.current_stabilization().x_relative_path_invert_loop = False
        self.Settings.current_stabilization().y_relative_path_loop = False
        self.Settings.current_stabilization().y_relative_path_invert_loop = False
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 0 and coordinates["Y"] == 200)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 62.5 and coordinates["Y"] == 150)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 0)
        self.assertTrue(coordinates["X"] == 125 and coordinates["Y"] == 100)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 1)
        self.assertTrue(coordinates["X"] == 187.5 and coordinates["Y"] == 50)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 1)
        self.assertTrue(coordinates["X"] == 250 and coordinates["Y"] == 0)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 250 and coordinates["Y"] == 0)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 250 and coordinates["Y"] == 0)

        # test with loop, no invert
        self.Settings.current_stabilization().x_relative_path_loop = True
        self.Settings.current_stabilization().x_relative_path_invert_loop = False
        self.Settings.current_stabilization().y_relative_path_loop = True
        self.Settings.current_stabilization().y_relative_path_invert_loop = False
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 0 and coordinates["Y"] == 200)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 62.5 and coordinates["Y"] == 150)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 0)
        self.assertTrue(coordinates["X"] == 125 and coordinates["Y"] == 100)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 1)
        self.assertTrue(coordinates["X"] == 187.5 and coordinates["Y"] == 50)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 1)
        self.assertTrue(coordinates["X"] == 250 and coordinates["Y"] == 0)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 0 and coordinates["Y"] == 200)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 62.5 and coordinates["Y"] == 150)

        # test with loop and invert
        self.Settings.current_stabilization().x_relative_path_loop = True
        self.Settings.current_stabilization().x_relative_path_invert_loop = True
        self.Settings.current_stabilization().y_relative_path_loop = True
        self.Settings.current_stabilization().y_relative_path_invert_loop = True
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 0 and coordinates["Y"] == 200)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 62.5 and coordinates["Y"] == 150)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 0)
        self.assertTrue(coordinates["X"] == 125 and coordinates["Y"] == 100)
        coordinates = snapshot_gcode_generator.get_snapshot_position(1, 1)
        self.assertTrue(coordinates["X"] == 187.5 and coordinates["Y"] == 50)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 1)
        self.assertTrue(coordinates["X"] == 250 and coordinates["Y"] == 0)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 187.5 and coordinates["Y"] == 50)
        coordinates = snapshot_gcode_generator.get_snapshot_position(0, 0)
        self.assertTrue(coordinates["X"] == 125 and coordinates["Y"] == 100)

    def test_GetSnapshotGcode_Fixed_AbsoluteCoordintes_ExtruderRelative(self):
        """Test snapshot gcode in absolute coordinate system with relative extruder and fixed coordinate
        stabilization """
        # adjust the settings for absolute position and create the snapshot gcode generator
        self.Settings.current_stabilization().x_type = "fixed_coordinate"
        self.Settings.current_stabilization().x_fixed_coordinate = 10
        self.Settings.current_stabilization().y_type = "fixed_coordinate"
        self.Settings.current_stabilization().y_fixed_coordinate = 20
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        self.Extruder.is_retracted = lambda: True
        snapshot_gcode = snapshot_gcode_generator.create_snapshot_gcode(
            0, 0, 0, 3600, False, True, self.Extruder, 0.5, "SavedCommand")
        # verify the created gcode
        self.assertEqual(snapshot_gcode.GcodeCommands[0], "G91")
        self.assertEqual(snapshot_gcode.GcodeCommands[1], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[2], "G1 Z0.500")
        self.assertEqual(snapshot_gcode.GcodeCommands[3], "G90")
        self.assertEqual(snapshot_gcode.GcodeCommands[4], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[5], "G1 X10.000 Y20.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[6], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[7], "M114")
        self.assertEqual(snapshot_gcode.GcodeCommands[8], "G1 X0.000 Y0.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[9], "G91")
        self.assertEqual(snapshot_gcode.GcodeCommands[10], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[11], "G1 Z-0.500")
        self.assertEqual(snapshot_gcode.GcodeCommands[12], "G90")
        self.assertEqual(snapshot_gcode.GcodeCommands[13], "G1 F3600")
        self.assertEqual(snapshot_gcode.GcodeCommands[14], "SAVEDCOMMAND")
        self.assertEqual(snapshot_gcode.GcodeCommands[15], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[16], "M114")
        # verify the indexes of the generated gcode
        self.assertEqual(snapshot_gcode.SnapshotIndex, 7)
        self.assertEqual(snapshot_gcode.end_index(), 16)
        # verify the return coordinates
        self.assertEqual(snapshot_gcode.ReturnX, 0)
        self.assertEqual(snapshot_gcode.ReturnY, 0)
        self.assertEqual(snapshot_gcode.ReturnZ, 0)

    def test_GetSnapshotGcode_RelativePath_RelativeCoordinates_ExtruderAbsolute_ZHop_Retraction(self):
        # test with relative paths, absolute extruder coordinates, retract and z hop
        # use relative coordinates for stabilizations
        self.Settings.current_stabilization().x_type = "relative_path"
        self.Settings.current_stabilization().x_relative_path = "50,100"  # 125,250
        self.Settings.current_stabilization().x_relative_path_loop = False
        self.Settings.current_stabilization().x_relative_path_invert_loop = False
        self.Settings.current_stabilization().y_type = "relative_path"
        self.Settings.current_stabilization().y_relative_path = "50,100"  # 100,200
        self.Settings.current_stabilization().y_relative_path_loop = False
        self.Settings.current_stabilization().y_relative_path_invert_loop = False
        self.Settings.current_snapshot().retract_before_move = True
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())

        snapshot_gcode = snapshot_gcode_generator.create_snapshot_gcode(
            10, 10, 10, 3600, True, False, self.Extruder, 0.5, "SavedCommand")
        # verify the created gcode
        self.assertEqual(snapshot_gcode.GcodeCommands[0], "M83")
        self.assertEqual(snapshot_gcode.GcodeCommands[1], "G1 F4000")
        self.assertEqual(snapshot_gcode.GcodeCommands[2], "G1 E-2.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[3], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[4], "G1 Z0.500")
        self.assertEqual(snapshot_gcode.GcodeCommands[5], "G90")
        self.assertEqual(snapshot_gcode.GcodeCommands[6], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[7], "G1 X125.000 Y100.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[8], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[9], "M114")
        self.assertEqual(snapshot_gcode.GcodeCommands[10], "G1 X10.000 Y10.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[11], "G91")
        self.assertEqual(snapshot_gcode.GcodeCommands[12], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[13], "G1 Z-0.500")
        self.assertEqual(snapshot_gcode.GcodeCommands[14], "G1 F3000")
        self.assertEqual(snapshot_gcode.GcodeCommands[15], "G1 E2.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[16], "M82")
        self.assertEqual(snapshot_gcode.GcodeCommands[17], "G1 F3600")
        self.assertEqual(snapshot_gcode.GcodeCommands[18], "SAVEDCOMMAND")
        self.assertEqual(snapshot_gcode.GcodeCommands[19], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[20], "M114")

        # verify the indexes of the generated gcode
        self.assertTrue(snapshot_gcode.SnapshotIndex == 9)
        self.assertTrue(snapshot_gcode.end_index() == 20)
        # verify the return coordinates
        self.assertTrue(snapshot_gcode.ReturnX == 10)
        self.assertTrue(snapshot_gcode.ReturnY == 10)
        self.assertTrue(snapshot_gcode.ReturnZ == 10)

    def test_GetSnapshotGcode_FixedPath_RelativeCoordinates_ExtruderAbsolute_ZHop_AlreadyRetracted(self):
        # test with relative paths, absolute extruder coordinates, retract and z hop
        # use relative coordinates for stabilizations
        self.Settings.current_stabilization().x_type = "fixed_path"
        self.Settings.current_stabilization().x_fixed_path = "50,100"  # 125,250
        self.Settings.current_stabilization().x_fixed_path_loop = False
        self.Settings.current_stabilization().x_fixed_path_invert_loop = False
        self.Settings.current_stabilization().y_type = "fixed_path"
        self.Settings.current_stabilization().y_fixed_path = "50,100"  # 100,200
        self.Settings.current_stabilization().y_fixed_path_loop = False
        self.Settings.current_stabilization().y_fixed_path_invert_loop = False
        self.Settings.current_snapshot().retract_before_move = True
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        self.Extruder.is_retracted = lambda: True
        snapshot_gcode = snapshot_gcode_generator.create_snapshot_gcode(
            100, 50, 0, 3600, True, False, self.Extruder, 0.5, "SavedCommand")
        # verify the created gcode
        self.assertEqual(snapshot_gcode.GcodeCommands[0], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[1], "G1 Z0.500")
        self.assertEqual(snapshot_gcode.GcodeCommands[2], "G90")
        self.assertEqual(snapshot_gcode.GcodeCommands[3], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[4], "G1 X50.000 Y50.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[5], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[6], "M114")
        self.assertEqual(snapshot_gcode.GcodeCommands[7], "G1 X100.000 Y50.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[8], "G91")
        self.assertEqual(snapshot_gcode.GcodeCommands[9], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[10], "G1 Z-0.500")
        self.assertEqual(snapshot_gcode.GcodeCommands[11], "G1 F3600")
        self.assertEqual(snapshot_gcode.GcodeCommands[12], "SAVEDCOMMAND")
        self.assertEqual(snapshot_gcode.GcodeCommands[13], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[14], "M114")

        # verify the indexes of the generated gcode
        self.assertEqual(snapshot_gcode.SnapshotIndex, 6)
        self.assertEqual(snapshot_gcode.end_index(), 14)
        # verify the return coordinates
        self.assertEqual(snapshot_gcode.ReturnX, 100)
        self.assertEqual(snapshot_gcode.ReturnY, 50)
        self.assertEqual(snapshot_gcode.ReturnZ, 0)

        # Get the next coordinate in the path
        snapshot_gcode = snapshot_gcode_generator.create_snapshot_gcode(
            101, 51, 0, 3600, True, False, self.Extruder, 0.5, "SavedCommand")
        # verify the created gcode
        self.assertEqual(snapshot_gcode.GcodeCommands[0], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[1], "G1 Z0.500")
        self.assertEqual(snapshot_gcode.GcodeCommands[2], "G90")
        self.assertEqual(snapshot_gcode.GcodeCommands[3], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[4], "G1 X100.000 Y100.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[5], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[6], "M114")
        self.assertEqual(snapshot_gcode.GcodeCommands[7], "G1 X101.000 Y51.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[8], "G91")
        self.assertEqual(snapshot_gcode.GcodeCommands[9], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[10], "G1 Z-0.500")
        self.assertEqual(snapshot_gcode.GcodeCommands[11], "G1 F3600")
        self.assertEqual(snapshot_gcode.GcodeCommands[12], "SAVEDCOMMAND")
        self.assertEqual(snapshot_gcode.GcodeCommands[13], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[14], "M114")

        # verify the indexes of the generated gcode
        self.assertEqual(snapshot_gcode.SnapshotIndex, 6)
        self.assertEqual(snapshot_gcode.end_index(), 14)
        # verify the return coordinates
        self.assertEqual(snapshot_gcode.ReturnX, 101)
        self.assertEqual(snapshot_gcode.ReturnY, 51)
        self.assertEqual(snapshot_gcode.ReturnZ, 0)

    def test_GetSnapshotGcode_Relative_RelativeCoordinates_AbsoluteExtruder_ZhopTooHigh(self):
        """Test snapshot gcode with relative stabilization, relative coordinates, absolute extruder, z is too high to
        hop, no retraction """

        # test with relative coordinates, absolute extruder coordinates, z hop impossible (current z height will not
        # allow this since it puts things outside of the bounds) use relative coordinates for stabilizations
        self.Settings.current_stabilization().x_type = "relative"
        self.Settings.current_stabilization().x_relative = 50  # 125
        self.Settings.current_stabilization().y_type = "relative"
        self.Settings.current_stabilization().y_relative = 100  # 200
        self.Settings.current_snapshot().retract_before_move = False
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        # create
        snapshot_gcode = snapshot_gcode_generator.create_snapshot_gcode(
            10, 10, 200, 3600, True, False, self.Extruder, 0.5, "SavedCommand")
        # verify the created gcode
        self.assertEqual(snapshot_gcode.GcodeCommands[0], "G90")
        self.assertEqual(snapshot_gcode.GcodeCommands[1], "G1 F6000")
        self.assertEqual(snapshot_gcode.GcodeCommands[2], "G1 X125.000 Y200.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[3], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[4], "M114")
        self.assertEqual(snapshot_gcode.GcodeCommands[5], "G1 X10.000 Y10.000")
        self.assertEqual(snapshot_gcode.GcodeCommands[6], "G91")
        self.assertEqual(snapshot_gcode.GcodeCommands[7], "G1 F3600")
        self.assertEqual(snapshot_gcode.GcodeCommands[8], "SAVEDCOMMAND")
        self.assertEqual(snapshot_gcode.GcodeCommands[9], "M400")
        self.assertEqual(snapshot_gcode.GcodeCommands[10], "M114")

        # verify the indexes of the generated gcode
        self.assertTrue(snapshot_gcode.SnapshotIndex == 4)
        self.assertTrue(snapshot_gcode.end_index() == 10)
        # verify the return coordinates
        self.assertTrue(snapshot_gcode.ReturnX == 10)
        self.assertTrue(snapshot_gcode.ReturnY == 10)
        self.assertTrue(snapshot_gcode.ReturnZ == 200)

    def test_GetSnapshotGcode_SnapshotCommands(self):
        # test with relative paths, absolute extruder coordinates, retract and z hop
        # use relative coordinates for stabilizations
        self.Settings.current_stabilization().x_type = "fixed_path"
        self.Settings.current_stabilization().x_fixed_path = "50,100"  # 125,250
        self.Settings.current_stabilization().x_fixed_path_loop = False
        self.Settings.current_stabilization().x_fixed_path_invert_loop = False
        self.Settings.current_stabilization().y_type = "fixed_path"
        self.Settings.current_stabilization().y_fixed_path = "50,100"  # 100,200
        self.Settings.current_stabilization().y_fixed_path_loop = False
        self.Settings.current_stabilization().y_fixed_path_invert_loop = False
        self.Settings.current_snapshot().retract_before_move = True
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        self.Extruder.is_retracted = lambda: True
        snapshot_gcode = snapshot_gcode_generator.create_snapshot_gcode(
            100, 50, 0, 3600, True, False, self.Extruder, 0.5, "SavedCommand")

        # verify the snapshot commands
        self.assertEqual(snapshot_gcode.get_snapshot_commands()[0], "G1 F6000")
        self.assertEqual(snapshot_gcode.get_snapshot_commands()[1], "G1 Z0.500")
        self.assertEqual(snapshot_gcode.get_snapshot_commands()[2], "G90")
        self.assertEqual(snapshot_gcode.get_snapshot_commands()[3], "G1 F6000")
        self.assertEqual(snapshot_gcode.get_snapshot_commands()[4], "G1 X50.000 Y50.000")
        self.assertEqual(snapshot_gcode.get_snapshot_commands()[5], "M400")
        self.assertEqual(snapshot_gcode.get_snapshot_commands()[6], "M114")

    def test_GetSnapshotGcode_ReturnCommands(self):
        # test with relative paths, absolute extruder coordinates, retract and z hop
        # use relative coordinates for stabilizations
        self.Settings.current_stabilization().x_type = "fixed_path"
        self.Settings.current_stabilization().x_fixed_path = "50,100"  # 125,250
        self.Settings.current_stabilization().x_fixed_path_loop = False
        self.Settings.current_stabilization().x_fixed_path_invert_loop = False
        self.Settings.current_stabilization().y_type = "fixed_path"
        self.Settings.current_stabilization().y_fixed_path = "50,100"  # 100,200
        self.Settings.current_stabilization().y_fixed_path_loop = False
        self.Settings.current_stabilization().y_fixed_path_invert_loop = False
        self.Settings.current_snapshot().retract_before_move = True
        snapshot_gcode_generator = SnapshotGcodeGenerator(
            self.Settings, self.create_octoprint_printer_profile())
        self.Extruder.is_retracted = lambda: True
        snapshot_gcode = snapshot_gcode_generator.create_snapshot_gcode(
            100, 50, 0, 3600, True, False, self.Extruder, 0.5, "SavedCommand")

        # verify the return commands
        self.assertEqual(snapshot_gcode.get_return_commands()[0], "G1 X100.000 Y50.000")
        self.assertEqual(snapshot_gcode.get_return_commands()[1], "G91")
        self.assertEqual(snapshot_gcode.get_return_commands()[2], "G1 F6000")
        self.assertEqual(snapshot_gcode.get_return_commands()[3], "G1 Z-0.500")
        self.assertEqual(snapshot_gcode.get_return_commands()[4], "G1 F3600")
        self.assertEqual(snapshot_gcode.get_return_commands()[5], "SAVEDCOMMAND")
        self.assertEqual(snapshot_gcode.get_return_commands()[6], "M400")
        self.assertEqual(snapshot_gcode.get_return_commands()[7], "M114")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSnapshotGcode)
    unittest.TextTestRunner(verbosity=3).run(suite)
