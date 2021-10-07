from get_files import get_files

file_list = get_files('/', is_recursive=False)

for f in file_list:
    print("{url} ({name})".format(url=f['shareURL'], name=f['title']))
