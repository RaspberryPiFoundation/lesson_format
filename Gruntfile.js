
'use strict';

module.exports = function (grunt) {
  grunt.initConfig({
    css: {
      any: 'assets/sass/**/*.scss',
      input: 'assets/sass/master.scss',
      output: 'assets/css/master.min.css'
    },

    pkg: grunt.file.readJSON('package.json'),

    sass: {
      options: {
        require: 'sass-globbing'
      },
      dev: {
        files: {
          '<%= css.output %>': '<%= css.input %>'
        },
        options: {
          style: 'expanded'
        }
      },
      dist: {
        files: {
          '<%= css.output %>': '<%= css.input %>'
        },
        options: {
          style: 'compressed'
        }
      }
    },

    watch: {
      css: {
        files: '<%= css.any %>',
        tasks: [
          'sass:dev'
        ]
      }
    }
  });

  require('load-grunt-tasks')(grunt);

  grunt.registerTask('default', [
    'sass:dev',
    'watch'
  ]);

  grunt.registerTask('build', [
    'sass:dist'
  ]);
};
