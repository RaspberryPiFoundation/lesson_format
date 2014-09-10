var page = require('webpage').create(),
    system = require('system'),
    address, output, size,
    footerContents;

// styled-up footer contents
footerContents = '\
<div style="text-align: center; font-family: Helvetica, Arial, sans-serif; font-size: 9px; line-height: 11px;"> \
    <span style="display: inline-block; border: 2px #00A5DF solid; border-radius: 50%; width: 28px; height: 28px; line-height: 28px; font-size: 22px; color: #00A5DF; background-color: #fff;"> \
        {{ pageNum }} \
    </span> \
    <hr style="height: 4px; border: 0; background-color: #AFE3EF; position: relative; top: -18px; z-index: -999; margin: 0 60px;"> \
    \
    These projects are for use inside the UK only. All Code Clubs must be registered. You can check registered clubs on the map at <strong>www.codeclub.org.uk</strong>.<br> \
    \
    This coursework is developed in the open on GitHub, at <strong>www.github.com/CodeClub/</strong>. Come and join us! \
</div>';

if (system.args.length < 3 || system.args.length > 5) {
    console.log('Usage: rasterize.js URL filename [paperwidth*paperheight|paperformat] [zoom]');
    console.log('  paper (pdf output) examples: "5in*7.5in", "10cm*20cm", "A4", "Letter"');
    phantom.exit(1);
} else {
    address = system.args[1];
    output = system.args[2];
    page.viewportSize = { width: 600, height: 600 };
    if (system.args.length > 3 && system.args[2].substr(-4) === ".pdf") {
        size = system.args[3].split('*');
        page.paperSize = size.length === 2 ? { width: size[0], height: size[1], margin: '0px' }
        : {
            format: system.args[3],
            orientation: 'portrait',
            margin: {top: '1.2cm'},
            footer: {
                height: "2.5cm",
                contents: phantom.callback(function(pageNum) {
                    return footerContents.replace('{{ pageNum }}', pageNum);
                })
            }
        };
    }
    if (system.args.length > 4) {
        page.zoomFactor = system.args[4];
    }
    page.open(address, function (status) {
        if (status !== 'success') {
            console.log('Unable to load the address!');
            phantom.exit();
        } else {
            page.injectJs('lib/js/lesson.js');
            window.setTimeout(function () {
                page.render(output);
                phantom.exit();
            }, 200);
        }
    });
}
