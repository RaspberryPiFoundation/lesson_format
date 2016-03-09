.DEFAULT_GOAL := pages_world

clone:
	make clear

	git clone --depth 1 https://github.com/CodeClub/scratch-curriculum.git lessons/scratch
	git clone --depth 1 https://github.com/CodeClub/webdev-curriculum.git  lessons/webdev
	git clone --depth 1 https://github.com/CodeClub/python-curriculum.git  lessons/python

update:
	cd lessons/scratch && git checkout master && git pull
	cd lessons/webdev  && git checkout master && git pull
	cd lessons/python  && git checkout master && git pull

clear:
	rm -rf lessons
	rm -rf output

pages_world:
	python build.py ${options} world lessons/scratch lessons/python lessons/webdev output/codeclubworld

pages_cc:
	python build.py ${options} cc lessons/scratch lessons/python lessons/webdev output/codeclub

css_world:
	python build.py ${options} css lessons/scratch lessons/python lessons/webdev output/codeclubworld

css_cc:
	python build.py ${options} css lessons/scratch lessons/python lessons/webdev output/codeclub

serve_world:
	php -S localhost:8000 -t ./output/codeclubworld

serve_cc:
	php -S localhost:8000 -t ./output/codeclub