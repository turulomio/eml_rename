# eml_rename project

Script renames all eml files in a directory using mail metadata

## Idea

I needed this tool to classify and order my mail files at work.

I took this idea from an article of Armand Niculescu (August 20, 2014) at https://www.media-division.com/using-python-to-batch-rename-email-files/ , so thanks an I hope you like this code.

## Features

- Automatically renames all *.eml files in a directory, using email metadata. 
- Renamed files will have this format is 'YYYYMMDD HHMM [From] Subject'
- If 'YYYYMMDD HHMM [From]' format is detected the script won't rename the file. With this feature user can change subject manually and the script won't overwrite it.
- If you use --force parameter the script will overwrite all files even they have the 'YYYYMMDD HHMM [From]' format.
- Length of the new name will have 140 character as maximum, although you can change it with the --length parameter
- --save parameter renames files. If you don't use this parameter it will only pretend the result
- It uses concurrency to make process faster

## Changelog

### 0.2.0 (2022-11-12)
-  Now mail datetime uses local system time zone

### 0.1.0 (2022-11-06)
- First version
- Added main features