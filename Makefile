.DEFAULT_GOAL := pages_world

clone:
	make clear

	git clone --depth 1 https://github.com/CodeClub/scratch-curriculum.git lessons/scratch
	git clone --depth 1 https://github.com/CodeClub/webdev-curriculum.git  lessons/webdev
	git clone --depth 1 https://github.com/CodeClub/python-curriculum.git  lessons/python

	git clone --depth 1 https://github.com/CodeClub/pandoc_scratchblocks.git lib/pandoc_scratchblocks

update:
	cd lessons/scratch && git checkout master && git pull
	cd lessons/webdev  && git checkout master && git pull
	cd lessons/python  && git checkout master && git pull

	cd lib/pandoc_scratchblocks && git checkout master && git pull

clear:
	rm -rf lessons
	rm -rf output
	rm -rf lib

pages_world:
	python build.py ${options} world lessons/scratch lessons/python lessons/webdev output/codeclubworld

css_world:
	python build.py ${options} css lessons/scratch lessons/python lessons/webdev output/codeclubworld

serve_world:
	php -S localhost:8000 -t ./output/codeclubworld
