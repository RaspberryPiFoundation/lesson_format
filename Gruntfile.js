
'use strict';

module.exports = function (grunt) {
  grunt.initConfig({
    css: {
      any: 'assets/sass/**/*.scss',
      input: 'assets/sass/master.scss',
      output: 'assets/css/master.min.css'
    },

    pdf_css: {
      input: 'assets/sass/pdf.scss',
      output: 'assets/css/pdf.min.css'
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
          '<%= pdf_css.output %>': '<%= pdf_css.input %>'
        },
        options: {
          style: 'expanded'
        }
      },
      dist: {
        files: {
          '<%= css.output %>': '<%= css.input %>',
          '<%= pdf_css.output %>': '<%= pdf_css.input %>'
        },
        options: {
          style: 'compressed'
        }
      }
    },

    shell: {
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
          'shell:css_world'
        ]
      }
    }
  });

  require('load-grunt-tasks')(grunt);

  grunt.registerTask('default', [
    'sass:dev',
    'shell:css_world',
    'watch'
  ]);

  grunt.registerTask('build', [
    'sass:dist',
    'shell:css_world'
  ]);
};
