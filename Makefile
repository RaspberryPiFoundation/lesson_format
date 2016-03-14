.DEFAULT_GOAL := pages_cc

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

pages_cc:
	python build.py ${options} cc lessons/scratch lessons/python lessons/webdev output/codeclub

css_cc:
	python build.py ${options} css lessons/scratch lessons/python lessons/webdev output/codeclub

serve_cc:
	php -S localhost:8000 -t ./output/codeclub
