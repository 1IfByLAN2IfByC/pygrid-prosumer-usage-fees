for filename in ~/git/pygrid/ERCOT/*.png; do
  ann="${filename##*/}";
  ext="${filename##*.}";
  tmp="${ann%.*}"
  label="${tmp: -4}"
  convert "$filename" \
  -fill red\
  -pointsize 8\
  -density 300\
  -annotate +350+30 "Load at ${label}" \
  "annotated $ann"
done;
