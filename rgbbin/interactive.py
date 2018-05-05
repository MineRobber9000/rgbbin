import os
import rgbbin.logger as logger

from optparse import OptionParser
from rgbbin.objfile import ObjectFile

parser = OptionParser(
	usage="%prog [-h/--help] [-v] [-x] [-o OUTDIR] [-s SYMFILE] OBJFILE"
)
parser.add_option("-v", "--verbose",
	action="store_true",
	default=False,
	help="show detailed information about the parsing process",
	dest="verbose")
parser.add_option("-o", "--output-dir",
	help="output files to OUTDIR (defaults to current directory)",
	dest="outdir",
	metavar="OUTDIR",
	default=".")
parser.add_option("-s", "--symfile",
	help="write a symbol file to SYMFILE",
	dest="symfile",
	metavar="SYMFILE")
parser.add_option("-x", "--hex",
	action="store_true",
	default=False,
	help="alongside .bin files, write .hex files with readable ASCII dumps",
	dest="hex")

(args, file) = parser.parse_args()

if not file:
	parser.error("no input object specified")
file = file[0]

args = vars(args)

if not os.path.isdir(args['outdir']):
	parser.error("output directory does not exist: %s" % args['outdir'])
	
if not os.path.isfile(file):
	parser.error("input file does not exist: %s" % file)

logger.subscribe_info(lambda x: print(x))

if args['verbose']:
	logger.subscribe_verbose(lambda x: print(x))

with ObjectFile(file) as obj:
	obj.parse_header()
	obj.parse_symbols()
	logger.info("loaded %i symbols from '%s'" % (len(obj.symbols), file))
	obj.parse_sections()
	logger.info("loaded %i sections from '%s'" % (len(obj.sections), file))
	obj.parse_patches()
	logger.info("section patches successfully applied")
	for section in obj.sections:
		section['name'] = section['name'].replace("/","_")
		filename_base = args['outdir'] + "/" + section['name']
		logger.info("writing section '%s' to '%s.*'"
			% (section['name'], filename_base))
		with open(filename_base + ".bin", "wb") as fp:
			fp.write(section['data'])
		if args['hex']:
			with open(filename_base + ".hex", "wb") as fp:
				fp.write(' '.join(["%02x" % i for i in section['data']])
							.encode('ascii'))
	if args['symfile'] is not None:
		with open(args['symfile'], "w") as fp:
			fp.write("; (file generated by rgbbin"
					 " // github.com/zzazzdzz/rgbbin)\n\n")
			for symbol in obj.symbols:
				org = obj.sections[symbol['sectid']]['origin']
				fp.write("00:%.4X %s\n"
					% (org + symbol['value'], symbol['name']))

logger.info("finished.")