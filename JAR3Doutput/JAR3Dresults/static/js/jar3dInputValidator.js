/*
    Javascript module for parsing JAR3D input

    BGSU RNA Bioinformatics Lab
    Anton I. Petrov
*/

var jar3dInputValidator = (function($) {

    var Validator = {

        params: {
            maxLoopLength: 25,
            maxSequenceLength: 500,
            closingPairs: ['AU', 'UA', 'GC', 'CG', 'GU', 'UG']
        },

        /*
            ======================
            Basic helper functions
            ======================
        */


        /*
            Split on newline characters, trim whitespace from each line,
            remove empty lines
            Returns an array of lines
        */
        splitLines: function( input ) {
            var lines,
                pattern = /\r\n|\r|\n/;

            lines = ( input.match( pattern ) ) ? input.split( pattern ) : input;

            if ( typeof(lines) == 'string' ) {
                return [lines.trim()];
            } else {
                return $.map(lines, function(line) {
                    var trimmed = line.trim();
                    return trimmed.length > 0 ? trimmed : null;
                });
            }
        },

        // line is a fasta-formatted description line
        isFastaLine: function( line ) {
            return line[0] == '>'
        },

        /*
            <= 25 characters, internal or hairpin loops, case-insensitive,
            A, C, G, U, T, and "*"
            closing basepairs must be complementary
        */
        isLoopLine: function( line ) {
            var self = jar3dInputValidator,
                L = line.length,
                validCharsNum = line.split(/A|C|G|U|T|-|\.\*/ig).length - 1,
                chainBreaks = line.split(/\*/g).length - 1;

            return L <= self.params.maxLoopLength &&
                   L == validCharsNum &&
                   chainBreaks < 2
                   // && self.complementaryClosingBases( line )
        },

        complementaryClosingBases: function( line ) {
            var self = jar3dInputValidator,
                pairs = self.getClosingBases( line );

            var valid = $.grep(pairs, function(pair, i) {
                return self.isComplementaryPair( pair );
            });

            return valid.length == pairs.length;
        },

        getClosingBases: function( line ) {
            var closingBases = new Array,
                starPosition = line.indexOf('*');

            // the first and the last bases
            closingBases.push(line[0] + line[line.length-1]);

            // if an internal loop
            if ( starPosition > 0 ) {
                closingBases.push(line[starPosition-1] + line[starPosition+1]);
            }
            return closingBases;
        },

        isComplementaryPair: function( pair ) {
            return $.inArray(pair, jar3dInputValidator.params.closingPairs) < 0 ? false : true;
        },

        /*
            case-insensitive, < 500 characters, only A, C, G, U, T, and "-"
        */
        isSequenceLine: function( line ) {

            if ( typeof(line) != 'string' ) { return false; }

            var L = line.length,
                validCharsNum = line.split(/A|C|G|U|T|-/ig).length - 1;

            return L <= jar3dInputValidator.params.maxSequenceLength &&
                   validCharsNum == L
        },

        /*
            Same number of opening and closing brackets, only "(", ")", and "."
            No pseudoknots
        */
        isSecondaryStructure: function( line ) {

            if ( typeof(line) != 'string' ) { return false; }

            var open  = line.split( /\(|</g ).length - 1,
                close = line.split( /\)|>/g ).length - 1,
                dots  = line.split( /\.|:|-/g ).length - 1;

            return open + close + dots == line.length && open == close;
        },

        /*
            all lines must be valid and have the same length
            oddFunc  - function that parses odd lines
            evenFunc - function that parses even lines
        */
        parseAlternatingBlock: function( lines, oddFunc, evenFunc ) {
            var self = jar3dInputValidator,
                odd  = new Array(),
                even = new Array();

            $.each(lines, function(ind, line) {
                if ( ind % 2 ) {
                    even.push(line);
                    return evenFunc(line); // returning false breaks out of the loop
                } else {
                    odd.push(line);
                    return oddFunc(line);
                }
            });

            // don't insist on same length for loops
            sameLength = ( evenFunc === self.isLoopLine ? true : self.assertSameLength(even) );

            return odd.length == even.length &&
                   odd.length == lines.length / 2 &&
                   sameLength;
        },

        // loops over an array of strings, returns true
        // if all elements have the same length, false otherwise
        assertSameLength: function( data ) {

            if ( !$.isArray(data) || ( data.length==0 ) ) { return false; }

            var firstElemLength = data[0].length;

            for (var i=1, len=data.length; i<len; i++) {
                if ( !typeof(data[i]) == 'string' ||
                     data[i].length != firstElemLength ) {
                    return false;
                }
            }
            return true;
        },

        // loops over an array of strings, returns true if all strings
        // have the same number of "*" characters
        assertSameLoopType: function( data ) {
            var pattern = /\*/g,
                starsCount  = data[0].split( pattern ).length - 1;

            for (var i=1, len=data.length; i<len; i++) {
                if ( data[i].split( pattern ).length - 1 != starsCount ) {
                    return false;
                }
            }
            return true;
        },

        /*
            =====================================
            parsing functions for each input type
            =====================================
        */

        /*
            >seq1
            GAAAC*GGACC
        */
        isFastaSingleLoop: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input);
            return lines.length == 2 &&
                   self.isFastaLine( lines[0] ) &&
                   self.isLoopLine( lines[1] );
        },

        /*
            GAAAC*GGACC
        */
        isNoFastaSingleLoop: function( input ) {
            var self = jar3dInputValidator,
                loop = self.splitLines(input);

            return loop.length == 1 &&
                   self.isLoopLine( loop[0] );
        },

        /*
            >seq1
            GAAAC*GUAGC
            >seq2
            GACUC*GUAGC
        */
        isFastaMultipleLoops: function( input ) {

            var self = jar3dInputValidator,
                lines = self.splitLines(input),
                l = lines.length;

            // uneven number of lines or less than 4 lines
            if ( l % 2 != 0 || l < 4 ) {
                return false;
            }

            var loop_lines = $.grep(lines, function(line, i) {
                return i % 2 != 0;
            });

            return self.parseAlternatingBlock(lines,
                                              self.isFastaLine,
                                              self.isLoopLine) &&
                   self.assertSameLoopType(loop_lines);
        },

        /*
            GAAAC*GGACC
            GAAAC*GGACC
            GAAAC*GGACC
            GAAAC*GGACC
        */
        isNoFastaMultipleLoops: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input)
                l = lines.length;

            if ( l < 2 ) { return false; }

            var validLoops = $.grep(lines, function(line) {
                return self.isLoopLine(line);
            });

            return validLoops.length == l &&
                   self.assertSameLoopType(lines);
        },

        /*
            (((((............)))))
            >seq1
            ACGUGUCGUAGUCGAUCUGUAC
        */
        isFastaSingleSequenceSS: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input)
                l = lines.length;

            if ( l != 3 ) { return false; }

            return self.isSecondaryStructure( lines[0] ) &&
                   self.isFastaLine( lines[1] ) &&
                   self.isSequenceLine( lines[2] ) &&
                   lines[0].length == lines[2].length;
        },

        /*
            ((((((((((...))))))))))
            AAAAAAAAAAAAAAAAAAAAAAA
        */
        isNoFastaSingleSequenceSS: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input),
                l = lines.length;

            if ( l != 2 ) { return false; }

            return self.isSecondaryStructure( lines[0] ) &&
                   self.isSequenceLine( lines[1] ) &&
                   lines[0].length == lines[1].length;
        },

        /*
            >seq1
            AAAAAAAAAAAAAAAAAAAAAA
        */
        isFastaSingleSequenceNoSS: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input),
                l = lines.length;

            if ( l != 2 ) { return false; }

            return self.isFastaLine( lines[0] ) &&
                   self.isSequenceLine( lines[1] );
        },

        /*
            AAAAAAAAAAAAAAAAAAAAAA
        */
        isNoFastaSingleSequenceNoSS: function( input ) {

            if ( typeof(input) != 'string' ) {
                return false;
            }
            return jar3dInputValidator.isSequenceLine(input);
        },

        /*
            (((((.....)))))
            > seq1
            AAAAAUUUUUGGGGG
            > seq2
            AAAAAUUUUUGGGGG
        */
        isFastaMultipleSequencesSS: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input),
                l = lines.length;

            if ( l % 2 == 0 || l < 5 ) { return false; }

            return self.isSecondaryStructure( lines[0] ) &&
                   self.parseAlternatingBlock( lines.slice(1,l),
                                               self.isFastaLine,
                                               self.isSequenceLine) &&
                   lines[0].length == lines[2].length;
        },

        /*
            (((((.....)))))
            AAAAAUUUUUGGGGG
            AAAAAUUUUUGGGGG
        */
        isNoFastaMultipleSequencesSS: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input),
                l = lines.length;

            if ( l < 3 || !self.isSecondaryStructure( lines[0] ) ) { return false; }

            for (var i=1; i<l; i++) {
                if ( !self.isSequenceLine( lines[i] ) ) {
                    return false;
                }
            }

            return self.assertSameLength( lines );
        },

        /*
            >seq1
            AAAAAAAAAAAA
            >seq2
            CCCCCCCCCCCC
        */
        isFastaMultipleSequencesNoSS: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input),
                l = lines.length;

            if ( l < 4 ) { return false; }

            return self.parseAlternatingBlock( lines,
                                               self.isFastaLine,
                                               self.isSequenceLine);
        },

        /*
            AAAAAAAAAAA
            CCCCCCCCCCC
            GGGGGGGGGGG
        */
        isNoFastaMultipleSequencesNoSS: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input),
                l = lines.length;

            if ( l < 2 ) { return false; }

            for (var i=0; i<l; i++) {
                if ( !self.isSequenceLine( lines[i] ) ) {
                    return false;
                }
            }
            return true;
        },

        /*
            ========================
            Main validation function
            ========================
        */
        validate: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input),
                l = lines.length;

            var response = {
                valid: false,
                query_type: null,
                fasta: new Array(),
                data: new Array(),
                ss: null,
                parsed_input: lines.join('\n')
            };

            if ( l == 0 ) { return response; }

            if ( self.isSecondaryStructure( lines[0] ) ) {
                response.ss = lines.shift();
                // SS input
                if ( self.isFastaSingleSequenceSS( input ) ) {
                    response.query_type = 'isFastaSingleSequenceSS';
                } else if ( self.isFastaMultipleSequencesSS( input ) ) {
                    response.query_type = 'isFastaMultipleSequencesSS';
                } else if ( self.isNoFastaSingleSequenceSS( input ) ) {
                    response.query_type = 'isNoFastaSingleSequenceSS';
                } else if ( self.isNoFastaMultipleSequencesSS( input ) ) {
                    response.query_type = 'isNoFastaMultipleSequencesSS';
                }
            } else {
                // NoSS input
                if ( self.isFastaLine( lines[0] ) ) {
                    // fasta input
                    if ( self.isFastaSingleLoop( input ) ) {
                        response.query_type = 'isFastaSingleLoop';
                    } else if ( self.isFastaMultipleLoops( input ) ) {
                        response.query_type = 'isFastaMultipleLoops';
                    } else if ( self.isFastaMultipleSequencesNoSS( input ) ) {
                        response.query_type = 'isFastaMultipleSequencesNoSS';
                    } else if ( self.isFastaSingleSequenceNoSS( input ) ) {
                        response.query_type = 'isFastaSingleSequenceNoSS';
                    }
                } else {
                    // non-fasta input
                    if ( self.isNoFastaSingleLoop( input ) ) {
                        response.query_type = 'isNoFastaSingleLoop';
                    } else if ( self.isNoFastaMultipleLoops( input ) ) {
                        response.query_type = 'isNoFastaMultipleLoops';
                    } else if ( self.isNoFastaSingleSequenceNoSS( input ) ) {
                        response.query_type = 'isNoFastaSingleSequenceNoSS';
                    } else if ( self.isNoFastaMultipleSequencesNoSS( input ) ) {
                        response.query_type = 'isNoFastaMultipleSequencesNoSS';
                    }
                }
            }

            if ( response.query_type ) {
                response.valid = true;
                if ( !response.query_type.match(/NoFasta/) && lines.length > 1 ) {
                    $.each(lines, function(ind, line) {
                        if ( ind % 2 == 0 ) {
                            response.fasta.push(line);
                        } else {
                            response.data.push(line);
                        }
                    });
                } else {
                    response.data = lines;
                }
            }

            return response;

        }


    };

    return Validator;

})(jQuery);