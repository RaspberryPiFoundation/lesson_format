
clone: clear
	mkdir repositories
	git clone git@github.com:CodeClub/scratch-curriculum.git repositories/scratch-curriculum
	git clone git@github.com:CodeClub/webdev-curriculum.git repositories/webdev-curriculum
	git clone git@github.com:CodeClub/python-curriculum.git repositories/python-curriculum
	git clone git@github.com:CodeClub/CodeClubUK-Projects.git repositories/codeclubuk-projects
	git clone git@github.com:CodeClub/CodeClubWorld-Projects.git repositories/codeclubworld-projects

update:
	cd repositories/scratch-curriculum && git pull && git checkout master
	cd repositories/webdev-curriculum && git pull && git checkout master
	cd repositories/python-curriculum && git pull && git checkout master
	cd repositories/codeclubuk-projects && git pull && git checkout gh-pages
	cd repositories/codeclubworld-projects && git pull && git checkout gh-pages

clear:
	rm -rf repositories

pages_uk:
	python build.py ${options} uk repositories/scratch-curriculum/ repositories/python-curriculum repositories/webdev-curriculum/ repositories/codeclubuk-projects/

pages_world:
	python build.py ${options} world repositories/scratch-curriculum/ repositories/python-curriculum repositories/webdev-curriculum/ repositories/codeclubworld-projects/

world: pages_world
	cd repositories/codeclubworld-projects && git add * && git commit -am "Rebuild" && git push

uk: pages_uk
	cd repositories/codeclubuk-projects && git add * && git commit -am "Rebuild" && git push

css:
	python build.py ${options} css repositories/scratch-curriculum/ repositories/python-curriculum repositories/webdev-curriculum/ repositories/codeclubuk-projects/
