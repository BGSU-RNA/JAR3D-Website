var Examples = {
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
    isFastaSingleSequenceSS: ['((((((((((..(((...)))...))))))))))',
                              '>seq1',
                              'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG'].join('\n'),

    isNoFastaSingleSequenceSS: ['((((((((((..(((...)))...))))))))))',
                                'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG'].join('\n'),

    isFastaSingleSequenceNoSS: ['>seq1','CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG'].join('\n'),

    isNoFastaSingleSequenceNoSS: 'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG',

    // multiple sequences
    isFastaMultipleSequencesSS:        ['((((((((((..(((...)))...))))))))))',
                               '>seq1', 'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG',
                               '>seq2', 'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG',
                               '>seq3', 'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG'].join('\n'),

    isNoFastaMultipleSequencesSS: ['((((((((((..(((...)))...))))))))))',
                                   'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG',
                                   'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG',
                                   'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG'].join('\n'),

    isFastaMultipleSequencesNoSS: ['>seq1','CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG',
                                   '>seq2','CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG',
                                   '>seq3','CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG'].join('\n'),

    isNoFastaMultipleSequencesNoSS: ['CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG',
                                     'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG',
                                     'CGGCCCGGCCAACCCUUUGGGCAGGGCCGGGCCG'].join('\n')

};

(function() {

    var input    = $('#input'),
        submit   = $('#submit'),
        message  = $('#message'),
        clear    = $('#clear'),
        examples = $('.examples');

    function init() {
        input.focus();
        bindEvents();
    };

    function bindEvents() {

        clear.on('click', function() {
            input.val('').focus();
        });

        input.focusin(function() {
            message.fadeOut();
        });

        examples.on('click', 'a', function() {
            message.fadeOut();
            input.val( Examples[this.id] );
        });

        submit.on('click', function() {

            var response = jar3dInputValidator.validate( input.val() );

            console.log(response);

            showMessage(response);

            if (response.valid) {
                submitData(response);
            }
        });

    };

    function showMessage(response) {
        var alerts = ['alert-success', 'alert-error'],
            msg,
            alert_class;

        if ( response.valid ) {
            msg = response.query_type;
            alert_class = alerts[0];
        } else {
            if ( response.msg ) {
                msg = response.msg;
            } else {
                msg = 'Please check your input';
            }
            alert_class = alerts[1];
        }

        message.removeClass( alerts.join(' ') )
               .addClass( alert_class )
               .html( msg )
               .fadeIn();
    };

    function submitData(response) {

        $.ajax({
          type: 'POST',
          url: 'http://rna.bgsu.edu/jar3d_dev/process_input',
          contentType: 'application/json; charset=utf-8',
          traditional: false,
          data: response,
        }).done(function(data) {
            data = jQuery.parseJSON(data);
            if ( data.redirect ) {
                window.location.href = data.redirect;
            } else if ( data.error ) {
                console.log(data);
                showMessage( {valid: false, msg: data.error} );
            } else {
                console.log(data);
            }
        });

    };

    init();

})();