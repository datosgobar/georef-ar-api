sed -i.bu 's/%C3%A1/a/' $1
sed -i.bu 's/%C3%A9/e/' $1
sed -i.bu 's/%C3%AD/i/' $1
sed -i.bu 's/%C3%B3/o/' $1
sed -i.bu 's/%C3%BA/u/' $1
sed -i.bu 's/%C2%BF//' $1
sed -i.bu 's/---/-/' $1
rm $1.bu
