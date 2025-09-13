// motif groups are specific to the motif atlas release
var Examples_3_48 = {
    kinkturn: ['IL_29549.7','IL_51265.1','IL_68780.2','IL_90538.2','IL_35904.1','IL_64900.1','IL_74051.1','IL_68057.1','IL_16456.1','IL_37722.1','IL_90922.1','IL_76900.1','IL_34780.1','IL_65876.1','IL_85931.1'].join('\n'),
    sarcinricin: ['IL_04346.4','IL_35110.4','IL_02349.4','IL_93830.2','IL_88269.2','IL_24606.1','IL_26785.1','IL_34470.1','IL_16109.3','IL_36582.1','IL_34590.1','IL_56501.1','IL_29509.1','IL_59724.1','IL_68633.1','IL_61812.1','IL_20463.1','IL_89193.1'].join('\n'),
    doublesheared: ['IL_09705.6','IL_74719.1'].join('\n'),
    triplesheared: ['IL_56467.5'].join('\n'),
    cloop: ['IL_63596.2','IL_08376.2','IL_51590.1'].join('\n'),
    uaagan: ['IL_53523.4','IL_34907.1','IL_81389.2','IL_49767.3'].join('\n'),
    receptor11: ['IL_97601.6','IL_34915.2','IL_72938.1','IL_20549.1'].join('\n'),
    tandemnoncww: ['IL_85877.9','IL_50676.4','IL_84158.1'].join('\n'),
    loope: ['IL_56455.2'].join('\n'),
    gnra: ['HL_43074.14','HL_93727.3','HL_02361.5','HL_68304.6'].join('\n'),
    uncg: ['HL_79299.9'].join('\n'),
    tloop: ['HL_33239.14','HL_08002.5','HL_68493.4','HL_78061.2','HL_23537.2','HL_93436.1'].join('\n'),
    anticodon: ['HL_59710.7','HL_91131.1'].join('\n'),
    dloop: ['HL_32617.1','HL_61092.1','HL_10751.2','HL_88225.1','HL_81327.2','HL_49873.1','HL_12571.1','HL_55511.1','HL_27359.1'].join('\n'),
};

var Examples_3_98 = {
    kinkturn: ['IL_70923.9','IL_01488.3','IL_69229.3','IL_51265.3','IL_99692.2','IL_46174.3','IL_64900.1','IL_94910.1','IL_24134.1','IL_74051.1','IL_33886.1','IL_77045.1','IL_32016.1','IL_95727.1','IL_06029.1'].join('\n'),
    sarcinricin: ['IL_02349.4','IL_04346.10','IL_16458.4','IL_20463.1','IL_24254.1','IL_26307.2','IL_29198.2','IL_34470.3','IL_38862.4','IL_41756.4','IL_43547.1','IL_59724.1','IL_61286.1','IL_65594.1','IL_70670.1','IL_84694.2','IL_88269.4'].join('\n'),
    doublesheared: ['IL_09705.15','IL_10484.1'].join('\n'),
    triplesheared: ['IL_50730.2','IL_17948.2','IL_61440.1'].join('\n'),
    cloop: ['IL_63596.11','IL_03109.3','IL_26222.2'].join('\n'),
    uaagan: ['IL_38507.2','IL_89021.2','IL_49767.8'].join('\n'),
    receptor11: ['IL_53448.1','IL_67767.4'].join('\n'),
    tandemnoncww: ['IL_85033.2','IL_77658.1','IL_13404.2'].join('\n'),
    loope: ['IL_56455.6'].join('\n'),
    gnra: ['HL_37824.7','HL_81538.2'].join('\n'),
    uncg: ['HL_34617.5'].join('\n'),
    tloop: ['HL_28252.8','HL_01609.3','HL_02887.3'].join('\n'),
    anticodon: ['HL_06059.6','HL_83632.1'].join('\n'),
    dloop: ['HL_20811.4','HL_93616.2','HL_45175.1','HL_49941.1','HL_04642.1','HL_09260.2','HL_68767.1','HL_02581.1','HL_23115.1'].join('\n'),
};

{/*
<li><a href='#' id="kinkturn">Kink turn internal loop</a></li>
<li><a href='#' id="sarcinricin">Sarcin-ricin internal loop</a></li>
<li><a href='#' id="doublesheared">Double sheared pair internal loop</a></li>
<li><a href='#' id="triplesheared">Triple sheared pair internal loop</a></li>
<li><a href='#' id="cloop">C-loop internal loop</a></li>
<li><a href='#' id="uaagan">UAA/GAN internal loop</a></li>
<li><a href='#' id="receptor11">Receptor of 11nt loop-receptor internal loop</a></li>
<li><a href='#' id="tandemnoncww">Tandem non-canonical cWW pair internal loop</a></li>
<li><a href='#' id="loope">Bacterial 5S loop E internal loop</a></li>
<li><a href='#' id="gnra">GNRA hairpin loop</a></li>
<li><a href='#' id="uncg">UNCG hairpin loop</a></li>
<li><a href='#' id="tloop">T-loop hairpin loop</a></li>
<li><a href='#' id="anticodon">tRNA anticodon hairpin loop</a></li>
<li><a href='#' id="dloop">tRNA D-loop hairpin loop</a></li> */}


(function() {

    var input    = $('#input'),
        submit   = $('#submit'),
        message  = $('#message'),
        version  = $('#version'),
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

        version.on('change', function() {
            input.val('').focus();
        });

        examples.on('click', 'a', function() {
            // what happens when you click an example link
            message.fadeOut();
            if (version.val()==='3.48') {
                input.val( Examples_3_48[this.id] );
            } else if (version.val()==='3.98') {
                input.val( Examples_3_98[this.id] );
            }
        });

        submit.on('click', function() {
            console.log("Submit button clicked")
            var response = rfamSearchValidator.validate( input.val() );
            console.log(response);
            showMessage(response);

            //if response is valid, redirect to results page
            if (response.valid) {
                setTimeout(function() {
                    window.location.href = 'https://rna.bgsu.edu/jar3d/rfam/' + $('#version').val() + '/' + response.data.join(',');
                }, 2000);
            }

        });
    };

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
    };

    init();

})();
