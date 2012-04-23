
var jar3dInputValidator = {

    hasSecondaryStructure: function( input ) {

        if ( input.match(/(|)|\./) ) {
            return true;
        } else {
            return false;
        }

    },

    hasFasta: function( input ) {

        if ( input.match(/^>/) ) {
            return true;
        } else {
            return false;
        }

    }


};
