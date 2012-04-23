var testCases = {

    // extracted loops
    fastaSingleLoop: '>seq1\
GAAAC*GGACC',

    nofastaSingleLoop : 'GAAAC*GGACC',

    fastaMultipleLoops: '>seq1\
GAAC*GGACC\
>seq2\
GAAC*GGACC\
>seq3\
GAAC*GGACC',

    nofastaMultipleLoops: 'GAAAC*GGACC\
GAAAC*GGACC\
GAAAC*GGACC\
GAAAC*GGACC',

    // one entire sequence
    fastaSingleSequenceSS: '(((((.....))))))\
>seq1\
AAAAAAAAAAAAAAAAAAAAAA',

    nofastaSingleSequenceSS: '((((((((((())))))))))))\
AAAAAAAAAAAAAAAAAAAAAA',

    fastaSingleSequenceNoSS: '>seq1\
AAAAAAAAAAAAAAAAAAAAAA',

    nofastaSingleSequenceNoSS: 'AAAAAAAAAAAAAAAAAAAAAA',

    // multiple sequences
    fastaMultipleSequencesSS: '(((((......)))))))\
>seq1\
AAAAAAAAAAAAAAAAAA\
>seq2\
UUUUUUUUUUUUUUUUUU\
>seq3\
GGGGGGGGGGGGGGGGGG',

    nofastaMultipleSequencesSS: '(((((((((.....)))))))\
AAAAAAAAAAAAAAAAA\
GGGGGGGGGGGGGGGGG\
UUUUUUUUUUUUUUUUU',

    fastaMultipleSequencesNoSS: '>seq1\
AAAAAAAAAAA\
>seq2\
GGGGGGGGGGG\
>seq3\
CCCCCCCCCCC',

    nofastaMultipleSequencesNoSS: 'AAAAAAAAAAA\
GGGGGGGGGGG\
UUUUUUUUUUU'

};



test( "hello test", function() {
    ok( 1 == "1", "Passed!" );
});

test( "Fasta tests", function() {
    ok( jar3dInputValidator.hasFasta(testCases['fastaSingleLoop']), 'Passed');
    equal( jar3dInputValidator.hasFasta(testCases['nofastaSingleLoop']), false, 'Passed');
});

