var page = require('webpage').create(),
    system = require('system'),
    optimist = require('optimist-phantomjs'),
    address, output, size;

/**
 * This function is adapted from the phantomjs website. See:
 * https://github.com/ariya/phantomjs/blob/master/examples/waitfor.js
 */
function waitFor(testFx, onReady, timeOutMillis) {
    var maxtimeOutMillis = timeOutMillis ? timeOutMillis : 3000, //< Default Max Timout is 3s
        start = new Date().getTime(),
        condition = false,
        interval = setInterval(function() {
            if ( (new Date().getTime() - start < maxtimeOutMillis) && !condition ) {
                // If not time-out yet and condition not yet fulfilled
                condition = (typeof(testFx) === "string" ? eval(testFx) : testFx()); //< defensive code
            } else {
                if(condition) {
                    console.log("Injected javascript completed in " + (new Date().getTime() - start) + "ms.");
                } else {
                    // If condition still not fulfilled (timeout but condition is 'false')
                    console.log("Injected javascript timed out");
                }
                typeof(onReady) === "string" ? eval(onReady) : onReady();
                clearInterval(interval); //< Stop this interval
            }
        }, 250); //< repeat check every 250ms
};

var usage = '\nRasterize a webpage to image or PDF.\n\n';
usage += 'Usage: $0 [--footer FOOTER_HTML] [--waitFor JAVASCRIPT_CONDITIONAL] [--style STYLESHEET_FILENAME] [--script SCRIPT_FILENAME] input_URL output_filename [paperwidth*paperheight|paperformat] [zoom]\n\n';
usage += '  paper (pdf output) examples: "5in*7.5in", "10cm*20cm", "A4", "Letter"\n';

var argv = optimist
  .usage(usage)
  .demand(2)
  .argv
;

address = argv._[0];
output = argv._[1];
page.viewportSize = { width: 600, height: 600 };

var footer = (argv.footer) ? {
    height: "2.5cm",
    contents: phantom.callback(function(pageNum) {
        return argv.footer.replace('{{ pageNum }}', pageNum);
    })
} : {
    height: 0,
    contents: ''
};

if (argv._.length > 2 && output.substr(-4) === ".pdf") {
    size = argv._[2].split('*');
    page.paperSize = size.length === 2 ? { width: size[0], height: size[1], margin: '0px', footer: footer }
    : {
        format: argv._[2],
        orientation: 'portrait',
        margin: {top: '1.2cm'},
        footer: footer
    };
}
if (argv._.length > 3) {
    page.zoomFactor = argv._[3];
}
page.open(address, function (status) {
    if (status !== 'success') {
        console.log('Unable to load the address!');
        phantom.exit();
    } else {
        if (argv.style) {
            page.setContent(page.content.replace('</head>', '<link rel="stylesheet" href="' + argv.style + '"></head>'), page.url);
        }
        if (argv.script) {
            page.injectJs(argv.script);
        }
        waitFor(function () {
            if (argv.waitFor === undefined) return true;
            return page.evaluate(function(isJsDone) {
                return isJsDone;
            }, argv.waitFor);
        }, function() {
            page.render(output);
            phantom.exit();
        }, 8000);
    }
});
