
clone:
	make clear

	git clone https://github.com/CodeClub/scratch-curriculum.git lessons/scratch
	git clone https://github.com/CodeClub/webdev-curriculum.git  lessons/webdev
	git clone https://github.com/CodeClub/python-curriculum.git  lessons/python

	git clone https://github.com/CodeClub/CodeClubUK-Projects.git    output/codeclubuk
	git clone https://github.com/CodeClub/CodeClubWorld-Projects.git output/codeclubworld

update:
	cd lessons/scratch && git checkout master && git pull
	cd lessons/webdev  && git checkout master && git pull
	cd lessons/python  && git checkout master && git pull

	cd output/codeclubuk    && git checkout gh-pages && git pull
	cd output/codeclubworld && git checkout gh-pages && git pull

clear:
	rm -rf lessons
	rm -rf output

pages_uk:
	python build.py ${options} uk lessons/scratch lessons/python lessons/webdev output/codeclubuk

pages_world:
	python build.py ${options} world lessons/scratch lessons/python lessons/webdev output/codeclubworld

commit_uk:
	cd output/codeclubuk && git add * && git commit -am "Rebuild" && git push

commit_world:
	cd output/codeclubworld && git add * && git commit -am "Rebuild" && git push

css_uk:
	python build.py ${options} css lessons/scratch lessons/python lessons/webdev output/codeclubuk

css_world:
	python build.py ${options} css lessons/scratch lessons/python lessons/webdev output/codeclubworld
