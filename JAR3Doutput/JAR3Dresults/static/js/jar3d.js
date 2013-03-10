$(document).ready(function() {

  var sortDiv = function(klass) {
        entry = function(div) {
          return $(div).find('.' + klass);
        };

    return function(a, b) {
      var first = parseFloat(entry(a).text()),
          second = parseFloat(entry(b).text());

      if (Math.abs(first - second) < 0.00001) {
        return 0;
      }
      if (first < second) {
        return -1;
      }
      return 1;
    };
  };

  $('.sorter').change(function() {
    var $this = $(this),
        value = $this.val(),
        sorter = sortDiv(value),
        $toSort = $('#' + $this.data('div-sort'));

    $toSort.replaceWith($toSort.children().sort(sorter));

  });
});
