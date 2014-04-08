
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
      makeCSS: {
        options: {
          stdout: true
        },
        command: 'make css'
      }
    },

    watch: {
      css: {
        files: '<%= css.any %>',
        tasks: [
          'sass:dev',
          'shell:makeCSS'
        ]
      }
    }
  });

  require('load-grunt-tasks')(grunt);

  grunt.registerTask('default', [
    'sass:dev',
    'shell:makeCSS',
    'watch'
  ]);

  grunt.registerTask('build', [
    'sass:dist',
    'shell:makeCSS'
  ]);
};
