"""section builder

	Provides a set of functions to build a basic MPEG2-TS PSI section.
"""

def create_section_data_block(data_length):
	"""Create a block of data to represend a section
	
	Creates a list of the given size and returns it. The list will have every byte zeroed
	Arguments:
		data_length -- amount of bytes needed for the data block
	Returns:
		A list of bytes of the desired length with zero in every byte
	"""
	data = [0x00] * data_length
	return data
	
def set_table_id(data, table_id):
	"""Set the Table ID in a Section
	
	Given a block of section data, sets the Table ID
	Arguments:
		data -- List of bytes. Data to manipulate
		table_id -- the table id to set
	Returns:
		table id that was set
	"""
	data[0] = table_id
	return table_id
	
def set_section_syntax_indicator(data, indicator):
	"""Set the section syntax indicator in a Section
	
	Given a block of section data, sets the section syntax indicator
	Arguments:
		data -- List of bytes. Data to manipulate
		indicator -- Boolean value to set the indicator to
	"""
	data[1] = data[1] & int ('01111111', 2)
	if indicator: data[1] = data[1] | int ('10000000', 2)

def set_private_indicator(data, indicator):
	"""Sets the private section indicator in the given section data
	
	Given a block of section data, sets the private indicator
	Arguments:
		data -- List of bytes. Data to manipulate
		indicator -- Boolean value to set the indicator to
	"""
	data[1] = data[1] & int ('10111111', 2)
	if indicator: data[1] = data[1] | int ('01000000', 2)

def set_section_length(data, section_length):
	"""Sets the section length in the given section data
	
	Given a block of section data, sets the section length
	Arguments:
		data -- List of bytes. Data to manipulate
		section_length -- value to set
	"""
	#clear the bit feilds first
	data[1] = data[1] & int('11110000', 2)
	data[2] = 0x00;
	#now break up the input
	part1 = section_length & 0x0f00
	part1 = part1 >> 8
	part2 = section_length & 0x00ff
	data[1] |= part1
	data[2]  = part2


# Table body 2
def set_table_id_extension(data, table_id_extension):
	"""Sets the table id extension in the given section data
	
	Given a block of section data, sets the table id extension
	Arguments:
		data -- List of bytes. Data to manipulate
		table_id_extension -- value to set
	"""
	data[3] = (table_id_extension & 0xff00) >> 8
	data[4] = table_id_extension & 0x00ff

def set_version_number(data, version):
	"""Sets version number in the given section data
	
	Given a block of section data, sets the version number
	Arguments:
		data -- List of bytes. Data to manipulate
		version -- value to set
	"""
	data[5] &= int('11000001', 2) #clear the bit feilds first
	#version &= int('00011111', 2)
	version <<= 1
	version &= int('00111110', 2)
	data[5] |= version
	
def set_current_next_indicator(data, indicator):
	"""Sets the current/next indicator in the given section data
	
	Given a block of section data, sets the current/next indicator
	Arguments:
		data -- List of bytes. Data to manipulate
		indicator -- Boolean value to set the indicator to
	"""
	data[5] &= int ('11111110', 2)
	if indicator: data[5] |= int ('00000001', 2)

def set_section_number(data, section_number):
	"""Sets the section number in the given section data
	
	Given a block of section data, sets the section number
	Arguments:
		data -- List of bytes. Data to manipulate
		section_number -- value to set
	"""
	data[6] = section_number & 0xff

def set_last_section_number(data, last_section_number):
	"""Sets the last section number in the given section data
	
	Given a block of section data, sets the last section number
	Arguments:
		data -- List of bytes. Data to manipulate
		last_section_number -- value to set
	"""
	data[7] = last_section_number & 0xff
	
def set_data(data, payload, offset):
	"""Sets the data payload in the given section data
	
	Given a block of section data, sets the data payload (including CRC)
	Arguments:
		data -- List of bytes. Data to manipulate
		payload -- payload bytes
		offset -- the byte at which the data should start
	"""	
	j=0
	for i in range(offset, len(data)):
		data[i] = payload[j]
		j+=1

