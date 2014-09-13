var page = require('webpage').create(),
    system = require('system'),
    optimist = require('optimist-phantomjs'),
    address, output, size;

var usage = '\nRasterize a webpage to image or PDF.\n\n';
usage += 'Usage: $0 [--footer FOOTER_HTML] [--style STYLESHEET_FILENAME] [--script SCRIPT_FILENAME] input_URL output_filename [paperwidth*paperheight|paperformat] [zoom]\n\n';
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
        window.setTimeout(function () {
            page.render(output);
            phantom.exit();
        }, 200);
    }
});
