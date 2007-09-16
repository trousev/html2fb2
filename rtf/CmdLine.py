def main(rtfClass):
    import sys
    import optparse
    parser = optparse.OptionParser(usage="%prog [options] file.rtf")
    parser.add_option("-o", "--output", dest="filename", default=None,
                      help="write output in FILE", metavar="FILE")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        print 'incorrect argument number'
        parser.print_help()
        sys.exit(1)
    finput = open(args[0], 'r')
    if options.filename:
        foutput = open(options.filename, 'w')
    else:
        foutput = sys.stdout
    tester = rtfClass(foutput)
    for line in finput:
        tester.feed(line)
    tester.close()
    if options.filename:
        foutput.close()
    finput.close()
    print tester.getAnsiCpg()
