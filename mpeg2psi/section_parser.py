"""section parser

	Provides a set of functions to parse information about a basic
	MPEG2-TS PSI section.
"""

def get_pointer_field(data):
	"""Get the pointer field from the packet payload
	
	This is an 8-bit field whose value shall be the number of bytes, immediately following the pointer_field
	until the first byte of the first section that is present in the payload of the Transport Stream packet.
	"""
	return data[0]

def get_table_id(data):
	"""Get the table ID from the given section data
	
	Parses the given array of section data bytes to find the Section table ID.
	"""
	return data[0]

def get_section_syntax_indicator(data):
	"""Get the section syntax indicator from the given section data
	
	Parses the given array of section data bytes and returns the section syntax indicator. If True, then this
	is an extended table. If False then it is a simple section.
	"""
	if data[1] & int('10000000', 2): return True
	return False

def get_private_indicator(data):
	"""Gets the private section indicator from the given section data
	
	Parses the given array of section data bytes and returns the private section indicator. If True, then this
	is a private table. If False then it is a normal mpeg ts table (PAT, PMT, CAT).
	"""
	if data[1] & int('01000000', 2): return True
	return False

def get_section_length(data):
	"""Gets the section length from the given section data
	
	Parses the given array of section data bytes and returns the section length.
	"""
	sl = (data[1] & int('00001111', 2)) << 8
	sl = sl + data[2]
	return sl

# Table body 2
def get_table_id_extension(data):
	"""Gets the table id extension from the given section data
	
	Parses the given array of section data bytes and returns the table ID extension value.
	"""
	tide = (data[3] << 8) + data[4]
	return tide

def get_version_number(data):
	"""Gets the table version from the given section data
	
	Parses the given array of section data bytes and returns the version number of the section.
	"""
	vn = data[5] & int('00111110', 2)
	vn = vn >> 1
	return vn

def get_current_next_indicator(data):
	"""Gets the current/next indicator from the given section data
	
	Parses the given array of section data bytes and returns the current/next indicator. If True, then this
	is the currently applicable table. If False then it will become applicable some time in the future.
	"""
	if data[5] & int('00000001', 2): return True
	return False

def get_section_number(data):
	"""Gets the section number from the given section data
	
	Parses the given array of section data bytes and returns the section number. SI tables come in sections.
	Each section is numbered and this function will return the number of the given section.
	"""
	return data[6]

def get_last_section_number(data):
	"""Gets the last section number from the given section data
	
	Parses the given array of section data bytes and returns the last section number. SI tables come in sections.
	This number allows the client to know how many sections in the current table.
	"""
	return data[7]
	
def get_data(data):
	"""Gets the section data payload from the given section data
	
	Parses the given array of section data bytes and returns the section data. This is an array of data bytes.
	It can be further parsed based on the type of section.
	"""	
	offset = 3
	sl = get_section_length(data)
	data_len = sl
	if get_section_syntax_indicator(data): 
		offset += 5
		data_len -= 5
	return list(data[offset:offset+data_len])
	
'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
	#TODO - not a full unit test - need to do partial data addition
	import unittest

	class DataParsing(unittest.TestCase):
		def test(self):
			self.assertEqual(get_table_id([0x22,0xFF]),	0x22, 'failed to get the table ID')
			self.assertEqual(get_table_id([0x64,0xFF]),	0x64, 'failed to get the table ID')
			self.assertEqual(get_table_id([0x00,0xFF]), 0x00, 'failed to get the table ID')
			
			self.assertTrue(get_section_syntax_indicator([0xFF, int('10000000', 2), 0xFF]), 'failed to getting the section syntax indicator')
			self.assertFalse(get_section_syntax_indicator([0xFF, int('01111111', 2), 0xFF]), 'failed to getting the section syntax indicator')
			
			self.assertTrue(get_private_indicator([0xFF,  int('01000000', 2), 0xFF]), 'failed to getting the private indicator')
			self.assertFalse(get_private_indicator([0xFF, int('10111111', 2), 0xFF]), 'failed to getting the private indicator')
			
			self.assertEqual(get_section_length( [0xFF, int('11111111', 2), int('10101010', 2), 0xFF]), int('111110101010', 2), 'failed to get the section length')
			self.assertEqual(get_section_length([0x00, int('00001111', 2), int('10101010', 2), 0x00]), int('111110101010', 2), 'failed to get the section length')

			self.assertEqual(get_table_id_extension([0x22, 0xFF, 0xff, 0x00, 0x00, 0xff]), 0x00, 'failed to get the table id extension')
			self.assertEqual(get_table_id_extension([0x22, 0xFF, 0xff, 0x12, 0x34, 0xff]), 0x1234, 'failed to get the table id extension')


			self.assertEqual(get_version_number([0x22, 0xFF, 0xff, 0x00, 0x00, int('00111110',2), 0x00]), int('11111',2), 'failed to get the version number')
			self.assertEqual(get_version_number([0x22, 0xFF, 0xff, 0x00, 0xFF, int('11000001',2), 0xff]), int('00000',2), 'failed to get the version number')
			
			self.assertTrue(get_current_next_indicator ([0x22, 0xFF, 0xff, 0x00, 0x00, int('00000001',2), 0x00]), 'failed to get the current next flag')
			self.assertFalse(get_current_next_indicator([0x22, 0xFF, 0xff, 0x00, 0x00, int('11111110',2), 0xff]), 'failed to get the current next flag')
			
			self.assertEqual(get_section_number([0x22, 0xFF, 0xff, 0x00, 0x00, 0x00, 0x12]), 0x12, 'failed to get the section number')
			self.assertEqual(get_section_number([0x22, 0xFF, 0xff, 0x00, 0x00, 0x00, 0x34]), 0x34, 'failed to get the section number')
			
			self.assertEqual(get_last_section_number([0x22, 0xFF, 0xff, 0x00, 0x00, 0x00, 0x00, 0x12]), 0x12, 'failed to get the last section number')
			self.assertEqual(get_last_section_number([0x22, 0xFF, 0xff, 0x00, 0x00, 0x00, 0x00, 0x34]), 0x34, 'failed to get the last section number')
			
			self.assertEqual(get_data([0xFF, int('10000000', 2), 10, 0x00, 0x00, 0x00, 0x00, 0x34, 0x12, 0x34, 0x56, 0x78, 0x90]), [0x12, 0x34, 0x56, 0x78, 0x90], 'failed to get the table data')
			self.assertEqual(get_data([0xFF, int('01111111', 2), 5, 0x12, 0x34, 0x56, 0x78, 0x90]), [0x12, 0x34, 0x56, 0x78, 0x90], 'failed to get the table data')
			
		def setUp(self):
			pass
			
		def tearDown(self):
			pass
	
	unittest.main()