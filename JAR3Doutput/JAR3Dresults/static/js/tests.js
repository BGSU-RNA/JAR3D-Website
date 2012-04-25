var testCases = {

    // extracted loops
    isFastaSingleLoop: ['>seq1',
                        'GAAAC*GGACC'].join('\n'),

    isNoFastaSingleLoop : 'GAAAC*GGACC',

    isFastaMultipleLoops: ['>seq1', 'GAAC*GGACC',
                           '>seq2', 'GAAC*GGACC',
                           '>seq3', 'GAAC*GGACC'].join('\n'),

    isNoFastaMultipleLoops: ['GAAAC*GGACC',
                             'GAAAC*GGACC',
                             'GAAAC*GGACC',
                             'GAAAC*GGACC'].join('\n'),

    // one sequence
    isFastaSingleSequenceSS: ['(((((............)))))',
                            '>seq1',
                            'AAAAAAAAAAAAAAAAAAAAAA'].join('\n'),

    isNoFastaSingleSequenceSS: ['((((((((((...))))))))))',
                                'AAAAAAAAAAAAAAAAAAAAAAA'].join('\n'),

    isFastaSingleSequenceNoSS: ['>seq1','AAAAAAAAAAAAAAAAAAAAAA'].join('\n'),

    isNoFastaSingleSequenceNoSS: 'AAAAAAAAAAAAAAAAAAAAAA',

    // multiple sequences
    isFastaMultipleSequencesSS:        ['(((((.....)))))',
                               '>seq1', 'AAAAAUUUUUGGGGG',
                               '>seq2', 'AAAAAUUUUUGGGGG',
                               '>seq3', 'AAAAAUUUUUGGGGG'].join('\n'),

    isNoFastaMultipleSequencesSS: ['(((((.....)))))',
                                   'AAAAAUUUUUAAAAA',
                                   'AAAAAUUUUUAAAAA',
                                   'AAAAAUUUUUAAAAA'].join('\n'),

    isFastaMultipleSequencesNoSS: ['>seq1','AAAAAAAAAAA',
                                   '>seq2','GGGGGGGGGGG',
                                   '>seq3','CCCCCCCCCCC'].join('\n'),

    isNoFastaMultipleSequencesNoSS: ['AAAAAAAAAAA',
                                     'GGGGGGGGGGG',
                                     'UUUUUUUUUUU'].join('\n')

};

var validator = jar3dInputValidator;

module( "Helper functions" );
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
    equal(validator.isSecondaryStructure('([(((.].))))'), false, 'Pseudoknot');
});

test( "isSequenceLine", function() {
    ok(validator.isSequenceLine('ACGU'));
    ok(validator.isSequenceLine('acgu'));
    ok(validator.isSequenceLine('AcgU'));
    ok(validator.isSequenceLine('ACGU---UGAA'));
    ok(validator.isSequenceLine('ACGU---UGaA'));
    ok(validator.isSequenceLine('ACGTTTTACT'));
    ok(validator.isSequenceLine('ACGtTTtACT'));

    equal( validator.isSequenceLine('test'), false);
});

test( "assertSameLength", function() {
    ok ( validator.assertSameLength( ['test1', 'test2', 'test3'] ));
    ok ( validator.assertSameLength( ['test1'] ));

    equal( validator.assertSameLength( ['test11', 'test2', 'test3'] ), false );
    equal( validator.assertSameLength( ['test1', 'test21', 'test3'] ), false );
    equal( validator.assertSameLength( ['test1', 'test2', 'test31'] ), false );

    equal( validator.assertSameLength( [] ), false );
});

test( "parseAlternatingBlock", function() {
    ok ( validator.parseAlternatingBlock( ['>seq1', 'ACGU', '>seq2', 'ACGU', '>seq3', 'ACGU'], validator.isFastaLine, validator.isSequenceLine ));
    ok ( validator.parseAlternatingBlock( ['>seq1', 'ACGU*AggU', '>seq2', 'ACGU*AggU', '>seq3', 'ACGU*AggU'], validator.isFastaLine, validator.isLoopLine ));
    ok ( validator.parseAlternatingBlock( ['>seq1', 'ACGU*AgCCgU', '>seq2', 'ACGU*AggU', '>seq3', 'ACGU*AgUUUUgU'], validator.isFastaLine, validator.isLoopLine ));
    equal( validator.parseAlternatingBlock( ['>seq1', 'ACGUU', '>seq2', 'ACGU', '>seq3', 'ACGU'], validator.isFastaLine, validator.isSequenceLine ), false );
    equal( validator.parseAlternatingBlock( ['>seq1', 'ACGU', '>seq2', 'ACGUU', '>seq3', 'ACGU'], validator.isFastaLine, validator.isSequenceLine ), false );
    equal( validator.parseAlternatingBlock( ['>seq1', 'ACGU', '>seq2', 'ACGU', '>seq3', 'ACGUU'], validator.isFastaLine, validator.isSequenceLine ), false );
});

test( "complementaryClosingBases", function() {
    ok( validator.complementaryClosingBases('AcgcG*UagucU') ); // internal loop
    ok( validator.complementaryClosingBases('AcgucgucgugU') ); // hairpin
    equal( validator.complementaryClosingBases('AcgcG*GagucU'), false );
    equal( validator.complementaryClosingBases('AcgcG*UagucG'), false );
    equal( validator.complementaryClosingBases('AcgcG*GagucG'), false );
    equal( validator.complementaryClosingBases('AcgcuuuagucG'), false );
});

test( "splitLines", function() {
    deepEqual( validator.splitLines('test'), 'test' );
    deepEqual( validator.splitLines(['test1','test2','test3'].join('\n')),  ['test1','test2','test3'] );
    deepEqual( validator.splitLines(['test1','test2','test3'].join('\r')),  ['test1','test2','test3'] );
    deepEqual( validator.splitLines(['test1','test2','test3'].join('\r\n')),['test1','test2','test3'] );
    deepEqual( validator.splitLines(['','','test1','test2','','','test3','',''].join('\r')), ['test1','test2','test3'] );
});




module( "Input parsing functions" );
var jar3dTest = function( testType ) {

    test( testType, function() {
        var testedFunction = validator[testType];
        ok( testedFunction(testCases[testType]) );

        $.each(testCases, function(type, i) {
            if ( type != testType ) {
                equal( testedFunction(testCases[type]), false, type + ' ' + testCases[type] );
            }
        });
    });

};

$.each( testCases, function(type, i) {
    jar3dTest( type );
});
