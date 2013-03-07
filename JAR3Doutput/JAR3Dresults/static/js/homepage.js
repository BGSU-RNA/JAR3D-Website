var Examples = {
    // extracted loops
    isFastaSingleLoop: ['>seq1',
                        'CGCAG*UCAGG'].join('\n'),

    isNoFastaSingleLoop : 'CGCAG*UCAGG',

    isFastaMultipleLoops: ['>sarcin 1', 'CUCAGUAU*AGAACCG',
                           '>sarcin 2', 'CUCAGUAC*GGAACCG',
                           '>sarcin 3', 'CUCAGUAC*GGAACUG'].join('\n'),

    isNoFastaMultipleLoops: ['CUCAGUAU*AGAACCG',
                             'CUCAGUAC*GGAACCG',
                             'CUCAGUAC*GGAACUG'].join('\n'),

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
    }

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

    }

    function showMessage(response) {
        var alerts = ['alert-success', 'alert-error'],
            msg,
            alert_class;

        if ( response.valid ) {
            msg = 'Your query has been submitted. You will be redirected to the results page shortly.';
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
    }

    function submitData(response) {

        var url = document.URL.match(/^http:\/\/127\.0\.0\.1:8000/) ||
              document.URL.match(/^http:\/\/rna.bgsu.edu\/\w+/),
            postURL = url[0] + '/process_input';

        $.ajax({
          type: 'POST',
          url: postURL,
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

    }

    init();

}());
