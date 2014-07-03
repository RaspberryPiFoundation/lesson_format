
clone:
	clear

	git clone git@github.com:CodeClub/pandoc_scratchblocks.git lib/pandoc_scratchblocks

	git clone git@github.com:CodeClub/scratch-curriculum.git lessons/scratch
	git clone git@github.com:CodeClub/webdev-curriculum.git  lessons/webdev
	git clone git@github.com:CodeClub/python-curriculum.git  lessons/python

	git clone git@github.com:CodeClub/CodeClubUK-Projects.git    output/codeclubuk
	git clone git@github.com:CodeClub/CodeClubWorld-Projects.git output/codeclubworld

update:
	cd lib/pandoc_scratchblocks && git pull && git checkout master

	cd lessons/scratch && git pull && git checkout master
	cd lessons/webdev  && git pull && git checkout master
	cd lessons/python  && git pull && git checkout master

	cd output/codeclubuk    && git pull && git checkout gh-pages
	cd output/codeclubworld && git pull && git checkout gh-pages

clear:
	rm -rf lib
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
