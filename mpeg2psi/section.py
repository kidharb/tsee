"""section module

	Provides a Section class to parse and encapsulate information about a basic 
	MPEG2-TS PSI section.
"""

import section_parser as sparse
import section_builder as sbuild

_DEV   = False
_DEBUG = False

if _DEV:
	import struct
	def _save_section_to_file(section):
		filename = 'dev_data/section_tid_%d_ver_%d_scn_%d.sect'%(section.table_id,
															section.version,
															section.section_number)
		print 'SAVING section to file %s'%(filename)
		f = open(filename, 'wb')
		for byte in section.data_cache:
			f.write(struct.pack('B', byte))
		f.close()


class Section(object):
	"""A basic program specific information class
	
	Can be used as a base class for all other SI sections. Will parse an array of section data bytes and generate
	the section header (plus extended header if it is a long table). It will also keep the section data payload
	in a separate array of bytes for further processing for inherited sections.
	"""
	def __init__(self, data=None):
		"""Constructor
		
		If the given array is None then the section object will be created but incomplete. To build the information
		Section.parse() or Section.add_data() should be called. 
		Arguments:
			data -- array of data bytes to parse to build the section information (default None)
		"""
		self.table_id        = None
		self.complete        = False
		self.header          = False
		self.extended_header = False
		self.data_cache      = None
		if data: self.parse(data)

	def _get_header(self, data):
		"""Parses the given data to generate the simple section header
		
		Private method used to generate the first level header.
		Arguments:
			data -- array section data bytes long enough to describe the entire section header
		Returns:
			The byte offset at which the header ends and the rest of the section data continues
		"""
		if self.header: return 3
		self.table_id                 = sparse.get_table_id(data)
		self.section_syntax_indicator = sparse.get_section_syntax_indicator(data)
		self.private_indicator        = sparse.get_private_indicator(data)
		self.section_length           = sparse.get_section_length(data)
		self.length                   = self.section_length + 3
		self.header                   = True
		return 3

	def _get_extended_header(self, data):
		"""Parses the given data to generate the extended section header
		
		Private method called if the table is an extended one (section syntax indicator == 1).
		fills in the extended header information for this object.
		Arguments:
			data -- array of section data bytes, from beginning of section, long enough to describe
			the simple and extended headers.
		Returns:
			The byte offset at which the extended header ends and the rest of the section data continues
		"""
		if self.extended_header: return 5
		self.table_id_extension     = sparse.get_table_id_extension(data)
		self.version                = sparse.get_version_number(data)
		self.current_next_indicator = sparse.get_current_next_indicator(data)
		self.section_number         = sparse.get_section_number(data)
		self.last_section_number    = sparse.get_last_section_number(data)
		self.extended_header        = True
		return 5
	
	def _parse_header(self, data):
		"""Parses the given data to the full section header information
		
		Private method called that parses the section data to generate the complete header information.
		If this section is an extended table (section syntax indicator == 1), then the extended header will be recorded as well
		Arguments:
			data -- array of section data bytes, from beginning of section, long enough to describe
			the simple (and extended header if it exists).
		Returns:
			The byte offset at which the header ends and the rest of the section data continues
		"""
		data_len = len(data)
		if data_len < 3: return 0
		parsed_len  = self._get_header(data)
		data_len   -= parsed_len
		if self.section_syntax_indicator:
			if data_len < 5: return 0
			parsed_len += self._get_extended_header(data)
		return parsed_len		
		
	def parse(self, data=None):
		"""Parses the given data to generate all the section information
		
		Given an array of bytes that comprise a section, this method will parse and record all the section information
		in object members. The Section object can progressively parse data using Section.add_data(). If this method is
		called with the data argument == None, (normally done privately) then the cached data pushed in by 
		Section.add_data() will be parsed. When the entire section has been parse then the member Section.complete will
		be set to True
		Arguments:
			data -- Array of data bytes that describe all or part of a section (default None, in this case, the method
			will assume that new data has been added to the internal cache by Section.add_data() and will continue
			parsing and extracting information not yet handled)
		"""
		if data: self.data_cache = list(data)
		else: data = self.data_cache
		
		self._parse_header(data)
		if not self.header: return
		
		if len(data) >= self.section_length + 3:
			self.table_body = data[3:3+self.section_length]
			self.complete = True
			self._get_crc(self.table_body)
			if _DEV: _save_section_to_file(self)
			#del (self.data_cache)
			
	def build(self):
		"""Takes the section object and builds a data section from it
		
		Will allocate a new array of bytes and then build a transport stream section from the information in this object
		Return:
		    Returns the array of bytes containing the section
		"""
		if not self.complete: return None
		data=sbuild.create_section_data_block(self.section_length+3)
		sbuild.set_table_id(data, self.table_id)
		sbuild.set_section_syntax_indicator(data, self.section_syntax_indicator)
		sbuild.set_private_indicator(data, self.private_indicator)
		sbuild.set_section_length(data, self.section_length)
		offset=3
		if self.section_syntax_indicator:
		    sbuild.set_table_id_extension(data, self.table_id_extension)
		    sbuild.set_version_number(data, self.version_number)
		    sbuild.set_current_next_indicator(data, self.current_next_indicator)
		    sbuild.set_section_number(data, self.section_number)
		    sbuild.set_last_section_number(data, self.last_section_number)
		    offset=8
		sbuild.set_data(data, self.table_body, offset)
		if self.section_syntax_indicator:
			sbuild.append_crc(data)
			self.crc=sbuild.calculate_crc(data[0:-4])
		return data
	
	def add_data(self, data):
		"""Add section data to the object to be processed
		
		The Section object can be parsed progressively. If it is not yet complete then this method can be called
		to add required data. As new data is added more section information will be available from the object.
		If the section parsing is already complete (Section.complete == True), the method will return immediately.
		Arguments:
			data -- Array of data bytes that describe all or part of the section. Can be progressively added.
		Return:
			Returns the number of bytes added
		"""
		if self.complete: return 0
		if not self.data_cache:
			self.parse(data)
			return len(self.data_cache)
			
		data = list(data)
		datalen = len(data)
		consumed_len = 0
		
		if not self.header:
			current_data_len = len(self.data_cache)
			missing_header_len = 3 - current_data_len
			if datalen < missing_header_len:
				self.data_cache.extend(data)
				return datalen
			self.data_cache.extend(data[0:missing_header_len])
			consumed_len += missing_header_len
			self.parse()
		
		missing_data_len = (self.section_length + 3) - len(self.data_cache)
		self.data_cache.extend(data[consumed_len:missing_data_len])
		consumed_len += missing_data_len
		self.parse()
		
		return consumed_len
		
	def _get_crc(self, data):
		"""Saves the section CRC
		
		Private method that will parse the section data (entire section length of bytes plus header required
		since the CRC is the last 4 bytes) and save the 4 byte CRC value
		Arguments:
			data -- Array of data bytes that describe the entire section.
		"""
		if not self.complete: return
		if not self.extended_header: return
		crc_data = data[-4:]
		self.crc = crc_data[0] << 8
		self.crc += crc_data[1]
		self.crc <<= 8
		self.crc += crc_data[2]
		self.crc <<= 8
		self.crc += crc_data[3]

	def __str__(self):
		if self.table_id == None: return 'Empty'
		res = 'Section:\n'
		res += '\tTableID                 [%d]\n'%(self.table_id)
		res += '\tSection Syntax Indicator[%s]\n'%(str(self.section_syntax_indicator))
		res += '\tPrivate Section         [%s]\n'%(str(self.private_indicator))
		res += '\tSection Length          [%d]\n'%(self.section_length)
		if self.section_syntax_indicator and self.extended_header:
			res += ' Extension:\n'
			res += '\tTableID Extension  [%d]\n'%(self.table_id_extension)
			res += '\tVersion            [%d]\n'%(self.version)
			res += '\tCurrent Next flag  [%s]\n'%(str(self.current_next_indicator))
			res += '\tSection Number     [%d]\n'%(self.section_number)
			res += '\tLast Section Number[%d]\n'%(self.last_section_number)
			if self.complete:
				res += '\tCRC[0x%x]\n'%(self.crc)
		return res
	

