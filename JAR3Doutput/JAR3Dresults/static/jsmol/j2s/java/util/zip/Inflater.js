Clazz.declarePackage ("java.util.zip");
Clazz.load (["JZ.Inflater"], "java.util.zip.Inflater", null, function () {
c$ = Clazz.declareType (java.util.zip, "Inflater", JZ.Inflater);
Clazz.defineMethod (c$, "initialize", 
function (nowrap) {
return this.init (0, nowrap);
}, "~B");
});
