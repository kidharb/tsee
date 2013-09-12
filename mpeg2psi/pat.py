"""Program Association Table module

	Provides a set of functions and a PAT Section class to parse and encapsulate information about a
	MPEG2-TS Program Association Table section
"""

from section import Section

def get_program_map(data=None):
	"""Returns the program map contained in the PAT section data
	
	Given an array of data bytes that comprise of the PAT payload, this method will return the PATs
	program to PID map.
	Arguments:
		data -- Array of data bytes that represent a complete PAT payload (default None)
	Returns:
		A dictionary mapping program numbers to PMT PIDs 
	"""
	programs = {}
	offset = 0
	table_size = len(data) - 4 # remove crc32
	table_entries = table_size / 4
	while table_entries > 0:
		entry = data[offset:offset+4]
		prog = (entry[0] << 8) + entry[1]
		pid  = ((entry[2] & int('00011111',2)) << 8) + entry[3]
		if prog != 0:
			programs[prog] = pid
		offset = offset + 4
		table_entries -= 1
	return programs

class Pat(Section):
	"""Program Association Table class
    
    Inherits from Section and holds information specific to the Program Association Table
    described as a part of MPEG2 PSI
    """
	TABLE_ID = 0x00
	
	def __init__(self, data=None):
		"""Constructor
        
        If the given array is None then the Pat object will be created but incomplete. To build the information
        Pat.parse() or Pat.add_data() should be called. 
        Arguments:
            data -- array of data bytes to parse to build the section information (default None)
        """
		super(Pat, self).__init__(data)
		self.transport_stream_id = self.table_id_extension

	def parse(self, data=None):
		"""Parses the given data to generate all the PAT information
        
        Given an array of bytes that comprise a PAT section, this method will parse and record all the section information
        in object members. Inherits from Section.parse. Will call the Section.parse() method and once complete will parse
        the section table_data to get the PAT specific information.
        Arguments:
            data -- Array of data bytes that describe all or part of the PAT section (default None)
        """
		super(Pat, self).parse(data)
		self.transport_stream_id = self.table_id_extension
		if self.complete:
			self.payload = self.table_body[5:]
			self.table = get_program_map(self.payload)
			del(self.payload)
	
	def __str__(self):
		res = super(Pat, self).__str__()
		resar = res.split('\n')
		resar[0] = 'PAT:'
		resar[6] = '\n\tTransport Stream ID[%d]\n'%(self.transport_stream_id)
		res = '\n'.join(resar)
		res += ' Table:\n'
		for prog in self.table:
			res += '\tprog[%x] - pid[%x]\n'%(prog, self.table[prog]) 
		return res

'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
	print 'Testing Pat class'
	import unittest
	import _known_tables
	pat_data = _known_tables.get_sample_pat_data()[0]
	
	def testPatSection(test_case, section):
		test_case.assertEqual(0, section.table_id, 'incorrect table id')
		test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
		test_case.assertEqual(False, section.private_indicator, 'incorrect private section indicator')
		test_case.assertEqual(97, section.section_length, 'incorrect section length')
		test_case.assertEqual(16, section.table_id_extension, 'incorrect table id extension')
		test_case.assertEqual(16, section.transport_stream_id, 'incorrect table id extension')
		test_case.assertEqual(16, section.version, 'incorrect version')
		test_case.assertEqual(0, section.section_number, 'incorrect section number')
		test_case.assertEqual(0, section.last_section_number, 'incorrect last section number')
		test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
		test_case.assertEqual(22, len(section.table), 'incorrect table length')
		known_table = {10010: 1639, 10011: 1636, 10012: 1603, 10013: 1600, 1695: 1606, 1696: 2003, 1605: 1984, 1607: 1859,
					   1609: 1909, 1613: 2034, 1614: 1634, 3153: 1609, 1619: 1968, 1620: 2079, 1630: 2076, 1640: 2072,
					   1645: 2064, 1656: 1905, 1657: 1901, 1658: 1898, 1659: 32, 1660: 1892}
		test_case.assertEqual(known_table, section.table, 'incorrect table')
		test_case.assertEqual(0xaafe7cbf, section.crc, 'bad crc')

	class KnownSections(unittest.TestCase):
		known_sections = {testPatSection:pat_data}

		def testKnownSections(self):
			for function in self.known_sections:
				data = self.known_sections[function]
				pat = Pat(data)
				function(self, pat)
				print pat

	unittest.main()	