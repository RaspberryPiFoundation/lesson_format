
'use strict';

module.exports = function (grunt) {
  grunt.initConfig({
    css: {
      any: 'assets/sass/**/*.scss',
      input: 'assets/sass/master.scss',
      output: 'assets/css/master.min.css'
    },

    pkg: grunt.file.readJSON('package.json'),

    tag: {
      banner: '/*!\n' +
        ' * <%= pkg.name %>\n' +
        ' * @author <%= pkg.author.name %> <<%= pkg.author.email %>>\n' +
        ' * @version <%= pkg.version %>\n' +
        ' */\n'
    },

    sass: {
      options: {
        banner: '<%= tag.banner %>',
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

    shell: {
      makeCSS_UK: {
        options: {
          stdout: true
        },
        command: 'make css_uk'
      },
      makeCSS_WORLD: {
        options: {
          stdout: true
        },
        command: 'make css_world'
      },
      makePages_UK: {
        options: {
          stdout: true
        },
        command: 'make pages_uk'
      },
      makePages_WORLD: {
        options: {
          stdout: true
        },
        command: 'make pages_world'
      }
    },

    watch: {
      css: {
        files: '<%= css.any %>',
        tasks: [
          'sass:dev',
          'shell:makeCSS_UK',
          'shell:makeCSS_WORLD'
        ]
      },
      py: {
        files: 'build.py',
        tasks: [
          'shell:makePages_UK',
          'shell:makePages_WORLD'
        ]
      }
    }
  });

  require('load-grunt-tasks')(grunt);

  grunt.registerTask('default', [
    'sass:dev',
    'shell:makeCSS_UK',
    'shell:makeCSS_WORLD',
    'watch'
  ]);

  grunt.registerTask('build', [
    'sass:dist',
    'shell:makeCSS_UK',
    'shell:makeCSS_WORLD'
  ]);
};