'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
	#TODO - not a full unit test - need to do partial data addition
	import unittest
	import _known_tables

	nit_data_0 = _known_tables.get_sample_nit_data()[0]
	nit_data_1 = _known_tables.get_sample_nit_data()[1]
	cat_data   = _known_tables.get_sample_cat_data()[0]
	pat_data   = _known_tables.get_sample_pat_data()[0]
	pmt_data   = _known_tables.get_sample_pmt_data()[0]
	
	def testNitSection0(test_case, section):
		test_case.assertEqual(64, section.table_id, 'incorrect table id')
		test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
		test_case.assertEqual(True, section.private_indicator, 'incorrect private section indicator')
		test_case.assertEqual(1014, section.section_length, 'incorrect section length')
		test_case.assertEqual(6144, section.table_id_extension, 'incorrect table id extension')
		test_case.assertEqual(1, section.version, 'incorrect version')
		test_case.assertEqual(0, section.section_number, 'incorrect section number')
		test_case.assertEqual(1, section.last_section_number, 'incorrect last section number')
		test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
		test_case.assertEqual(0xD9787E8A, section.crc, 'bad crc')
		
	def testNitSection1(test_case, section):
		test_case.assertEqual(64, section.table_id, 'incorrect table id')
		test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
		test_case.assertEqual(True, section.private_indicator, 'incorrect private section indicator')
		test_case.assertEqual(145, section.section_length, 'incorrect section length')
		test_case.assertEqual(6144, section.table_id_extension, 'incorrect table id extension')
		test_case.assertEqual(1, section.version, 'incorrect version')
		test_case.assertEqual(1, section.section_number, 'incorrect section number')
		test_case.assertEqual(1, section.last_section_number, 'incorrect last section number')
		test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
		test_case.assertEqual(0xCF1BECB1, section.crc, 'bad crc')
		
	def testCatSection(test_case, section):
		test_case.assertEqual(1, section.table_id, 'incorrect table id')
		test_case.assertTrue(section.section_syntax_indicator, 'incorrect section syntax indicator')
		test_case.assertFalse(section.private_indicator, 'incorrect private section indicator')
		test_case.assertEqual(15, section.section_length, 'incorrect section length')
		test_case.assertEqual(0, section.version, 'incorrect version')
		test_case.assertTrue(section.current_next_indicator, 'incorrect current next indicator')
		test_case.assertEqual(0, section.section_number, 'incorrect section number')
		test_case.assertEqual(0, section.last_section_number, 'incorrect last section number')
		test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
		test_case.assertEqual(0x9064C6D0, section.crc, 'bad crc')
		
	def testPatSection(test_case, section):
		test_case.assertEqual(0, section.table_id, 'incorrect table id')
		test_case.assertTrue(section.section_syntax_indicator, 'incorrect section syntax indicator')
		test_case.assertFalse(section.private_indicator, 'incorrect private section indicator')
		test_case.assertEqual(0x61, section.section_length, 'incorrect section length')
		test_case.assertEqual(16, section.table_id_extension, 'incorrect table id extension')
		test_case.assertEqual(16, section.version, 'incorrect version')
		test_case.assertTrue(section.current_next_indicator, 'incorrect current next indicator')
		test_case.assertEqual(0, section.section_number, 'incorrect section number')
		test_case.assertEqual(0, section.last_section_number, 'incorrect last section number')
		test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
		test_case.assertEqual(0xAAFE7CBF, section.crc, 'bad crc')
		
	def testPmtSection(test_case, section):
		test_case.assertEqual(2, section.table_id, 'incorrect table id')
		test_case.assertTrue(section.section_syntax_indicator, 'incorrect section syntax indicator')
		test_case.assertFalse(section.private_indicator, 'incorrect private section indicator')
		test_case.assertEqual(0x48, section.section_length, 'incorrect section length')
		test_case.assertEqual(1, section.version, 'incorrect version')
		test_case.assertTrue(section.current_next_indicator, 'incorrect current next indicator')
		test_case.assertEqual(0, section.section_number, 'incorrect section number')
		test_case.assertEqual(0, section.last_section_number, 'incorrect last section number')
		test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
		test_case.assertEqual(0x11F62C03, section.crc, 'bad crc')
		
	class KnownSections(unittest.TestCase):
		known_sections = {testNitSection0:nit_data_0,
						  testNitSection1:nit_data_1,
						  testPatSection:pat_data,
						  testPmtSection:pmt_data,
						  testCatSection:cat_data}
		
		def testKnownSections(self):
			for function in self.known_sections:
				data = self.known_sections[function]
				section = Section(data)
				function(self, section)							
	
	
	def test_nit_0(test_case, section):
		test_case.assertEqual(64, section.table_id, 'incorrect table id')
		test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
		test_case.assertEqual(True, section.private_indicator, 'incorrect private section indicator')
		test_case.assertEqual(1014, section.section_length, 'incorrect section length')
		test_case.assertEqual(6144, section.table_id_extension, 'incorrect table id extension')
		test_case.assertEqual(1, section.version, 'incorrect version')
		test_case.assertEqual(0, section.section_number, 'incorrect section number')
		test_case.assertEqual(1, section.last_section_number, 'incorrect last section number')
		test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
		test_case.assertEqual(0xD9787E8A, section.crc, 'bad crc')
	
	class PartialData(unittest.TestCase):
		nit_data_0 = _known_tables.get_sample_nit_data()[0]
		
		def setUp(self):
			self.section = Section()
	
		def testPartialData1(self):
			for i in range(0,len(nit_data_0)):
				#print list([nit_data_0[i]])
				self.section.add_data(list([nit_data_0[i]]));
			test_nit_0(self, self.section)
		
		def testPartialData2(self):
			for i in range(0,len(nit_data_0), 2):
				self.section.add_data(list(nit_data_0[i:i+2]));
			test_nit_0(self, self.section)
		
		def testPartialData3(self):
			for i in range(0,len(nit_data_0), 3):
				self.section.add_data(list(nit_data_0[i:i+3]));
			test_nit_0(self, self.section)
		
		def testPartialData4(self):
			for i in range(0,len(nit_data_0), 4):
				self.section.add_data(list(nit_data_0[i:i+4]));
			test_nit_0(self, self.section)
		
	
	class SectionBuilder(unittest.TestCase):
		
		def setUp(self):
			self.section = Section()
		
		def tearDown(self):
		    del(self.section)
		    
		def testBuildCat(self):
		    section = self.section
		    section.table_id=1
		    section.section_syntax_indicator=True
		    section.private_indicator=False
		    section.section_length=15
		    section.version=0
		    section.current_next_indicator=True
		    section.table_id_extension=0xffff
		    section.version_number=0
		    section.section_number=0
		    section.last_section_number=0
		    section.crc=0x9064C6D0
		    section.table_body=[0x09, 0x04, 0x06, 0x06, 0x05, 0x00, 0x90, 0x64, 0xC6, 0xD0]
		    section.complete=True
		    data=section.build()
		    self.assertEqual(cat_data, data)
				
	unittest.main()