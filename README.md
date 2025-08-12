# SHIFT Meteorology task
A Data Engineering project for SHIFT, includes a full ETL pipeline.
Includes requesting a file, converting and saving it.
Original data was in imperial units, and soil temperature measurments had some missing data, which was fixed.
The data is downloaded from open-meteo.com, the loop version also include a date selection.
"loop" scripts solve task modularly and DRY-like, while "robust" scripts explain everything better.