'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
	#TODO - not a full unit test - need to do partial data addition
	import unittest
	import section_parser as sparser
	import random

	
	class All(unittest.TestCase):
		def test(self):
			self.assertEqual(len(self.data), self.data_length)
			set_table_id(self.data, 1)
			set_section_syntax_indicator(self.data, True)
			set_private_indicator(self.data, False)
			set_section_length(self.data, self.data_length - 3)
			set_table_id_extension(self.data, 20)
			set_version_number(self.data, 10)
			set_current_next_indicator(self.data, True)
			set_section_number(self.data, 25)
			set_last_section_number(self.data, 35)
			self.data_contents = random.sample(range(256), self.data_length-8)
			set_data(self.data, self.data_contents, 8)
			actual_data_contents = sparser.get_data(self.data)
			
			self.assertEqual(self.data[0], 1)
			self.assertTrue(sparser.get_section_syntax_indicator(self.data))
			self.assertFalse(sparser.get_private_indicator(self.data))
			self.assertEqual(sparser.get_section_length(self.data), self.data_length-3)
			self.assertEqual(sparser.get_table_id_extension(self.data), 20)
			self.assertEqual(sparser.get_version_number(self.data), 10)
			self.assertTrue(sparser.get_current_next_indicator(self.data))
			self.assertEqual(sparser.get_section_number(self.data), 25)
			self.assertEqual(sparser.get_last_section_number(self.data), 35)
			self.assertEqual(actual_data_contents, self.data_contents)
			

		def setUp(self):
			self.data_length = 100
			self.data=create_section_data_block(self.data_length)
			
		def tearDown(self):
			del(self.data)
			
	class AllReverse(unittest.TestCase):
		def test(self):
			self.data_contents = random.sample(range(256), self.data_length-8)
			set_data(self.data, self.data_contents, 8)
			set_last_section_number(self.data, 35)
			set_section_number(self.data, 25)
			set_current_next_indicator(self.data, True)
			set_version_number(self.data, 10)
			set_table_id_extension(self.data, 20)
			set_section_length(self.data, self.data_length - 3)
			set_private_indicator(self.data, False)
			set_section_syntax_indicator(self.data, True)
			set_table_id(self.data, 1)
			
			self.assertEqual(len(self.data), self.data_length)
			self.assertEqual(self.data[0], 1)
			self.assertTrue(sparser.get_section_syntax_indicator(self.data))
			self.assertFalse(sparser.get_private_indicator(self.data))
			self.assertEqual(sparser.get_section_length(self.data), self.data_length-3)
			self.assertEqual(sparser.get_table_id_extension(self.data), 20)
			self.assertEqual(sparser.get_version_number(self.data), 10)
			self.assertTrue(sparser.get_current_next_indicator(self.data))
			self.assertEqual(sparser.get_section_number(self.data), 25)
			self.assertEqual(sparser.get_last_section_number(self.data), 35)
			actual_data_contents = sparser.get_data(self.data)
			self.assertEqual(actual_data_contents, self.data_contents)
			

		def setUp(self):
			self.data_length = 100
			self.data=create_section_data_block(self.data_length)
			
		def tearDown(self):
			del(self.data)
	
	class Seq(unittest.TestCase):
		def test(self):
			self.assertEqual(len(self.data), self.data_length)
			set_table_id(self.data, 1)
			self.assertEqual(self.data[0], 1, 'error setting table id')
			set_section_syntax_indicator(self.data, True)
			self.assertTrue(sparser.get_section_syntax_indicator(self.data), 'Error setting section syntax indicator')
			set_section_syntax_indicator(self.data, False)
			self.assertFalse(sparser.get_section_syntax_indicator(self.data), 'Error setting section syntax indicator')
			set_section_syntax_indicator(self.data, True)
			self.assertTrue(sparser.get_section_syntax_indicator(self.data), 'Error setting section syntax indicator')
			set_private_indicator(self.data, False)
			self.assertFalse(sparser.get_private_indicator(self.data), 'Error setting private indicator')
			set_section_length(self.data, self.data_length - 3)
			self.assertEqual(sparser.get_section_length(self.data), self.data_length-3, 'error setting section length')
			set_table_id_extension(self.data, 20)
			self.assertEqual(sparser.get_table_id_extension(self.data), 20, 'error setting table id extension')
			set_version_number(self.data, 10)
			self.assertEqual(sparser.get_version_number(self.data), 10, 'error setting version number')
			set_current_next_indicator(self.data, True)
			self.assertTrue(sparser.get_current_next_indicator(self.data), 'Error setting current next indicator')
			set_section_number(self.data, 25)
			self.assertEqual(sparser.get_section_number(self.data), 25, 'error setting section number')
			set_last_section_number(self.data, 35)
			self.assertEqual(sparser.get_last_section_number(self.data), 35, 'error setting last section number')
			self.data_contents = random.sample(range(256), self.data_length-8)
			actual_data_contents = sparser.get_data(self.data)
			set_data(self.data, self.data_contents, 8)
			actual_data_contents = sparser.get_data(self.data)
			self.assertEqual(actual_data_contents, self.data_contents, 'error setting section data')

		def setUp(self):
			self.data_length = 100
			self.data=create_section_data_block(self.data_length)
			
		def tearDown(self):
			del(self.data)
			
	unittest.main()