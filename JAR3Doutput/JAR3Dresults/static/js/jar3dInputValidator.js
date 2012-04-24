
var jar3dInputValidator = {

    splitLines: function( input ) {
        var lines;
        if ( input.match(/\r\n|\r|\n/) ) {
            lines = input.split(/\r\n|\r|\n/)
        } else {
            lines = input;
        }
        for (var i = 0; i < lines.length-1; i++) {
            lines[i].trim();
        }
        return lines;
    },

    // line is a fasta-formatted description line
    isFastaLine: function( line ) {
        return line[0] == '>' ? true : false;
    },

    // line is a valid loop
    isLoopLine: function( line ) {

        var self = this,
            L = line.length,
            MAX_LOOP_LENGTH = 25,
            validChars = line.split(/A|C|G|U|T|\*/ig).length - 1,
            chainBreaks = line.split(/\*/g).length - 1;

        if ( L < MAX_LOOP_LENGTH &&
             L == validChars &&
             chainBreaks < 2 &&
             this.complementaryClosingBases( line ) ) {
            return true;
        } else {
            return false;
        }
    },

    complementaryClosingBases: function( line ) {
        var self = this,
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

        if ( starPosition > 0 ) {
            closingBases.push(line[starPosition-1] + line[starPosition+1]);
        }
        return closingBases;
    },

    isComplementaryPair: function( pair ) {
        return $.inArray(pair, ['AU', 'UA', 'GC', 'CG', 'GU', 'UG']) < 0 ? false : true;
    },

    // line is a valid nucleotide sequence
    isSequenceLine: function( line ) {
        var L = line.length,
            validChars = line.split(/A|C|G|U|T|-/ig).length - 1,
            MAX_SEQUENCE_LENGTH = 500;

        if ( L <= MAX_SEQUENCE_LENGTH &&
             validChars.length == L) {
            return true;
         } else {
            return false;
         }

    },

    // line is a valid secondary structure
    isSecondaryStructure: function( line ) {
        var open  = line.split(/\(/g).length - 1,
            close = line.split(/\)/g).length - 1,
            dots  = line.split(/\./g).length - 1;
        return open + close + dots == line.length && open == close;
    },

    // individual functions for each input case
    isFastaSingleLoop: function( input ) {
        var self = this,
            lines = self.splitLines(input);
        return lines.length == 2 &&
               self.isFastaLine( lines[0] ) &&
               self.isLoopLine( lines[1] );
    },

    isNoFastaSingleLoop: function( input ) {
        var self = this,
            loop = self.splitLines(input);

        return typeof(loop) == 'string' &&
               self.isLoopLine( loop );
    },

    /*
        Multiple loops with fasta descriptions
        >seq1
        GAAAC*GUAGC
        >seq2
        GACUC*GUAGC
    */
    isFastaMultipleLoops: function( input ) {
        var self = this,
            lines = self.splitLines(input),
            l = lines.length,
            fasta = new Array(),
            loops = new Array(),
            badloops = new Array();

        // uneven number of lines or less than 4 lines
        if ( l % 2 != 0 || l < 4 ) {
            return false;
        }

        $.each(lines, function(i, line) {
            // 0, 2, 4 => fasta
            // 1, 3, 5 => loop
            if ( i % 2 ) {
                loops.push(line);
                return self.isLoopLine(line);
            } else {
                fasta.push(line);
                return self.isFastaLine(line);
            }
        });

        // all loops should be the same length
        badLoops = $.grep(loops, function(loop, i) {
            return loop.length != loops[0].length;
        });

        return fasta.length == loops.length &&
               fasta.length == lines.length / 2 &&
               badLoops.length == 0;

    }

};
