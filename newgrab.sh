rm test -r
cp template test -r
cd test/vbi
../../dumpvbi
cd ~/vhs-teletext
./vbi.py test
./t42cat.py test/t42 | ./pagesplit.py test/pages
./subpagesquash.py test/pages test/html