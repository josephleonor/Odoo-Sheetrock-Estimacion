from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSheetrockWallGeometry(TransactionCase):

    def setUp(self):
        super().setUp()
        self.wall = self.env['sheetrock.section'].create({
            'name': 'M-01',
            'length': 4.80,
            'height': 2.70,
            'faces': '2',
            'layers': 1,
            'waste_percent': 10.0,
            'stud_spacing': 0.40,
            'structure_type': 'metal',
            'board_thickness': '1/2',
            'structure_gauge': '26',
        })

    def test_net_area_with_door_and_window(self):
        self.env['sheetrock.opening'].create({
            'section_id': self.wall.id,
            'name': 'P-01',
            'opening_type': 'door',
            'width': 0.90,
            'height': 2.10,
            'x_position': 0.30,
            'sill_height': 0.0,
        })
        self.env['sheetrock.opening'].create({
            'section_id': self.wall.id,
            'name': 'V-01',
            'opening_type': 'window',
            'width': 1.20,
            'height': 1.00,
            'x_position': 2.40,
            'sill_height': 1.00,
        })

        self.assertAlmostEqual(self.wall.gross_area, 12.96, places=2)
        self.assertAlmostEqual(self.wall.openings_area, 3.09, places=2)
        self.assertAlmostEqual(self.wall.net_area, 9.87, places=2)
        self.assertAlmostEqual(self.wall.area, 19.74, places=2)
        self.assertAlmostEqual(self.wall.area_with_waste, 21.714, places=3)
        self.assertIn('svg', str(self.wall.elevation_html))

    def test_opening_cannot_leave_wall(self):
        with self.assertRaises(ValidationError):
            self.env['sheetrock.opening'].create({
                'section_id': self.wall.id,
                'name': 'V-OUT',
                'opening_type': 'window',
                'width': 1.50,
                'height': 1.00,
                'x_position': 4.00,
                'sill_height': 1.00,
            })

    def test_openings_cannot_overlap(self):
        self.env['sheetrock.opening'].create({
            'section_id': self.wall.id,
            'name': 'P-01',
            'opening_type': 'door',
            'width': 0.90,
            'height': 2.10,
            'x_position': 0.30,
            'sill_height': 0.0,
        })
        with self.assertRaises(ValidationError):
            self.env['sheetrock.opening'].create({
                'section_id': self.wall.id,
                'name': 'V-OVERLAP',
                'opening_type': 'window',
                'width': 0.80,
                'height': 0.80,
                'x_position': 0.50,
                'sill_height': 1.00,
            })
