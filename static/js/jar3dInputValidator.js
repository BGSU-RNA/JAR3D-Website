/*
    Javascript module for parsing JAR3D input

    BGSU RNA Bioinformatics Lab
    Anton I. Petrov
*/

var jar3dInputValidator = (function($) {

    var Validator = {

        params: {
            maxLoopLength: 35,
            maxSequenceLength: 1000,
            maxSequences: 1000,
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
            <= 35 characters, internal or hairpin loops, case-insensitive,
            A, C, G, U, T, and "*"
            closing basepairs must be complementary
        */
        isLoopLine: function( line ) {
            var self = jar3dInputValidator,
                L = line.length,
                validCharsNum = line.split(/A|C|G|U|T|-|\.|\*/ig).length - 1,
                chainBreaks = line.split(/\*/g).length - 1;

            return L <= self.params.maxLoopLength &&
                   L == validCharsNum &&
                   chainBreaks < 4
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
                validCharsNum = line.split(/A|C|G|U|T|-|\./ig).length - 1;

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
            RF00001
            RF02543
        */

        isRfamFamily: function( str ) {
            // if lines[0] starts with 'RF' and is followed by 5 digits,
            // then it's a Rfam ID
            const pattern = /^RF\d{5}$/;
            return pattern.test(str.toUpperCase());
        },


        countSequences: function( input ) {
            // count the number of input sequences

            var count = 0;
            lines = input.split('\n');
            for (i=0; i < lines.length; i++) {
                if (!lines[i].startsWith('>')) {
                    count = count + 1;
                }
            }
            return count;
        },

        clean: function( input ) {
            // replace characters found in SSCONS line with simpler ones

            lines = input.split('\n');
            for (i=0; i < lines.length; i++) {
                if (!lines[i].startsWith('>')) {
                    newtext = lines[i];
                    newtext = newtext.replace(/\./g,"-");
                    newtext = newtext.replace(/,/g,"-");
                    newtext = newtext.replace(/_/g,"-");
                    newtext = newtext.replace(/~/g,"-");
                    newtext = newtext.replace(/:/g,"-");
                    newtext = newtext.replace(/</g,"(");
                    newtext = newtext.replace(/>/g,")");
                    newtext = newtext.replace(/[ \t\d]/g, "");
                    lines[i] = newtext;
                }
            }
            modified = lines.join('\n');
            return modified
        },


        /*
            ========================
            Main validation function
            ========================
        */
        validate: function( input ) {
            var self = jar3dInputValidator,
                lines = self.splitLines(input),
                l = lines.length
                // title = $('#title-input').text();

            lines = lines.map(line => line.trim());
            input = lines.join('\n');

            var response = {
                valid: false,
                query_type: null,
                fasta: new Array(),
                data: new Array(),
                ss: null,
                parsed_input: lines.join('\n'),
            };

            if ( l == 0 ) { response.length = 0; return response; }

            num_sequences = self.countSequences( input );
            if ( num_sequences > self.params.maxSequences) {
                response.msg = 'Found ' + num_sequences + ' sequences, but the limit is ' + self.params.maxSequences;
                return response;
            }

            if ( self.isSecondaryStructure( lines[0] ) ) {
                response.ss = lines.shift();
                response.ss = response.ss.replace(/-/g,".");
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
                        response.msg = 'Please provide secondary structure information';
                    } else if ( self.isFastaSingleSequenceNoSS( input ) ) {
                        response.msg = 'Please provide secondary structure information';
                    }
                } else {
                    // non-fasta input
                    if ( self.isNoFastaSingleLoop( input ) ) {
                        response.query_type = 'isNoFastaSingleLoop';
                    } else if ( self.isNoFastaMultipleLoops( input ) ) {
                        response.query_type = 'isNoFastaMultipleLoops';
                    } else if ( self.isNoFastaSingleSequenceNoSS( input ) ) {
                        response.msg = 'Please provide secondary structure information';
                    } else if ( self.isNoFastaMultipleSequencesNoSS( input ) ) {
                        response.msg = 'Please provide secondary structure information';
                    } else if ( self.isRfamFamily( input ) ) {
                        input_upper = input.toUpperCase();
                        const LSU = ['RF00001','RF00002','RF02543','RF02540','RF02541','RF02546'];
                        const SSU = ['RF01960','RF01959','RF00177','RF02545','RF02542'];
                        const tRNA = ['RF00005'];
                        if (LSU.includes(input_upper)) {
                            response.msg = 'Rfam Ribosomal LSU families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + input;
                        } else if (SSU.includes(input_upper)) {
                            response.msg = 'Rfam Ribosomal SSU families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + input;
                        } else if (tRNA.includes(input_upper)) {
                            response.msg = 'Rfam tRNA families are not supported, see 3D structures by visiting the <a href="https://rna.bgsu.edu/rna3dhub/nrlist/release/rna/current" target= "_blank">Representative Sets</a> page and filtering on ' + input;
                        } else {
                            response.query_type = 'isRfamFamily';
                        }
                    }
                }
            }

            if ( response.query_type ) {
                response.valid = true;
                if (response.query_type == 'isRfamFamily') {
                    response.data = lines;
                } else if ( !response.query_type.match(/NoFasta/) && lines.length > 1 ) {
                    $.each(lines, function(ind, line) {
                        if ( ind % 2 == 0 ) {
                            // header lines
                            response.fasta.push(line);
                        } else {
                            // sequence lines
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
