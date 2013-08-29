'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
	#TODO - not a full unit test - need to do partial data addition
	import unittest
	import section_parser as sparser
	import random

	class Building(unittest.TestCase):
		def test(self):
			self.assertEqual(len(self.data), self.data_length)
			set_table_id(self.data, 1)
			self.assertEqual(self.section_data[0], 1, 'error setting table id')
			set_section_syntax_indicator(self.section_data, True)
			seld.assertTrue(sparser.get_section_syntax_indicator(self.data), 'Error setting section syntax indicator')
			set_private_indicator(self.data, False)
			self.assertFalse(sparser.get_private_indicator(self.data), 'Error setting private indicator')
			set_section_length(self.data, self.data_length - 3)
			self.assertEqual(sparser.get_section_length(self.data), self.data_length-3, 'error setting section length')
			set_table_id_extension(self.data, 16)
			self.assertEqual(sparser.get_table_id_extension(self.data), 16, 'error setting table id extension')
			set_version_number(self.data, 10)
			self.assertEqual(sparser.get_version_number(self.data), 10, 'error setting version number')
			set_current_next_indicator(self.data, True)
			seld.assertTrue(sparser.get_current_next_indicator(self.data), 'Error setting current next indicator')
			set_section_number(self.data, 25)
			self.assertEqual(sparser.get_section_number(self.data), 25, 'error setting section number')
			set_last_section_number(self.data, 35)
			self.assertEqual(sparser.get_last_section_number(self.data), 35, 'error setting last section number')
			self.data_contents = random.sample(range(256), self.data_length-8)
			set_data(self.data, self.data_contents)
			actual_data_contents = sparser.get_data(self.data)
			self.assertEqual(actual_data_contents, self.data_contents, 'error setting section data')

		def setUp(self):
			self.data_length = 100
			self.data=create_section_data_block(self.data_length)
			
		def tearDown(self):
			pass
	
	unittest.main()