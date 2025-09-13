/*
    Javascript module for parsing JAR3D RFAM matching input

*/

var rfamSearchValidator = (function($) {

    var Validator = {

        params: {
            maxLoopLength: 25,
            maxSequenceLength: 1000,
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

            //convert spaces, commas, and tabs to newline characters
            input = input.replace(/[\s,;]+/g, '\n');

            //split on newline characters
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

        // line is a Motif Group ID
        isMotifGroupID: function( line ) {
            // Returns true if the line starts with IL_, HL_, or JL_, then 5 digits, a dot, and 1-2 digits
            return line.match(/^(HL_|IL_|J3_|J4_)\d{5}\.\d+/);
            // return line.match(/IL_|HL_|J3_|J4_\d{5}\.\d{1,2}/);
            },


        /*
            ========================
            Main validation function
            ========================
        */
        validate: function( input ) {
            var self = rfamSearchValidator,
                lines = self.splitLines(input),
                l = lines.length,
                title = $('#title-input').text();

            var response = {
                valid: false,
                parsed_input: lines.join('\n'),
            };

            if ( l == 0 ) { return response; }

            //Loop over all lines, check to see if eahc line is a valid motif group ID
            for ( var i = 0; i < l; i++ ) {
                if ( !self.isMotifGroupID(lines[i]) ) {
                    return response;
                }
            }


            //If all lines are valid, return the response object
            response.valid = true;
            response.data = lines;
            return response;

        }


    };

    return Validator;

})(jQuery);
