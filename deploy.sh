dev=$1
prod=$2

cd $dev/app
# temporarily stash all uncommitted changes
git stash
git checkout develop
git push origin develop
# merge and push develop
git checkout master
git merge develop
git push origin master
# switch back to stay on develop
git checkout develop

cd $prod/app
# make sure we are on master, update
git checkout master
git pull origin master

# copy over js, css etc
python $dev/app/JAR3Doutput/manage.py collectstatic --noinput
python $prod/app/JAR3Doutput/manage.py collectstatic --noinput

# restart django
wsgid restart --app-path=$dev
wsgid restart --app-path=$prod

# restore uncommitted changes
cd $dev/app
git stash pop
