$(document).ready(function() {

  var plot = Rna2D({
    width: 250,
    height: 300,
    selection: "#query-2d",
    view: 'airport'
  });

  plot.nucleotides(LOCATIONS);
  plot.interactions(PAIRS);

  // No need for a brush in the query.
  plot.brush.enabled(false);

  plot();
});
