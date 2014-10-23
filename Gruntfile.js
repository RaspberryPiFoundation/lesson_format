
'use strict';

module.exports = function (grunt) {
  grunt.initConfig({
    css: {
      any: 'assets/sass/**/*.scss',
      input: 'assets/sass/master.scss',
      output: 'assets/css/master.min.css'
    },

    phantom_css: {
      input: 'assets/sass/phantomjs.scss',
      output: 'assets/css/phantomjs.min.css'
    },

    wkhtmltopdf_css: {
      input: 'assets/sass/wkhtmltopdf.scss',
      output: 'assets/css/wkhtmltopdf.min.css'
    },

    pkg: grunt.file.readJSON('package.json'),

    sass: {
      options: {
        require: 'sass-globbing',
        sourcemap: 'none'
      },
      dev: {
        files: {
          '<%= css.output %>': '<%= css.input %>',
          '<%= phantom_css.output %>': '<%= phantom_css.input %>',
          '<%= wkhtmltopdf_css.output %>': '<%= wkhtmltopdf_css.input %>'
        },
        options: {
          style: 'expanded'
        }
      },
      dist: {
        files: {
          '<%= css.output %>': '<%= css.input %>',
          '<%= phantom_css.output %>': '<%= phantom_css.input %>',
          '<%= wkhtmltopdf_css.output %>': '<%= wkhtmltopdf_css.input %>'
        },
        options: {
          style: 'compressed'
        }
      }
    },

    shell: {
      css_uk: {
        options: {
          stdout: true
        },
        command: 'make css_uk'
      },
      css_world: {
        options: {
          stdout: true
        },
        command: 'make css_world'
      }
    },

    watch: {
      css: {
        files: '<%= css.any %>',
        tasks: [
          'sass:dev',
          'shell:css:uk',
          'shell:css:world'
        ]
      }
    }
  });

  require('load-grunt-tasks')(grunt);

  grunt.registerTask('default', [
    'sass:dev',
    'shell:css_uk',
    'shell:css_world',
    'watch'
  ]);

  grunt.registerTask('build', [
    'sass:dist',
    'shell:css_uk',
    'shell:css_world'
  ]);
};
