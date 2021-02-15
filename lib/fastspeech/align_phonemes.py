#!/usr/bin/env python3
#
# Copyright 2015 Robert Kjaran
#
#

from collections import OrderedDict
from pprint import pprint

# Eiríkur Rögnvaldsson. Icelandic Phonetic Transcription.
ER_PHONEMES = {
    # Consonants Plosives
    'p',
    'pʰ',
    't',
    'tʰ',
    'c',
    'cʰ',
    'k',
    'kʰ',
    # Consonants Fricatives
    'f',
    'v',
    'ð',
    'θ',
    's',
    'j',
    'ç',
    'ɣ',
    'x',
    'h',
    # Consonants Nasals
    'm',
    'n',
    'ɲ',
    'ŋ',
    'm̥',
    'n̥',
    'ɲ̊',
    'ŋ̊',
    # Consonants Laterals
    'l',
    'l̥',
    # Consonants Taps/Trills
    'r',
    'r̥',
    # Vowels Single
    'ɪ',
    'ɪː',
    'i',
    'iː',
    'ɛ',
    'ɛː',
    'a',
    'aː',
    'ʏ',
    'ʏː',
    'œ',
    'œː',
    'u',
    'uː',
    'ɔ',
    'ɔː',
    # Vowels Dipthongs
    'au',
    'auː',
    'ou',
    'ouː',
    'ei',
    'eiː',
    'ai',
    'aiː',
    'œy',
    'œyː',
    'ʏi',
    'ɔi',
}

DEFAULT_PHONEMES = ER_PHONEMES

class Aligner(object):
    def __init__(self, phoneme_set=None, align_sep=' ', cleanup=''):
        "Align according to phoneme_set"
        if phoneme_set:
            self.phoneme_set = phoneme_set
        else:
            self.phoneme_set = DEFAULT_PHONEMES
        self.phoneme_stats = dict(zip(self.phoneme_set, [0 for i in
                                                         range(len(self.phoneme_set))]))
        self.max_plen = 0
        self.align_sep = align_sep
        self.clean_trtbl = str.maketrans('', '', cleanup)
        for phoneme in self.phoneme_set:
            plen = len(phoneme)
            self.max_plen = plen if plen > self.max_plen else self.max_plen

    def find_longest(self, partial_pstring, phoneme_string):
        if len(partial_pstring) < self.max_plen:
            max_len = len(partial_pstring)
        else:
            max_len = self.max_plen

        r = range(1, max_len+1)[::-1]

        for l in r:
            if partial_pstring[0:l] in self.phoneme_set:
                self.phoneme_stats[partial_pstring[0:l]] += 1
                return l
        raise ValueError('Invalid symbol found in "{}"'
                         .format(phoneme_string + '\t' + partial_pstring[0:l]))

    def align(self, phoneme_string):
        phoneme_string = self.clean(phoneme_string)
        sublengths = []
        w = phoneme_string
        while len(w) > 0:
            offset = self.find_longest(w, phoneme_string)
            w = w[offset:]
            sublengths.append(offset)
        aligned = []
        a = 0
        for b in sublengths:
            aligned.append(phoneme_string[a:a+b])
            a = a+b
        return self.align_sep.join(aligned)

    def clean(self, phoneme_string):
        """Clean some unwanted characters from string"""
        return phoneme_string.translate(self.clean_trtbl)

    @staticmethod
    def read_file_as_set(fpath):
        phonemes = set()
        with open(fpath) as fobj:
            for line in fobj:
                line = line.strip()
                if line[0] != '#':
                    phonemes.add(line)
        return phonemes

def parse_args():
    """Align phomemes"""
    import argparse, sys
    parser = argparse.ArgumentParser(
        description='Aligns input (left-to-right)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('input', nargs='?',
                        type=argparse.FileType('r'), default=sys.stdin,
                        help='Input file, generally two columns.')
    parser.add_argument('output', nargs='?',
                        type=argparse.FileType('w'), default=sys.stdout,
                        help='Output file, --')

    parser.add_argument('--col-sep', '-d', metavar='D', default='\t',
                        help='Column seperator')
    parser.add_argument('--align-col', '-f', metavar='F', type=lambda s: int(s)-1,
                        help='Column to align', default=1)
    parser.add_argument('--align-sep', default=' ', type=str,
                        help='Seperator for alignment')

    parser.add_argument('--output-sep', default='\t', type=str,
                        help='Seperator for output columns.')
    parser.add_argument('--output-cols', metavar='O',
                        type=lambda s: [int(item)-1 for item in
                                        s.split(',')],
                        help="""Which fields from input (comma seperated)
                        should be printed, defaults to only print
                        aligned column.""")

    parser.add_argument('--phoneme-set',
                        type=lambda s: Aligner.read_file_as_set(str(s)),
                        help="""Phoneme set to use for alignment. Newline seperated text
                        file. Ignores lines beginning with #""")
    parser.add_argument('--remove-chars', type=str, default='ˈ',
                        help="""Remove these unicode *characters* from the align column. """)

    return parser.parse_args()

def main():
    import sys

    args = parse_args()

    # write the output otherwise written to stderr to file
    # comment this out if you want to use the output argument for the aligned results!
    if args.output != sys.stdout:
        sys.stderr = args.output


    if not args.output_cols:
        output_cols = [args.align_col]
    else:
        output_cols = args.output_cols
    aligner = Aligner(phoneme_set=args.phoneme_set,
                      align_sep=args.align_sep, cleanup=args.remove_chars)



    print('Using the following phoneme-set: {}'.format(aligner.phoneme_set),
          file=sys.stderr)

    err_cnt = 0
    for line in args.input:
        try:
            line = line.strip()
            cols = line.split(args.col_sep)
            pron = aligner.align(cols[args.align_col])

            out_cols = cols
            out_cols[args.align_col] = pron

            print(args.output_sep.join(out_cols[col] for col in output_cols))
        except ValueError as e:
            err_cnt += 1
            if err_cnt < 1000:
                print('"{}"'.format(e),
                      file=sys.stderr)
            elif err_cnt == 11:
                print('more than {} errors, not showing more'.format(err_cnt),
                      file=sys.stderr)
    print('Total #errors {}'.format(err_cnt), file=sys.stderr)
    print('Phoneme frequencies:', file=sys.stderr)
    pprint(OrderedDict(sorted(aligner.phoneme_stats.items(),
                              key=lambda t: t[1])), stream=sys.stderr)

if __name__ == '__main__':
    main()
