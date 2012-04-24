var testCases = {

    // extracted loops
    fastaSingleLoop: ['>seq1','GAAAC*GGACC'].join('\n'),

    nofastaSingleLoop : 'GAAAC*GGACC',

    fastaMultipleLoops: ['>seq1', 'GAAC*GGACC',
                         '>seq2', 'GAAC*GGACC',
                         '>seq3', 'GAAC*GGACC'].join('\n'),

    nofastaMultipleLoops: ['GAAAC*GGACC',
                           'GAAAC*GGACC',
                           'GAAAC*GGACC',
                           'GAAAC*GGACC'].join('\n'),

    // one entire sequence
    fastaSingleSequenceSS: ['(((((.....))))))',
                            '>seq1',
                            'AAAAAAAAAAAAAAAAAAAAAA'].join('\n'),

    nofastaSingleSequenceSS: ['((((((((((())))))))))))',
                              'AAAAAAAAAAAAAAAAAAAAAA'].join('\n'),

    fastaSingleSequenceNoSS: ['>seq1','AAAAAAAAAAAAAAAAAAAAAA'].join('\n'),

    nofastaSingleSequenceNoSS: 'AAAAAAAAAAAAAAAAAAAAAA',

    // multiple sequences
    fastaMultipleSequencesSS: ['(((((......)))))))',
                               '>seq1', 'AAAAAAAAAAAAAAAAAA',
                               '>seq2', 'UUUUUUUUUUUUUUUUUU',
                               '>seq3', 'GGGGGGGGGGGGGGGGGG'].join('\n'),

    nofastaMultipleSequencesSS: ['(((((((((.....)))))))',
                                 'AAAAAAAAAAAAAAAAA',
                                 'GGGGGGGGGGGGGGGGG',
                                 'UUUUUUUUUUUUUUUUU'].join('\n'),

    fastaMultipleSequencesNoSS: ['>seq1','AAAAAAAAAAA',
                                 '>seq2','GGGGGGGGGGG',
                                 '>seq3','CCCCCCCCCCC'].join('\n'),

    nofastaMultipleSequencesNoSS: ['AAAAAAAAAAA',
                                   'GGGGGGGGGGG',
                                   'UUUUUUUUUUU'].join('\n'),

};

var validator = jar3dInputValidator;

test( "isLoopLine", function() {
    ok(validator.isLoopLine('CCGU*ACGUG'), 'Valid internal loop');
    ok(validator.isLoopLine('CCGUACGUG'), 'Valid hairpin loop');
    equal(validator.isLoopLine('CCGUACGUGAUCGGUAUGUCUGAGUAUGUCGUAGC'), false, 'Very long loop');
    equal(validator.isLoopLine('CAGU*ACGA*G'), false, 'Extra chain break character');
    equal(validator.isLoopLine('CA&$GU*ACGAHG'), false, 'Disallowed characters');
    equal(validator.isLoopLine('CAGU*UCGAG'), false, 'Complementary internal loop');
    equal(validator.isLoopLine('AGUUCGAG'), false, 'Complementary hairpin');
});

test( "isSecondaryStructure", function() {
    ok(validator.isSecondaryStructure('(((...)))'), 'Valid secondary structure');
    equal(validator.isSecondaryStructure('(((((....))'), false, 'Unequal number of ( and )');
    equal(validator.isSecondaryStructure('(((((.N..)))))'), false, 'Disallowed characters');
});

test( "isFastaSingleLoop", function() {
    ok( validator.isFastaSingleLoop(testCases['fastaSingleLoop']), 'Passed');
    $.each(testCases, function(type, i) {
        if ( type != 'fastaSingleLoop' ) {
            equal( validator.isFastaSingleLoop(testCases[type]), false, testCases[type]);
        }
    });
});

test( "isNoFastaSingleLoop", function() {
    ok( validator.isNoFastaSingleLoop(testCases['nofastaSingleLoop']) );
    $.each(testCases, function(type, i) {
        if ( type != 'nofastaSingleLoop' ) {
            equal( validator.isNoFastaSingleLoop(testCases[type]), false, testCases[type]);
        }
    });
});

test( "isFastaMultipleLoops", function() {
    ok( validator.isFastaMultipleLoops(testCases['fastaMultipleLoops']) );
    $.each(testCases, function(type, i) {
        if ( type != 'fastaMultipleLoops' ) {
            equal( validator.isFastaMultipleLoops(testCases[type]), false, testCases[type]);
        }
    });
});

